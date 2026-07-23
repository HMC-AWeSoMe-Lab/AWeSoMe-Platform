# Interventions

![diagram](../static/images/interventionViz.svg)

The customizable intervention is the most important feature of our platform, since researchers can fulfill different research needs by implementing their own interventions. We have an abstract interface facilitating customization and three generic classes representing the popular ideas about interventions: the feedback box, the highlighting, and the pop-up. The researchers can add their interventions as one of the three types, or they can also write a new class for other types of interventions.

## The Base Class

We wrote an abstract class, `BaseIntervention`, for all interventions. We currently have three intervention classes inheriting from it: `feedbackBoxIntervention`, `HighlightingIntervention`, and `PopupIntervention`. In this way, the researchers can easily implement their interventions by writing a class inheriting from the three classes, or if they want an entirely different intervention, they can write a new class inheriting from `BaseIntervention`.

The `BaseIntervention` defined two methods that should be implemented by every intervention: `update(self, convo=None, text=None, **kwargs)` and `get_payload(self, **kwargs)`. `update(...)` is the public entry point that `app.py` actually calls on every intervention, once per incoming user event (keystroke, button click, page load, etc.). Its basic function is to forward `convo`, `text`, and any other keyword arguments collected into a dictionary called `**kwargs` straight to `get_payload(...)`, which contains the intervention's actual trigger logic and returns either a payload dict describing what the frontend should render, or `None` if the intervention shouldn't fire for this call. One special thing that `update(...)` does is that if the returned payload's type is `"highlighting"`, it stamps the payload with `"source_text"`, which is the exact draft text that this call was computed against. This additional feature is because of the LLM-calling toxicity highlighting, which is an example of LLM-related interventions that the researchers may implement. We will introduce the process of writing this intervention as a guide to help researchers implement new ones in the example section.


## Our Interventions

Below is a table with more information about the current interventions:

### Popup

Modal dialog boxes that overlay the entire page, drawing immediate user attention. Popups can be triggered by page load (for welcome messages), button clicks (for confirmations or warnings), or dynamically appear with text input (for real-time feedback). They feature customizable HTML content and automatic centering. Non-blocking popups show a single "OK" close button; blocking popups (see `blocking` below) replace that with "Post Anyway" / "Edit Post" buttons instead.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `trigger_event` | string | Yes | When to show popup: `"onLoad"`, `"onClick"`, `"onText"` |
| `text_func` | function | Yes | Function that generates popup content (receives user text). Return `None` to suppress the popup for that call. |
| `button_id` | string | No | Specific button ID to trigger popup (required if `trigger_event` is `"onClick"`) |
| `blocking` | boolean | No | If `True`, shows "Post Anyway" / "Edit Post" buttons instead of "OK", and prevents the comment from posting until the user chooses. Defaults to `False`. |

### Feedback Box

Contextual information boxes that appear positioned relative to specific UI elements. Unlike popups, feedback boxes don't block page interaction and provide targeted guidance without interrupting user flow. They can be positioned above, below, left, right, or inside a target element, with configurable widths and collision detection: `"left"`/`"right"` positioning automatically flips to the opposite side if the box would overflow the viewport.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `trigger_event` | string | Yes | When to show box: `"onLoad"`, `"onClick"`, `"onText"` |
| `text_func` | function | Yes | Function that generates box content (receives user text) |
| `button_id` | string | No | Specific button ID to trigger box (required if `trigger_event` is `"onClick"`) |
| `parent_id` | string | No | HTML ID of element to position relative to. If omitted, the box falls back to fixed page positioning instead of being anchored to an element. |
| `relation` | string | No | Positioning: `"above"`, `"below"`, `"left"`, `"right"`, `"inside"` (default: `"right"`) |
| `width` | string | No | CSS width value (default: `"220px"`) |

### Highlighting

Real-time highlights that appear as a user drafts their reply in the text area. In addition to updating live as the user types, existing highlighted spans respond to mouse hover with a tooltip showing why that span was flagged.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `trigger_event` | string | No | Only `"onText"` is currently supported — the highlighting intervention returns nothing for `onClick`, and there is no `onLoad` handling. Defaults to `"onText"`. |
| `highlight_func` | function | No | Function that takes the draft text and returns a list of `[start, end]` character ranges to highlight. Defaults to a built-in keyword matcher (`default_highlight_logic`) if omitted. Note: subclasses that need more than just the text (e.g. the LLM-based toxicity highlighter, which also needs conversation context) override the intervention's payload logic directly instead of using this parameter. |

## Worked Example

If you would like to see a worked example of how to add a highlight intervention using LLM reasoning, please click the link below.
[**Example: LLM Highlighting Intervention**](example-LLM-highlight.md)
