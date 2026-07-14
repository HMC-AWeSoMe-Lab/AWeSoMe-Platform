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


Example output for a draft like "yeah sure, whatever you say, genius":
[{"phrase": "whatever you say, genius", "reason": "Sarcastic dismissal that mocks the other speaker rather than engaging with their point."}]

Example output for a draft like "You are stupid and ugly":
[{"word": "ugly", "reason": "A direct personal insult attacking the recipient's phhysical appearance."}]

Example output for a draft like "You are ugly and stupid":
[{"phrase": "You are ugly", "reason": "A direct personal insult attacking the recipient's phhysical appearance."}]


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
# Per-session caching
# ---------------------------------------------------------------------------
# Keyed by convo_id (the id of the active conversation / session), so one
# user's in-progress typing never returns another user's cached result.
# Value: {"text": last text checked, "latest_id": ..., "ranges": [...]}
_cache = {}


def _get_cached(convo_id, text, latest_id):
    entry = _cache.get(convo_id)
    if entry and entry["text"] == text and entry["latest_id"] == latest_id:
        return entry["ranges"]
    return None


def _set_cached(convo_id, text, latest_id, ranges):
    _cache[convo_id] = {"text": text, "latest_id": latest_id, "ranges": ranges}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def toxic_highlight_logic(text, convo=None, convo_id=None, latest_id=None, bucket=0):
    """
    Main entry point: given the draft text and conversation context,
    return [start, end, reason] character ranges to highlight, where
    `reason` is the LLM's own justification for that specific phrase.

    Calls the LLM fresh unless the (text, latest_id) pair matches the
    last call made for this convo_id, in which case the cached result is
    reused.

    :param text: the user's draft comment text
    :param convo: Conversation object (or None)
    :param convo_id: id used to scope the per-session cache
    :param latest_id: id of the utterance being replied to
    :param bucket: parallelization bucket, passed through to call_llama
    :return: list of [start, end, reason] ranges
    :rtype: list[list]
    :raises ValueError: if the LLM call fails or returns unparseable output
    """
    if not text:
        return []

    cached = _get_cached(convo_id, text, latest_id)
    if cached is not None:
        return cached

    flagged = _call_llm_for_toxicity(convo, latest_id, text, bucket)
    ranges = _phrases_to_ranges(text, flagged)

    _set_cached(convo_id, text, latest_id, ranges)
    return ranges


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