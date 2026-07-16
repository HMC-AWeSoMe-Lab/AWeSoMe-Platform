"""
toxicityHighlighter.py

LLM-based contextual toxicity highlighting.

Unlike the keyword-based highlighting logic in interventionHelpers.py
(TRIGGER_WORDS / simple_highlight_logic / target_phrase_highlight_logic),
this does NOT match against a fixed word list. Instead, it sends the LLM:

    1. The full conversation (every branch, not just the ancestor path)
    2. A marker showing exactly which existing comment the user is
       replying to (latest_id)
    3. The user's live draft text

...and asks the LLM to judge whether the draft is toxic, or would raise
the tension of the conversation, and if so, which specific words/phrases
should be edited or removed, with a short reason for each.

The LLM is expected to return raw JSON in this exact shape:

    [
        {"phrase": "some exact substring from the draft", "reason": "short justification"},
        ...
    ]

or an empty list `[]` if nothing should be flagged.

WHAT'S INTENTIONALLY LEFT FOR YOU TO FILL IN
---------------------------------------------
TOXICITY_HIGHLIGHT_PROMPT below is a placeholder. Everything else (the
LLM call, JSON parsing, error handling, caching, and converting the
result into the [start, end] character ranges the highlighting system
needs) is fully implemented.

INTEGRATION
-----------
This file also defines ContextualToxicityHighlightingIntervention, a thin
subclass of HighlightingIntervention. It exists ONLY so that `convo` and
`latest_id` (already available to every intervention's get_payload call,
see backend/interventions/base.py) can be forwarded into the toxicity
logic above. HighlightingIntervention itself is not modified — its
highlight_func is normally called with just `text`, so a subclass is the
only way to also pass conversation context without editing
backend/interventions/highlighting.py.

To wire this in, add ONE entry to INTERVENTIONS in app.py:

    from backend.services.toxicityHighlighter import ContextualToxicityHighlightingIntervention

    INTERVENTIONS = [
        ...,
        ContextualToxicityHighlightingIntervention(trigger_event="onText"),
    ]
"""

import json
import re
import time

from backend.interventions.highlighting import HighlightingIntervention
from backend.interventions.popup import PopupIntervention
from backend.interventions.interventionHelpers import TRIGGER_WORDS
from backend.services.callLlamaSCD import call_llama


# ---------------------------------------------------------------------------
# PROMPT — left for you to fill in.
# ---------------------------------------------------------------------------
# This is the system prompt sent to the LLM. It should instruct the model to:
#   - judge the toxicity of the draft text using the conversation as context
#   - decide whether the draft itself is toxic, or risks raising the
#     tension of the conversation
#   - if so, identify the specific words/phrases that should be edited or
#     removed, each with a short reason
#   - return ONLY raw JSON (no markdown fences, no commentary) in the shape:
#     [{"phrase": "...", "reason": "..."}, ...]  (or [] if nothing to flag)
#
# The user-turn content (conversation transcript + reply target + draft
# text) is assembled separately below in _build_user_prompt() and does not
# need to be duplicated here.
TOXICITY_HIGHLIGHT_PROMPT = """You are analyzing a comment a user is currently drafting, before they post it, as a reply within the conversation shown to you.


If the draft comment is toxic, uncivil, or likely to increase tension in this conversation, identify the specific word or short phrases in the DRAFT COMMENT ONLY — never from the earlier conversation — that make it toxic or likely to escalate tension. For each, give a short, single-sentence reason.


Rules:
- Every "word" or "phrase" must be copied EXACTLY, character-for-character, from the draft comment — same spelling, capitalization, and punctuation. Do not paraphrase or correct it.
- Only flag words and phrases from the draft comment, never from the earlier conversation shown for context.
- DO NOT REFLAG the TRIGGER_WORDS
- If the comment is civil and unlikely to raise tension, do not flag anything.
Look out for people who are trying to cover up their words or phrases using symbols. For example “ F*ck you!” should still trigger the highlight. Additionally, look out for misspelled words that are toxic. 
Look for BOTH words and phrases. 


Example output for a draft like "You are stupid and ugly":
[{"word": "ugly", "reason": "A direct personal insult attacking the recipient's physical appearance."}]
This is because “stupid” is already a highlighted trigger word and should not be highlighted again. 


Example output for a draft like "You are ugly and stupid":
[{"phrase": "You are ugly", "reason": "A direct personal insult attacking the recipient's physical appearance."}]
This is because “stupid” is already a highlighted trigger word and should not be highlighted again. 


Example output for a draft like "yeah sure, whatever you say, genius":
[{"phrase": "whatever you say, genius", "reason": "Sarcastic dismissal that mocks the other speaker rather than engaging with their point."}]


Respond with ONLY raw JSON, no markdown fences, no extra commentary, in exactly this shape:
if a phrase is flagged, return [{"phrase": "...", "reason": "..."}]
if a word is flagged, return [{"word": "...", "reason": "..."}]


If nothing should be flagged, respond with exactly: []
"""


# ---------------------------------------------------------------------------
# Context building
# ---------------------------------------------------------------------------

def _build_conversation_transcript(convo, latest_id):
    """
    Build a transcript of the ENTIRE conversation (all branches), marking
    which utterance the user's draft would be replying to.

    :param convo: Conversation object (or None if unavailable)
    :type convo: convokit.Conversation or None
    :param latest_id: id of the utterance the user is currently replying to
    :type latest_id: str or None
    :return: human-readable transcript with the reply target marked
    :rtype: str
    """
    if convo is None:
        return "(no conversation context available)"

    speaker_labels = {}
    lines = []

    utts = list(convo.iter_utterances())
    # Chronological order gives the LLM a sensible reading order even
    # though every branch is included (not just the ancestor path).
    utts.sort(key=lambda u: (u.timestamp if u.timestamp is not None else float("inf")))

    latest_id_str = str(latest_id) if latest_id is not None else None

    for utt in utts:
        if utt.speaker_id not in speaker_labels:
            speaker_labels[utt.speaker_id] = f"Speaker{len(speaker_labels) + 1}"
        label = speaker_labels[utt.speaker_id]

        marker = ">>> [USER IS REPLYING TO THIS COMMENT] >>> " if (
            latest_id_str is not None and str(utt.id) == latest_id_str
        ) else ""

        lines.append(f"{marker}{label}: {utt.text}")

    return "\n".join(lines)


def _build_user_prompt(convo, latest_id, draft_text):
    """
    Assemble the full user-turn content sent to the LLM: conversation
    transcript (with reply target marked) followed by the live draft.

    Also tells the model which words are already caught by a separate,
    simpler keyword-based highlighter (TRIGGER_WORDS, defined in
    interventionHelpers.py), so it doesn't need to re-flag those — it
    should focus on other toxicity/tension signals instead.

    :param convo: Conversation object (or None)
    :param latest_id: id of the utterance being replied to
    :param draft_text: the user's current draft comment
    :return: combined prompt text
    :rtype: str
    """
    transcript = _build_conversation_transcript(convo, latest_id)
    already_flagged_words = ", ".join(sorted(TRIGGER_WORDS))
    return (
        "CONVERSATION (all branches, chronological order):\n"
        f"{transcript}\n\n"
        "DRAFT COMMENT (currently being typed by the user, not yet posted):\n"
        f"{draft_text or ''}\n\n"
        "NOTE: A separate, simpler system already highlights these specific "
        f"words whenever they appear: {already_flagged_words}. Do not flag "
        "those words again here — focus only on other toxicity or "
        "tension-raising language."
    )


# ---------------------------------------------------------------------------
# LLM call + JSON parsing
# ---------------------------------------------------------------------------

def _strip_code_fences(raw):
    """
    Some LLMs wrap JSON in ```json ... ``` fences despite instructions not
    to. Strip those if present before parsing.

    :param raw: raw LLM output
    :type raw: str
    :return: raw text with any surrounding code fences removed
    :rtype: str
    """
    if raw is None:
        return ""
    text = raw.strip()
    fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return text


def _parse_llm_json(raw):
    """
    Parse the LLM's response into a list of {"phrase": ..., "reason": ...}
    dicts. Raises ValueError on anything malformed so the caller can
    surface a clear intervention error (per project decision: fail loudly
    rather than silently).

    The prompt allows the LLM to key a flagged item as either "phrase"
    (multi-word spans) or "word" (single flagged words) — both are
    normalized to "phrase" here so every downstream consumer
    (_phrases_to_ranges, etc.) only ever has to handle one key.

    :param raw: raw LLM output
    :type raw: str
    :return: list of phrase/reason dicts (always keyed "phrase"/"reason")
    :rtype: list[dict]
    :raises ValueError: if the response isn't valid, well-shaped JSON
    """
    cleaned = _strip_code_fences(raw)
    if not cleaned:
        raise ValueError("Toxicity highlighter: LLM returned an empty response")

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Toxicity highlighter: LLM did not return valid JSON: {e}")

    if not isinstance(parsed, list):
        raise ValueError(
            f"Toxicity highlighter: expected a JSON list, got {type(parsed).__name__}"
        )

    result = []
    for i, item in enumerate(parsed):
        if not isinstance(item, dict) or "reason" not in item:
            raise ValueError(
                f"Toxicity highlighter: item {i} is missing required 'reason' key: {item!r}"
            )

        # Accept either "phrase" or "word" as the flagged-span key.
        if "phrase" in item:
            span = item["phrase"]
        elif "word" in item:
            span = item["word"]
        else:
            raise ValueError(
                f"Toxicity highlighter: item {i} is missing required 'phrase'/'word' key: {item!r}"
            )

        phrase = str(span)
        reason = str(item["reason"])
        if phrase.strip():
            result.append({"phrase": phrase, "reason": reason})

    return result


def _call_llm_for_toxicity(convo, latest_id, draft_text, bucket=0):
    """
    Call the LLM and return the parsed list of flagged phrase/reason dicts.

    :param convo: Conversation object (or None)
    :param latest_id: id of the utterance being replied to
    :param draft_text: user's current draft comment
    :param bucket: parallelization bucket, passed through to call_llama
    :return: list of {"phrase": ..., "reason": ...} dicts
    :rtype: list[dict]
    :raises ValueError: if the LLM call fails or returns unparseable output
    """
    user_prompt = _build_user_prompt(convo, latest_id, draft_text)

    try:
        raw_response = call_llama(TOXICITY_HIGHLIGHT_PROMPT, user_prompt, bucket)
    except Exception as e:
        raise ValueError(f"Toxicity highlighter: LLM call failed: {e}")

    return _parse_llm_json(raw_response)


# ---------------------------------------------------------------------------
# Phrase -> character range matching
# ---------------------------------------------------------------------------

def _is_boundary_ok(text, pos, phrase_len):
    """
    True if the occurrence of a phrase at [pos, pos+phrase_len) sits on a
    word boundary — i.e. it isn't just a substring stuck in the middle of
    a longer, unrelated word (e.g. flagging "ass" should not also light
    up the "ass" inside "class" or "assignment").

    The check only applies at an edge where BOTH the phrase's own edge
    character and the text's neighboring character are alphanumeric. If
    the phrase's edge character is already punctuation/symbol (as with
    the obfuscated-profanity case the prompt asks the LLM to catch, e.g.
    "F*ck" or "a$$"), that edge is exempt so obfuscated matches still
    highlight correctly — only clean alphanumeric edges need an actual
    word boundary.

    :param text: the full draft text the phrase was found in
    :param pos: start index of the match
    :param phrase_len: length of the matched phrase
    :return: whether this occurrence should be highlighted
    :rtype: bool
    """
    end = pos + phrase_len  # exclusive

    first_char = text[pos]
    if first_char.isalnum():
        prev_char = text[pos - 1] if pos > 0 else ""
        if prev_char.isalnum():
            return False

    last_char = text[end - 1]
    if last_char.isalnum():
        next_char = text[end] if end < len(text) else ""
        if next_char.isalnum():
            return False

    return True


def _trigger_word_ranges(text):
    """
    Character ranges covered by the fixed TRIGGER_WORDS list in `text`,
    using the same whole-word boundary matching as
    interventionHelpers.default_highlight_logic/simple_highlight_logic —
    i.e. exactly the spans the RED trigger-word highlighter will draw.

    Used to carve trigger-word spans OUT of the toxicity (orange) ranges:
    the prompt asks the LLM not to re-flag TRIGGER_WORDS, but LLMs don't
    reliably follow negative instructions, so this is a real code-level
    guard rather than relying on prompt compliance.

    :param text: the draft text
    :type text: str
    :return: list of (start, end) inclusive ranges
    :rtype: list[tuple[int, int]]
    """
    if not text:
        return []
    text_lower = text.lower()
    ranges = []
    for word in TRIGGER_WORDS:
        start = 0
        while True:
            pos = text_lower.find(word, start)
            if pos == -1:
                break
            if (pos == 0 or not text[pos - 1].isalnum()) and \
               (pos + len(word) == len(text) or not text[pos + len(word)].isalnum()):
                ranges.append((pos, pos + len(word) - 1))
            start = pos + 1
    return ranges


def _trim_range(text, start, end):
    """
    Shrink a [start, end] (inclusive) range inward past any leading/
    trailing whitespace, returning None if nothing but whitespace is left.

    Used after carving a trigger-word span out of a toxicity range: a cut
    like "You are stupid and ugly." minus "stupid" naively leaves
    "You are " (trailing space) and " and ugly." (leading space) as the
    two remaining segments. Left untrimmed, that dangling space still
    gets wrapped in a highlight span and painted with the underline
    background — visibly bleeding the orange toxicity highlight into
    blank space immediately next to the red trigger-word highlight,
    making the two look overlapped/misaligned even though their
    character ranges no longer actually overlap.

    :param text: the draft text the range was computed against
    :param start: inclusive start index
    :param end: inclusive end index
    :return: (start, end) trimmed to the first/last non-whitespace
        character, or None if the segment is empty/whitespace-only
    :rtype: tuple[int, int] or None
    """
    while start <= end and text[start].isspace():
        start += 1
    while end >= start and text[end].isspace():
        end -= 1
    if start > end:
        return None
    return (start, end)


def _subtract_trigger_words(ranges, text):
    """
    Remove any TRIGGER_WORDS-covered characters from a list of
    [start, end, reason] toxicity ranges, splitting a range into the
    remaining sub-segment(s) around the trigger word rather than dropping
    the whole thing. This is what lets "You are stupid and ugly" keep
    "ugly" highlighted orange while "stupid" — a TRIGGER_WORD, already
    highlighted red by the separate keyword highlighter — is excluded
    from the orange layer entirely, instead of the two colors stacking
    on the same characters.

    Each remaining sub-segment is trimmed of leading/trailing whitespace
    (see _trim_range) so the cut never leaves a dangling space rendered
    as part of the orange highlight — that dangling space is exactly
    what previously made orange highlights look shifted and made them
    visually bleed into/overlap the adjacent red trigger-word highlight.

    :param ranges: list of [start, end, reason] (inclusive end)
    :param text: the draft text these ranges were computed against
    :return: new list of [start, end, reason], with trigger-word spans
        carved out, edges trimmed of whitespace, and empty results dropped
    :rtype: list[list]
    """
    if not ranges:
        return ranges

    trigger_spans = _trigger_word_ranges(text)
    if not trigger_spans:
        return [[s, e, r] for s, e, r in ranges]

    result = []
    for start, end, reason in ranges:
        segments = [(start, end)]
        for tw_start, tw_end in trigger_spans:
            next_segments = []
            for seg_start, seg_end in segments:
                # No overlap — keep segment as-is.
                if tw_end < seg_start or tw_start > seg_end:
                    next_segments.append((seg_start, seg_end))
                    continue
                # Overlap — keep whatever's left on either side.
                if seg_start < tw_start:
                    next_segments.append((seg_start, tw_start - 1))
                if seg_end > tw_end:
                    next_segments.append((tw_end + 1, seg_end))
            segments = next_segments
        for seg_start, seg_end in segments:
            trimmed = _trim_range(text, seg_start, seg_end)
            if trimmed is not None:
                result.append([trimmed[0], trimmed[1], reason])

    return result


def _phrases_to_ranges(draft_text, flagged):
    """
    Convert LLM-flagged phrases into [start, end, reason] character ranges
    (inclusive end, matching the [start, end] convention used elsewhere in
    this project — see interventionHelpers.py's highlight functions — with
    the LLM's per-phrase reason appended as a third element so the frontend
    tooltip can show the specific justification for that highlight).

    Every exact (case-insensitive) occurrence of each flagged phrase is
    highlighted, as long as it lands on a word boundary (see
    _is_boundary_ok) rather than mid-word inside an unrelated word.
    Phrases not found verbatim in the draft are skipped, since there's no
    reliable position to highlight for a paraphrase.

    Any characters covered by the fixed TRIGGER_WORDS list (see
    _subtract_trigger_words) are carved out of the result before it's
    returned. The prompt tells the LLM not to re-flag TRIGGER_WORDS, but
    that's not reliable on its own — this is the actual code-level
    guarantee that a trigger word never ends up rendered in the orange
    toxicity color, since the separate red keyword-highlighter already
    owns it. A phrase that's partly a trigger word (e.g. "stupid and
    ugly") keeps the non-trigger-word part highlighted.

    :param draft_text: the user's draft comment
    :type draft_text: str
    :param flagged: list of {"phrase": ..., "reason": ...} dicts
    :type flagged: list[dict]
    :return: list of [start, end, reason] ranges
    :rtype: list[list]
    """
    if not draft_text or not flagged:
        return []

    text_lower = draft_text.lower()
    ranges = []

    for item in flagged:
        phrase = item["phrase"]
        if not phrase:
            continue
        phrase_lower = phrase.lower()
        reason = item.get("reason", "")

        start = 0
        while True:
            pos = text_lower.find(phrase_lower, start)
            if pos == -1:
                break
            if _is_boundary_ok(draft_text, pos, len(phrase)):
                ranges.append([pos, pos + len(phrase) - 1, reason])  # inclusive end
            start = pos + 1

    return _subtract_trigger_words(ranges, draft_text)


# ---------------------------------------------------------------------------
# Per-session state: LLM call gating + sticky per-phrase reasons
# ---------------------------------------------------------------------------
# Two separate problems, both keyed by convo_id (the id of the active
# conversation / session), so one user's in-progress typing never reads or
# writes another user's state:
#
# 1. GATE WHEN THE LLM IS ACTUALLY CALLED
#    Calling the LLM on every keystroke would be slow and expensive, and
#    typing a single mid-word letter rarely changes the toxicity judgment
#    of the whole draft anyway. Instead:
#      - The LLM is only called once at least MIN_LLM_CALL_INTERVAL_SECONDS
#        has passed since the last LLM call for this convo_id, AND
#      - the draft's last character is a space, punctuation mark, or
#        emoji (i.e. the user just finished typing a word/clause) —
#      - OR, regardless of the last character, if the user has gone quiet
#        for MIN_LLM_CALL_INTERVAL_SECONDS (no request arrived sooner) and
#        the draft has changed since the last LLM call, we still fire once
#        so the trailing partial word/sentence gets checked. This request
#        is delivered for free by the existing onText trigger (debounced
#        300ms client-side) — the *next* request to arrive after a lull is
#        naturally "the user paused," so no separate frontend timer is
#        needed to detect it.
#    Requests that don't qualify reuse the last-known ranges, recomputed
#    against the current text so positions stay correct even though
#    nothing was re-judged.
#
# 2. KEEP A FLAGGED PHRASE'S REASON STABLE ONCE ASSIGNED
#    Once a phrase has been flagged with a given reason, that reason is
#    remembered for the rest of the session (per convo_id) and reused
#    verbatim as long as the same phrase still appears verbatim in the
#    draft — even if the LLM is re-called (because the gate above allowed
#    it) and would have worded the reason differently this time. The
#    reason is only replaced if the user actually edits the characters
#    *of that phrase itself*, which removes it from the draft and lets a
#    fresh LLM call assign a new reason if it's re-flagged.
_last_call_time_by_convo = {}   # convo_id -> time.monotonic() of last LLM call
_last_text_by_convo = {}        # convo_id -> draft text as of the last LLM call
_reason_ledger_by_convo = {}    # convo_id -> {lowercased phrase: reason}

MIN_LLM_CALL_INTERVAL_SECONDS = 1.0

# Standard ASCII punctuation/symbols — mirrors the set the frontend treats
# as "qualifying" characters for its own display-side bookkeeping.
_PUNCTUATION_CHARS = set(".,!?;:'\"()[]{}-_/\\@#$%^&*+=~`<>|")

# Common emoji Unicode ranges (emoticons, symbols & pictographs, dingbats,
# transport, supplemental symbols, variation selectors, regional
# indicators for flag emoji) — covers the vast majority of emoji typed
# via standard keyboards/pickers.
_EMOJI_RANGES = (
    (0x1F300, 0x1FAFF),
    (0x2600, 0x27BF),
    (0x2190, 0x21FF),
    (0x2B00, 0x2BFF),
    (0xFE0F, 0xFE0F),
    (0x1F1E6, 0x1F1FF),
)


def _is_qualifying_char(ch):
    """
    True if `ch` is a space, punctuation mark, or emoji — the set of
    "just finished a word/clause" characters that make the current
    request eligible to trigger a fresh LLM call (subject to the
    MIN_LLM_CALL_INTERVAL_SECONDS cooldown).

    :param ch: a single character (or None/empty)
    :type ch: str or None
    :return: whether this character qualifies
    :rtype: bool
    """
    if not ch:
        return False
    if ch == " ":
        return True
    if ch in _PUNCTUATION_CHARS:
        return True
    codepoint = ord(ch)
    return any(lo <= codepoint <= hi for lo, hi in _EMOJI_RANGES)


def _should_call_llm(convo_id, text):
    """
    Decide whether this request should trigger a fresh LLM call.

    :param convo_id: id used to scope per-session gating state
    :param text: the draft text as of this request
    :return: True if the LLM should be called now
    :rtype: bool
    """
    now = time.monotonic()
    last_call_time = _last_call_time_by_convo.get(convo_id)

    # First request ever seen for this convo — always call once so the
    # draft gets an initial judgment.
    if last_call_time is None:
        return True

    elapsed = now - last_call_time
    if elapsed < MIN_LLM_CALL_INTERVAL_SECONDS:
        return False

    # Cooldown has elapsed. Either the user just typed a qualifying
    # character (fire immediately), or enough time has passed that this
    # request represents the user having paused/stopped — fire so the
    # trailing partial text still gets checked, but only if the text
    # actually changed since the last LLM call (no point re-calling on an
    # identical draft).
    if _is_qualifying_char(text[-1] if text else None):
        return True

    return _last_text_by_convo.get(convo_id) != text


def _get_reason_ledger(convo_id):
    return _reason_ledger_by_convo.setdefault(convo_id, {})


def _find_overlapping_ledger_key(ledger, new_key, current_text):
    """
    Find an existing ledger key whose character range (as it currently
    appears in current_text) overlaps the new phrase's range, so its
    reason can be reused instead of asking the LLM to justify the same
    stretch of text twice.

    Only used as a fallback when new_key isn't already an exact ledger
    key — this is what lets a later, differently-worded phrase for the
    same toxic content (e.g. "smile." flagged earlier, later re-flagged
    as part of a wider clause) still inherit the original reason.

    :param ledger: {lowercased phrase: reason} dict
    :param new_key: lowercased phrase being looked up
    :param current_text: draft text as it currently stands
    :return: the overlapping existing key, or None if no overlap found
    :rtype: str or None
    """
    text_lower = current_text.lower()
    new_pos = text_lower.find(new_key)
    if new_pos == -1:
        return None
    new_start, new_end = new_pos, new_pos + len(new_key) - 1

    for existing_key in ledger:
        pos = text_lower.find(existing_key)
        if pos == -1:
            continue
        existing_start, existing_end = pos, pos + len(existing_key) - 1
        if not (new_end < existing_start or new_start > existing_end):
            return existing_key
    return None


def _apply_sticky_reasons(convo_id, flagged, current_text):
    """
    Merge freshly-returned {"phrase", "reason"} items with this session's
    remembered phrases/reasons, so a previously-flagged phrase's highlight
    never moves, changes reason, or disappears on its own — it can only
    change if the user actually edits *that phrase's own characters*.

    Two things happen here:
      1. For phrases the LLM re-flags this round, keep the original
         remembered reason instead of the LLM's newest (possibly
         differently-worded) reason.
      2. For phrases that were flagged in a previous call and are STILL
         present verbatim in the current draft, but that this round's LLM
         call simply didn't re-flag (LLM output isn't perfectly
         repeatable call to call — see module docstring), add them back
         in. This is what stops a highlight from flickering/vanishing
         just because the LLM's fresh judgment didn't happen to mention
         it again; it can only truly go away via _forget_edited_phrases,
         which already only fires when the phrase's own characters were
         actually edited.

    :param convo_id: id used to scope the per-session ledger
    :param flagged: list of {"phrase": ..., "reason": ...} dicts fresh
        from this LLM call
    :param current_text: the draft text as it currently stands, used to
        confirm previously-ledgered phrases are still verbatim present
    :return: list of {"phrase": ..., "reason": ...} dicts, reasons
        stabilized and previously-flagged-but-unedited phrases retained
    :rtype: list[dict]
    """
    ledger = _get_reason_ledger(convo_id)
    result = []
    seen_keys = set()

    for item in flagged:
        phrase = item["phrase"]
        key = phrase.lower()
        if key in ledger:
            reason = ledger[key]
        else:
            existing_key = _find_overlapping_ledger_key(ledger, key, current_text)
            if existing_key is not None:
                # This phrase overlaps content already flagged under a
                # different (shorter/longer/differently-worded) key —
                # e.g. the LLM previously flagged just "smile." and now
                # returns the whole clause it's part of. Same underlying
                # toxic content, so reuse its existing reason rather than
                # treating this as something new.
                reason = ledger[existing_key]
            else:
                reason = item["reason"]
            ledger[key] = reason
        result.append({"phrase": phrase, "reason": reason})
        seen_keys.add(key)

    # Re-add any ledgered phrase the LLM didn't mention this round, as
    # long as it's still verbatim in the text (phrases that were edited
    # away were already dropped from the ledger by _forget_edited_phrases
    # before this function runs).
    for phrase, reason in _ledger_phrases_with_original_casing(ledger, current_text):
        if phrase.lower() not in seen_keys:
            result.append({"phrase": phrase, "reason": reason})
            seen_keys.add(phrase.lower())

    return _collapse_overlapping_phrases(result, current_text)


def _collapse_overlapping_phrases(items, current_text):
    """
    Collapse phrases that overlap the same stretch of text into a single
    entry, so the same toxic content never ends up highlighted as two+
    separate (and possibly staggered) ranges.

    This does NOT change what reason is used for any given phrase — a
    phrase's reason is still whatever was already assigned to it earlier
    in this same call (via the ledger lookups above), by design, so the
    same toxic content keeps producing the exact same tooltip text every
    time it's seen. This step only decides, among phrases that cover
    overlapping characters, which single phrase "wins" and gets rendered
    — it never asks the LLM again and never invents a new reason.

    The longer (more specific/complete) phrase is kept when two overlap,
    since it's normally the more recent, more fully-formed judgment (e.g.
    an early call flagging just "smile." and a later call flagging the
    whole clause it's part of are almost always the same underlying
    toxic content, just captured at different levels of completeness).

    :param items: list of {"phrase": ..., "reason": ...} dicts, each
        expected to appear verbatim in current_text
    :param current_text: the draft text these phrases were found in
    :return: list of {"phrase": ..., "reason": ...} with overlaps removed
    :rtype: list[dict]
    """
    if len(items) <= 1:
        return items

    text_lower = current_text.lower()
    positioned = []
    for item in items:
        phrase = item["phrase"]
        pos = text_lower.find(phrase.lower())
        if pos == -1:
            continue  # shouldn't happen; be defensive rather than crash
        positioned.append((pos, pos + len(phrase) - 1, item))

    # Longest phrase first, so the more complete span claims its
    # character range before any shorter, overlapping span is considered.
    positioned.sort(key=lambda p: (p[1] - p[0]), reverse=True)

    kept = []
    for start, end, item in positioned:
        overlaps_kept = any(not (end < ks or start > ke) for ks, ke, _ in kept)
        if not overlaps_kept:
            kept.append((start, end, item))

    kept.sort(key=lambda p: p[0])
    return [item for _, _, item in kept]


def _forget_edited_phrases(convo_id, current_text):
    """
    Drop any ledger entries whose phrase no longer appears verbatim
    (case-insensitively) in the current draft. This is what makes a
    reason "unstick": once the user edits a previously-flagged phrase
    enough that it's no longer a substring of the draft, its remembered
    reason is forgotten, so if the user later retypes that same phrase
    it's treated as newly flagged and a fresh reason is assigned.
    Phrases that still appear untouched elsewhere in the draft keep their
    remembered reason.

    :param convo_id: id used to scope the per-session ledger
    :param current_text: the draft text as it currently stands
    """
    ledger = _get_reason_ledger(convo_id)
    if not ledger:
        return
    current_lower = (current_text or "").lower()
    for key in list(ledger.keys()):
        if key not in current_lower:
            del ledger[key]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def toxic_highlight_logic(text, convo=None, convo_id=None, latest_id=None, bucket=0):
    """
    Main entry point: given the draft text and conversation context,
    return [start, end, reason] character ranges to highlight, where
    `reason` is stable per flagged phrase for the lifetime of this
    convo_id's session (see module docstring above for the two
    stability guarantees this provides).

    The LLM is only called when _should_call_llm() allows it: at most
    once per MIN_LLM_CALL_INTERVAL_SECONDS, and only when either (a) the
    draft's last character is a space/punctuation/emoji, or (b) the user
    has gone quiet long enough that this is effectively the "stopped
    typing" trailing check. All other requests reuse the previously
    known ranges, recomputed against the current text so positions stay
    correct even though nothing was re-judged this round.

    :param text: the user's draft comment text
    :param convo: Conversation object (or None)
    :param convo_id: id used to scope per-session state
    :param latest_id: id of the utterance being replied to
    :param bucket: parallelization bucket, passed through to call_llama
    :return: list of [start, end, reason] ranges
    :rtype: list[list]
    :raises ValueError: if the LLM call fails or returns unparseable output
    """
    if not text:
        _last_call_time_by_convo.pop(convo_id, None)
        _last_text_by_convo.pop(convo_id, None)
        _reason_ledger_by_convo.pop(convo_id, None)
        return []

    # A phrase that's no longer present at all (edited away) shouldn't
    # keep polluting the ledger forever, regardless of whether we call
    # the LLM this round or not.
    _forget_edited_phrases(convo_id, text)

    if not _should_call_llm(convo_id, text):
        # Gate says: reuse what we already know. Just re-derive ranges
        # for the phrases we already know about against the (possibly
        # shifted) current text, using their stable, ledgered reasons.
        ledger = _get_reason_ledger(convo_id)
        flagged = [{"phrase": phrase, "reason": reason}
                   for phrase, reason in _ledger_phrases_with_original_casing(ledger, text)]
        return _phrases_to_ranges(text, flagged)

    flagged = _call_llm_for_toxicity(convo, latest_id, text, bucket)
    flagged = _apply_sticky_reasons(convo_id, flagged, text)
    ranges = _phrases_to_ranges(text, flagged)

    _last_call_time_by_convo[convo_id] = time.monotonic()
    _last_text_by_convo[convo_id] = text
    return ranges


def get_current_toxic_phrases(convo_id, text):
    """
    Return the phrases currently flagged as toxic for this session, without
    triggering a fresh LLM call. Used at submit time: by then, typing has
    already driven one or more onText calls that populated the per-convo
    reason ledger, so we can just read it back instead of paying LLM
    latency again right as the user clicks submit.

    :param convo_id: id used to scope the per-session ledger
    :param text: the draft text as it currently stands (the exact text
        about to be submitted)
    :return: list of {"phrase": ..., "reason": ...} dicts still present
        verbatim in `text`
    :rtype: list[dict]
    """
    _forget_edited_phrases(convo_id, text)
    ledger = _get_reason_ledger(convo_id)
    return [
        {"phrase": phrase, "reason": reason}
        for phrase, reason in _ledger_phrases_with_original_casing(ledger, text)
    ]


def _ledger_phrases_with_original_casing(ledger, current_text):
    """
    The ledger keys are lowercased (for case-insensitive matching), but
    _phrases_to_ranges needs the phrase in the casing it actually
    appears in the current text so highlighted ranges line up correctly.
    Finds each ledgered phrase's real-casing substring in current_text.

    :param ledger: {lowercased phrase: reason} dict
    :param current_text: the draft text as it currently stands
    :return: generator of (phrase_in_original_casing, reason) tuples
    """
    text_lower = current_text.lower()
    for key, reason in ledger.items():
        pos = text_lower.find(key)
        if pos == -1:
            continue  # shouldn't happen since _forget_edited_phrases just ran, but be safe
        yield current_text[pos:pos + len(key)], reason


# ---------------------------------------------------------------------------
# Intervention subclass — forwards convo/latest_id into toxic_highlight_logic
# ---------------------------------------------------------------------------

class ContextualToxicityHighlightingIntervention(HighlightingIntervention):
    """
    Subclass of HighlightingIntervention that forwards conversation
    context (convo, latest_id) into the toxicity-highlighting logic above.

    This exists because HighlightingIntervention.get_payload normally
    calls self.highlight_func(text) with just the text — no conversation
    context. Since backend/interventions/highlighting.py cannot be edited
    for this feature, this subclass overrides get_payload to gather the
    extra context itself and call toxic_highlight_logic() directly,
    instead of going through self.highlight_func.
    """

    def __init__(self, trigger_event="onText", variant="toxicity", bucket=0):
        super().__init__(trigger_event=trigger_event, highlight_func=None, variant=variant)
        self.name = "contextual_toxicity_highlighting"
        self.bucket = bucket

    def get_payload(self, convo=None, text=None, trigger_event=None, latest_id=None, **kwargs):
        if self.trigger_event != trigger_event:
            return None
        if self.trigger_event == "onClick":
            return None

        convo_id = getattr(convo, "id", None)

        highlight_ranges = toxic_highlight_logic(
            text or "",
            convo=convo,
            convo_id=convo_id,
            latest_id=latest_id,
            bucket=self.bucket,
        )

        if not highlight_ranges:
            return None

        # Each range is [start, end, reason]. If every range carries its own
        # LLM-provided reason, use those (joined) for the logged top-level
        # "reason" too — more useful for research analysis than one generic
        # message. Falls back to the generic message if reasons are missing.
        per_range_reasons = [r[2] for r in highlight_ranges if len(r) > 2 and r[2]]
        if per_range_reasons:
            unique_reasons = list(dict.fromkeys(per_range_reasons))  # preserve order, dedupe
            reason = "; ".join(unique_reasons)
        else:
            reason = (f"{len(highlight_ranges)} portion(s) of the draft were flagged as potentially "
                      f"raising the tension of the conversation")

        # Note: no "source_text" key needed here — BaseIntervention.update()
        # attaches it automatically to any "highlighting"-typed payload,
        # including this override (see backend/interventions/base.py).
        return {
            "type": "highlighting",
            "triggerEvent": self.trigger_event,
            "variant": self.variant,
            "reason": reason,
            "enabled": True,
            "highlight_indices": highlight_ranges,
        }


# ---------------------------------------------------------------------------
# Submit-time popup — blocks on AI-flagged toxicity, not just TRIGGER_WORDS
# ---------------------------------------------------------------------------
#
# BUG THIS FIXES: the existing submit-comment PopupIntervention
# (backend/interventions/popup.py, wired with text_func=submit_check_logic
# in app.py) only ever looks at the fixed TRIGGER_WORDS list. A draft that
# the LLM toxicity highlighter actively flagged (visibly underlined in the
# "toxicity" variant color while typing) sails straight through submit with
# no popup at all, because submit_check_logic has no way to know about
# those flags. This class closes that gap: at submit time it reads back
# whatever this session's toxicity highlighter has flagged (via the same
# reason ledger toxic_highlight_logic already maintains — no extra LLM
# call needed) and blocks submission if any of it is still present in the
# draft, exactly like the TRIGGER_WORDS popup does for its own list.
#
# Wire this in ALONGSIDE the existing submit-comment PopupIntervention in
# app.py (both target button_id="submit-comment", blocking=True); the
# frontend already just looks for *any* blocking popup in the response
# (see commentActions.js's `interventions.find(i => i.type === "popup" &&
# i.blocking)`), so having two independent checks fire into the same
# response list works with zero frontend changes.
class ToxicitySubmitPopupIntervention(PopupIntervention):
    """
    Blocking submit-time popup driven by the AI toxicity highlighter's
    current flags for this session, instead of the static TRIGGER_WORDS
    list.
    """

    def __init__(self, button_id="submit-comment", blocking=True):
        super().__init__(
            trigger_event="onClick",
            text_func=lambda _text: None,  # replaced per-call below
            button_id=button_id,
            blocking=blocking,
        )
        self.name = "toxicity_submit_popup"

    def get_payload(self, convo=None, text=None, button_id=None, **kwargs):
        if self.button_id != button_id:
            return None

        convo_id = getattr(convo, "id", None)
        flagged = get_current_toxic_phrases(convo_id, text or "")
        if not flagged:
            return None

        reasons = list(dict.fromkeys(item["reason"] for item in flagged if item.get("reason")))
        popup_text = (
            "Your comment includes language flagged as likely to raise the "
            "tension of the conversation: " + "; ".join(reasons)
            if reasons else
            "Your comment includes language flagged as likely to raise the "
            "tension of the conversation."
        )

        # Reuse PopupIntervention's own HTML-building logic rather than
        # duplicating it — swap in a text_func that returns our computed
        # message for the duration of this call.
        original_text_func = self.text_func
        self.text_func = lambda _text: popup_text
        try:
            return super().get_payload(convo=convo, text=text, button_id=button_id, **kwargs)
        finally:
            self.text_func = original_text_func