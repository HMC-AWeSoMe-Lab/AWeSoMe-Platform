## Interventions

![diagram](../static/images/interventionViz.svg)

The customizable intervention is the most important feature of our platform, since researchers can fulfill different research needs by implementing their own interventions. We have an abstract interface facilitating customization and three generic classes representing the popular ideas about interventions: the feedback box, the highlighting, and the pop-up. The researchers can add their interventions as one of the three types, or they can also write a new class for other types of interventions.

### The base class

Every intervention subclasses `BaseIntervention` (`backend/interventions/base.py`), which is abstract and defines two methods:

- **`get_payload(self, **kwargs)`** — abstract; each concrete intervention must implement this. It contains the intervention's actual trigger logic and returns either a payload `dict` describing what the frontend should render, or `None` if the intervention shouldn't fire for this call.
- **`update(self, convo=None, text=None, **kwargs)`** — the public entry point that `app.py` actually calls on every intervention, once per incoming user event (keystroke, button click, page load, etc.). It forwards `convo`, `text`, and any other kwargs straight to `get_payload(...)`, and does one extra thing automatically: if the returned payload's `"type"` is `"highlighting"`, it stamps the payload with `"source_text"` — the exact draft text that this call was computed against. The frontend uses `source_text` to detect and discard stale responses (e.g. if the user kept typing while the request was in flight, discarding avoids painting highlight ranges against text that no longer matches). This additional feature is because of the LLM-calling toxicity highlighting, which is an example of LLM-related interventions that researchers may implement.

Because this stamping happens in `update()` rather than in each intervention's own `get_payload()`, it applies automatically to any highlighting-typed payload — including subclasses that override `get_payload()` entirely and never call `super().get_payload()` (e.g. `ContextualToxicityHighlightingIntervention`, below).

Each request to `/interventions` iterates over the full `INTERVENTIONS` list (defined in `app.py`) and calls `.update(...)` on each one. Any intervention whose `get_payload()` returns a non-`None` dict gets included in the JSON response sent back to the frontend; the frontend then renders whichever ones match the current `triggerEvent` (see `main.js`'s `triggerInterventions()`).

### Trigger events, not a separate "activation" step

There's no separate mechanism that watches for "the user completed an action" — each intervention declares its own `trigger_event` (e.g. `"onText"`, `"onClick"`, `"onLoad"`) at construction time, and its `get_payload()` starts by checking `self.trigger_event == trigger_event` (the event the current request is actually reporting). If they don't match, it returns `None` immediately. `onClick` interventions additionally check `button_id` against a specific `self.button_id` they were configured with. It's this event/button matching inside `get_payload()`, not the base class, that decides whether an intervention "activates" for a given user action.

### Custom variables per intervention

Concrete intervention `__init__` methods take whatever configuration that intervention type needs, passed at registration time in `app.py`'s `INTERVENTIONS` list:

- **`HighlightingIntervention`** (`backend/interventions/highlighting.py`) takes `highlight_func` — a callable `text -> list[[start, end], ...]` that decides which character ranges to highlight. If omitted, it defaults to `default_highlight_logic` (from `interventionHelpers.py`). It also takes `variant` (a string like `"default"` or `"toxicity"`, sent to the frontend so different highlighting sources can be styled/labeled independently — see `VARIANTS` in `highlighting.js`).
- **`PopupIntervention`** (`backend/interventions/popup.py`) takes `text_func` (`text -> str or None`, generates the popup's message, `None` meaning "don't show a popup"), `button_id` (required for `onClick` popups), and `blocking` (if `True`, renders "Post Anyway" / "Edit Post" buttons and the frontend prevents submission until the user chooses, instead of a plain "OK").
- **`feedbackBoxIntervention`** (`backend/interventions/feedbackBox.py`) takes `text_func`, `button_id`, plus positioning config: `parent_id` (which element to position relative to), `relation` (`"right"`/`"left"`/`"above"`/`"below"`), and `width`.

Below is a table with more information about the current interventions:

INSERT_TABLE_HERE

### `interventionHelpers.py`

`backend/interventions/interventionHelpers.py` is the central library of matching/generation logic that interventions are configured with. It doesn't get called by the base or concrete intervention classes directly — instead, its functions are passed in as the `highlight_func`/`text_func` callables (and similar config) when each intervention is constructed in `app.py`'s `INTERVENTIONS` list. This is the file researchers edit to define new intervention behavior: writing a new function here (or editing an existing one) and pointing an intervention's constructor at it is the standard way to change what an intervention actually detects or displays, without touching the intervention classes themselves. It currently includes:

- **`TRIGGER_WORDS`** — a single shared list of words (`"stupid"`, `"idiot"`, `"hate"`, etc.), used as the one source of truth by every keyword-based check below, so they can't drift out of sync with each other.
- **`default_highlight_logic` / `simple_highlight_logic`** — both scan text for whole-word matches against `TRIGGER_WORDS` and return `[start, end]` character ranges (inclusive end) for `HighlightingIntervention.highlight_func`.
- **`target_phrase_highlight_logic`** — an example of highlighting a fixed phrase instead of a word list.
- **`default_popup_logic` / `always_please` / `submit_check_logic`** — example `text_func` implementations for `PopupIntervention`.
- **`infer_trigger_reason`** — a generic, best-effort fallback that inspects the draft text against `TRIGGER_WORDS` to produce a human-readable "reason" string for logging, used when an intervention's own `get_payload()` doesn't set a more specific one.
- **`get_relative_feedback_position`** — resolves a feedback box's `relation` config into concrete CSS/insertion instructions.

To make the highlighting intervention highlight all trigger words, a researcher would add/edit `TRIGGER_WORDS` and the highlighting function (e.g. `default_highlight_logic`) here, then pass that function as `highlight_func` when constructing `HighlightingIntervention` in `app.py`.

### AI-backed interventions (`backend/services/`)

We currently keep all interventions whose logic needs an LLM call rather than a static keyword list in `backend/services/`, not `interventionHelpers.py`. But researchers can choose where they put their interventions. The example in this codebase is `backend/services/toxicityHighlight.py`, which implements contextual toxicity highlighting:

- Instead of matching a fixed word list, it sends the LLM the full conversation (all branches, not just the ancestor path), a marker showing which comment the user is replying to, and the live draft text, and asks it to return `[{"phrase": ..., "reason": ...}, ...]` for anything toxic or tension-raising.
- **`ContextualToxicityHighlightingIntervention`** is a subclass of `HighlightingIntervention` that exists specifically because `HighlightingIntervention.get_payload()` normally calls `highlight_func(text)` with just the text, no conversation context. Since `highlighting.py` itself isn't modified, this subclass overrides `get_payload()` to gather `convo`/`latest_id` and call the toxicity logic directly.
- **`ToxicitySubmitPopupIntervention`** is a companion `PopupIntervention` subclass that blocks submission if the AI highlighter flagged anything still present in the draft at submit time — reading back already-computed flags from a per-conversation "reason ledger" rather than making a second LLM call.
- The actual LLM call itself is isolated in `backend/services/callLlamaSCD.py`. If researchers want to implement LLM-related interventions, they can edit the method of calling their LLM in this file.

This pattern generalizes: any intervention whose decision logic needs to call out to a model (toxicity, stance detection, summarization, etc.) belongs in `backend/services/`, typically as a thin subclass of the relevant base intervention (`HighlightingIntervention`, `PopupIntervention`, etc.) that overrides `get_payload()` to gather extra context and call the AI logic — the base intervention classes and `interventionHelpers.py` stay reserved for synchronous, keyword/rule-based logic.
