# Interventions

![diagram](../static/images/interventionViz.svg)

The customizable intervention is the most important feature of our platform, since researchers can fulfill different research needs by implementing their own interventions. We have an abstract interface facilitating customization and three generic classes representing the popular ideas about interventions: the feedback box, the highlighting, and the pop-up. The researchers can add their interventions as one of the three types, or they can also write a new class for other types of interventions.

## The Base Class

# Interventions

We wrote an abstract class, `BaseIntervention`, for all interventions. We currently have three intervention classes inheriting from it: `feedbackBoxIntervention`, `HighlightingIntervention`, and `PopupIntervention`. In this way, the researchers can easily implement their interventions by writing a class inheriting from the three classes, or if they want an entirely different intervention, they can write a new class inheriting from `BaseIntervention`.

The `BaseIntervention` defined two methods that should be implemented by every intervention:

```python
update(self, convo=None, text=None, **kwargs)
get_payload(self, **kwargs)
```

`update(...)` is the public entry point that `app.py` actually calls on every intervention, once per incoming user event (keystroke, button click, page load, etc.). Its basic function is to forward `convo`, `text`, and any other keyword arguments collected into a dictionary called `**kwargs` straight to `get_payload(...)`, which contains the intervention's actual trigger logic and returns either a payload dict describing what the frontend should render, or `None` if the intervention shouldn't fire for this call. One special thing that `update(...)` does is that if the returned payload's type is `"highlighting"`, it stamps the payload with `"source_text"`, which is the exact draft text that this call was computed against. This additional feature is because of the LLM-calling toxicity highlighting, which is an example of LLM-related interventions that the researchers may implement. We will introduce the process of writing this intervention as a guide to help researchers implement new ones in the example section.

## Our Interventions
Below is a table with more information about the current interventions:

### Popup

Modal dialog boxes that overlay the entire page, drawing immediate user attention. Popups can be triggered by page load (for welcome messages), button clicks (for confirmations or warnings), or dynamically appear with text input (for real-time feedback). They feature customizable HTML content, automatic centering, and a close button.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `trigger_event` | string | Yes | When to show popup: `"onLoad"`, `"onClick"`, `"onText"` |
| `text_func` | function | Yes | Function that generates popup content (receives user text) |
| `button_id` | string | No | Specific button ID to trigger popup (for onClick events) |

### Feedback Box

Contextual information boxes that appear positioned relative to specific UI elements. Unlike popups, feedback boxes don't block page interaction and provide targeted guidance without interrupting user flow. They can be positioned above, below, left, or right of target elements with configurable widths and smart collision detection.


**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `trigger_event` | string | Yes | When to show box: `"onLoad"`, `"onClick"`, `"onText"` |
| `text_func` | function | Yes | Function that generates box content (receives user text) |
| `button_id` | string | No | Specific button ID to trigger box (for onClick events) |
| `parent_id` | string | Yes | HTML ID of element to position relative to |
| `relation` | string | No | Positioning: `"above"`, `"below"`, `"left"`, `"right"`, `"inside"` (default: `"right"`) |
| `width` | string | No | CSS width value (default: `"220px"`) |


### Highlighting

Real-time highlights that appear as a user drafts their reply in the text area. Highlights only interact with text actively being typed. 

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `trigger_event` | string | Yes | When to show highlights: `"onLoad"`, `"onClick"`, `"onText"` |
| `highlight_func` | function | Yes | Function that generates box content (receives user text) |

## Worked Example

If you would like to see a worked example of how to add a highlight intervention using LLM reasoning, please click the link below.
[**Example: LLM Highlighting Intervention**](example-LLM-highlight.md)
