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

from backend.interventions.highlighting import HighlightingIntervention
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

def _phrases_to_ranges(draft_text, flagged):
    """
    Convert LLM-flagged phrases into [start, end, reason] character ranges
    (inclusive end, matching the [start, end] convention used elsewhere in
    this project — see interventionHelpers.py's highlight functions — with
    the LLM's per-phrase reason appended as a third element so the frontend
    tooltip can show the specific justification for that highlight).

    Every exact (case-insensitive) occurrence of each flagged phrase is
    highlighted. Phrases not found verbatim in the draft are skipped,
    since there's no reliable position to highlight for a paraphrase.

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
            ranges.append([pos, pos + len(phrase) - 1, reason])  # inclusive end
            start = pos + 1

    return ranges


# ---------------------------------------------------------------------------
# Per-session state: change detection + sticky per-phrase reasons
# ---------------------------------------------------------------------------
# Two separate problems, both keyed by convo_id (the id of the active
# conversation / session), so one user's in-progress typing never reads or
# writes another user's state:
#
# 1. AVOID RE-CALLING THE LLM ON NON-ALPHABETIC EDITS
#    Typing a space, punctuation, or an emoji shouldn't cause the LLM to
#    re-judge the whole draft (it's non-deterministic, so the same
#    substance can come back with a different reason or slightly
#    different span each time). We only re-call the LLM when the
#    *alphabetic* content of the draft has actually changed since the
#    last call for this convo_id.
#
# 2. KEEP A FLAGGED PHRASE'S REASON STABLE ONCE ASSIGNED
#    Once a phrase has been flagged with a given reason, that reason is
#    remembered for the rest of the session (per convo_id) and reused
#    verbatim as long as the same phrase still appears verbatim in the
#    draft — even if the LLM is re-called (because other alphabetic
#    content changed) and would have worded the reason differently this
#    time. The reason is only replaced if the user actually edits the
#    alphabetic characters *of that phrase itself*, which removes it from
#    the draft and lets a fresh LLM call assign a new reason if it's
#    re-flagged.
_last_alpha_by_convo = {}   # convo_id -> last alphabetic-only text seen
_reason_ledger_by_convo = {}  # convo_id -> {lowercased phrase: reason}


_ALPHA_ONLY_RE = re.compile(r"[^a-zA-Z]+")


def _alphabetic_signature(text):
    """
    Reduce text to just its lowercased alphabetic characters, so that
    edits which only add/remove spaces, punctuation, digits, or emoji
    are indistinguishable from a no-op for change-detection purposes.

    :param text: any text
    :type text: str
    :return: lowercased alphabetic-only signature
    :rtype: str
    """
    return _ALPHA_ONLY_RE.sub("", text or "").lower()


def _get_reason_ledger(convo_id):
    return _reason_ledger_by_convo.setdefault(convo_id, {})


def _apply_sticky_reasons(convo_id, flagged):
    """
    Merge freshly-returned {"phrase", "reason"} items with this session's
    remembered reasons: if a phrase was already flagged before, keep its
    original reason instead of the LLM's newest wording, and record any
    genuinely new phrase's reason for future reuse.

    :param convo_id: id used to scope the per-session ledger
    :param flagged: list of {"phrase": ..., "reason": ...} dicts fresh
        from this LLM call
    :return: list of {"phrase": ..., "reason": ...} dicts with reasons
        stabilized against the ledger
    :rtype: list[dict]
    """
    ledger = _get_reason_ledger(convo_id)
    result = []
    for item in flagged:
        phrase = item["phrase"]
        key = phrase.lower()
        if key in ledger:
            reason = ledger[key]
        else:
            reason = item["reason"]
            ledger[key] = reason
        result.append({"phrase": phrase, "reason": reason})
    return result


def _forget_edited_phrases(convo_id, current_text):
    """
    Drop any ledger entries whose phrase no longer appears verbatim
    (case-insensitively) in the current draft. This is what makes a
    reason "unstick": once the user edits the alphabetic characters of a
    previously-flagged phrase enough that it's no longer a substring of
    the draft, its remembered reason is forgotten, so if the user later
    retypes that same phrase it's treated as newly flagged and a fresh
    reason is assigned. Phrases that still appear untouched elsewhere in
    the draft keep their remembered reason.

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

    The LLM is only re-called when the alphabetic content of the draft
    has changed since the last call for this convo_id; purely
    punctuation/whitespace/emoji edits reuse the previous ranges as-is
    (recomputed against the new text so positions stay correct even
    though nothing was re-judged).

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
        _last_alpha_by_convo.pop(convo_id, None)
        _reason_ledger_by_convo.pop(convo_id, None)
        return []

    # A phrase that's no longer present at all (edited away) shouldn't
    # keep polluting the ledger forever, regardless of whether we call
    # the LLM this round or not.
    _forget_edited_phrases(convo_id, text)

    alpha_sig = _alphabetic_signature(text)
    alpha_unchanged = _last_alpha_by_convo.get(convo_id) == alpha_sig

    if alpha_unchanged:
        # Nothing alphabetic changed — don't re-call the LLM. Just
        # re-derive ranges for the phrases we already know about against
        # the (possibly shifted, due to punctuation/space edits)
        # current text, using their stable, ledgered reasons.
        ledger = _get_reason_ledger(convo_id)
        flagged = [{"phrase": phrase, "reason": reason}
                   for phrase, reason in _ledger_phrases_with_original_casing(ledger, text)]
        return _phrases_to_ranges(text, flagged)

    flagged = _call_llm_for_toxicity(convo, latest_id, text, bucket)
    flagged = _apply_sticky_reasons(convo_id, flagged)
    ranges = _phrases_to_ranges(text, flagged)

    _last_alpha_by_convo[convo_id] = alpha_sig
    return ranges


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

        return {
            "type": "highlighting",
            "triggerEvent": self.trigger_event,
            "variant": self.variant,
            "reason": reason,
            "enabled": True,
            "highlight_indices": highlight_ranges,
        }