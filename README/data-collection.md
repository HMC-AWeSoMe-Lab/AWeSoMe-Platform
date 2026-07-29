# Data Collection

Usually, the researchers conduct user studies to analyze the difference in participants' behaviors. This can help them see how an intervention works and what influence it has on participants. As a result, our platform collects data about user actions and triggered interventions to help researchers analyze them.

Before the entire experiment, researchers must initialize the database by running the command: 

**python backend/database/init_db.py**

Initializing the database after the beginning of the experiment will lead to data loss. 

Data is automatically collected and stored as SQL tables during the experiment. There are five tables in total: POST, latest_id, trial_mode, questionnaire_response, and triggered_interventions. All data will be stored locally on the researchers' server by default. The types of data collected and corresponding explanations are listed below.

The researchers can easily export these tables by running export_data.py. 

## Table 1: POST

This table records almost all actions the participants do on the chat page, including mouse movement, keystrokes, clicks, text selection, and intervention triggers.

| Column | Type | Description |
|---|---|---|
| `action_type` | `TEXT` | The kind of event that occurred (see full list below). |
| `interaction_id` | `INTEGER` | The participant/session ID this event belongs to (assigned once per page load via `GET /get_id`). |
| `payload` | `TEXT` | Event-specific data, whose meaning depends on `action_type` (e.g. an element ID, a keystroke, JSON metadata). Empty/`NULL` for events that carry no extra data. |
| `current_text` | `TEXT` | A snapshot of whatever the participant currently has typed in the comment textarea at the moment of the event (**not** limited to text-input events — it's captured on every logged event). |
| `current_timestamp` | `DATETIME` | ISO-8601 timestamp of when the event was logged. |

> Note: `posts` has no `id`/primary key column — rows are only distinguishable by `interaction_id` + `current_timestamp`.
</br>

#### `action_type` values

| `action_type` | When it's logged | `payload` example | `current_text` example |
|---|---|---|---|
| `START` | Once, when the conversation page finishes loading. | *(empty)* | *(empty)* |
| `MODE` | Once, right after the participant is assigned to an experiment condition. | `"treatment"` or `"control"` | *(empty)* |
| `MOUSE_ENTER` | Cursor enters a comment card in the conversation thread. | The DOM `id` of the comment card, e.g. `"first-comment"` or the underlying utterance ID. | Current textarea draft, if any. |
| `MOUSE_LEAVE` | Cursor leaves a comment card in the conversation thread. | Same as `MOUSE_ENTER`. | Current textarea draft, if any. |
| `{ELEMENT_ID}_MOUSE_ENTER` | Cursor enters any element tagged with a `data-event-id` attribute (a generic hook for tracking hover on specific UI elements beyond comment cards). | The element's `data-event-id` value. | Current textarea draft, if any. |
| `{ELEMENT_ID}_MOUSE_LEAVE` | Cursor leaves such an element. | Same as above. | Current textarea draft, if any. |
| `HIGHLIGHT_COMMENT` | Participant selects/highlights text within a comment card. | JSON object: `{"elementId": ..., "selectedText": ..., "textLength": ..., "interventionType": ..., "interventionId": ..., "timestamp": ...}`. | Current textarea draft, if any. |
| `HIGHLIGHT_TEXT_AREA` | Participant selects text inside their own reply textarea (via keyboard, e.g. Shift+Arrow). | The exact substring selected, e.g. `"this is so"`. | The full draft text (same textarea the selection came from). |
| `HIGHLIGHT_INTERVENTION` | The frontend requests fresh highlight ranges for the participant's live draft (fires as they type, feeding the "toxic word" highlighting intervention). | The full draft text sent for analysis. | The full draft text (same as `payload`). |
| `FEEDBACKBOX_TEXT_SELECT` | Participant selects text inside a rendered feedback-box intervention. | JSON: `{"elementId": ..., "selectedText": ..., "textLength": ..., "interventionType": "FEEDBACKBOX", "interventionId": ..., "timestamp": ...}`. | Current textarea draft, if any. |
| `POPUP_TEXT_SELECT` | Participant selects text inside a rendered popup intervention. | Same shape as `FEEDBACKBOX_TEXT_SELECT`, with `"interventionType": "POPUP"`. | Current textarea draft, if any. |
| `KEYSTROKE` | Every keydown, and every copy/paste event, anywhere on the page. | The key pressed (e.g. `"a"`, `"Backspace"`) for keydown; `"copy"` or `"paste"` for clipboard events. | The draft text at that moment. |
| `BUTTON_CLICK` | A `<button>` element is clicked (reply, cancel, submit, feedback "See more", etc.). | JSON: `{"button_id": ..., "click_count": ...}` for generic tracked clicks, or just the raw button/element ID string for the reply and cancel buttons specifically (e.g. `"reply-btn"`, `"cancel-button"`). | The draft text at that moment. |
| `ELEMENT_CLICK` | A click occurs on any non-button element (fallback/general click tracking). | The clicked element's `id`, or `"unknown_element"` if it has none. | The draft text at that moment. |
| `FINISH` | Participant successfully submits ("posts") their comment. | *(empty)* | The final submitted comment text. |
| `TEXT_SELECT` | General-purpose selection logger: fires for any text selected inside an element marked as an intervention (a broader net than the two `*_TEXT_SELECT` types above). | JSON: `{"action": "TEXT_SELECT", "selectedText": ..., "elementId": ..., "elementType": ..., "textLength": ..., "timestamp": ..., "eventType": "mouseup"|"keyup", "interventionContext": {...}}`. | Current textarea draft, if any. |
| `{TYPE}_TEXT` | An intervention (`popup`, `feedbackBox`, or `highlighting`) renders and its displayed message text is extracted for logging — e.g. `POPUP_TEXT`, `FEEDBACKBOX_TEXT`, `HIGHLIGHTING_TEXT`. | The exact message text shown to the participant, e.g. `"Your message seems emotional. Want to revise?"`. | Current textarea draft, if any. |

</br>

## Table 2: Latest ID

This table contains only one content row and only records the newest interaction id. In this way, the researchers can keep track of the interaction id easily.

| Column | Type | Description |
|---|---|---|
| `interaction_id` | `INTEGER` | The most recently assigned interaction ID. Every new session gets this value, and it is then increased by 1. |

</br>

## Table 3: Trial Mode

This table records the mode that the participant is assigned to. We currently only have two randomly assigned modes, the treatment mode ("1") and the control mode ("0"). Participants in treatment mode can see all interventions, while those in control mode can see none. If the researchers want to put every participant in one mode, they can go to mode_assignment.py and make it return 0 or 1 forever.

| Column | Type | Description |
|---|---|---|
| `interaction_id` | `INTEGER` | The participant/session ID this assignment belongs to (same ID used in the other tables). |
| `mode` | `TEXT` | Which condition the participant was assigned to: `"0"` (control — no interventions) or `"1"` (treatment — interventions enabled). |

</br>

## Table 4: Questionnaire Response

This table records participants' answers to the **beginning** (`/welcome`) and **ending** (`/ending`) questionnaires. We currently have two types of questions, the multiple choices question and the free response question. The choices and response texts from the participants will be recorded in this table. Questions from the **beginning** (`/welcome`) questionnaire are named "q1", "q2", etc; questions from the **ending** (`/ending`) questionnaire are named "eq1", "eq2", etc., for the researchers to distinguish. 

| Column | Type | Description |
|---|---|---|
| `id` | `INTEGER` (primary key, autoincrement) | Unique row ID for this individual answer. |
| `interaction_id` | `INTEGER` | The participant/session ID this response belongs to (same ID used in the other tables). |
| `questionnaire` | `TEXT` | Which questionnaire this answer came from: `"beginning"` or `"ending"`. |
| `question_name` | `TEXT` | The form field name identifying which specific question was answered (see table below). |
| `answer` | `TEXT` | The participant's response — either the selected choice's value, or free-typed response text. |
| `current_timestamp` | `DATETIME` | ISO-8601 timestamp of when the questionnaire was submitted. |

</br>

#### `question_name` values

| Questionnaire | `question_name` | Question type example (Not in the table) | Question text example (Not in the table) | `answer` example |
|---|---|---|---|---|
| beginning | `q1` | Multiple-choice (Yes/No) | "Have you ever encountered toxic discussions online?" | `"1"` (Yes) or `"2"` (No) |
| beginning | `q2` | Free-response | "Please briefly describe the toxic conversation you met before. If you haven't encountered any, please write N/A." | `"Someone called me an idiot for disagreeing with them."` or `"N/A"` |
| ending | `eq1` | Multiple-choice (Yes/No) | "Do you think this conversation is toxic?" | `"1"` (Yes) or `"2"` (No) |
| ending | `eq2` | Free-response | "Please briefly describe the toxic behaviors in the conversation you just saw. If you haven't encountered any, please write N/A." | `"A couple of users were sarcastic and dismissive of others' opinions."` or `"N/A"` |

</br>

## Table 5: Triggered Interventions

This table records all interventions triggered when the participants are on the chat page. For every participant's id, the types of triggered interventions, the reasons for triggering, the content of the intervention, and the time of this trigger event will be recorded. This table facilitates the researchers to look through all interventions triggered during the experiment quickly.

| Column | Type | Description |
|---|---|---|
| `id` | `INTEGER` (primary key, autoincrement) | Unique row ID for this triggered intervention event. |
| `interaction_id` | `INTEGER` | The participant/session ID this event belongs to. |
| `intervention_type` | `TEXT` | Which kind of intervention fired (see table below). |
| `trigger_event` | `TEXT` | The frontend event that caused this intervention to be evaluated: `"onClick"`, `"onText"`, or `"onLoad"`. |
| `trigger_reason` | `TEXT` | Human-readable explanation of *why* the intervention fired. |
| `content` | `TEXT` | The actual content shown to the participant — typically the rendered HTML, or a JSON dump of the payload if no HTML was produced. |
| `current_timestamp` | `DATETIME` | ISO-8601 timestamp of when the intervention fired. |

</br>

#### `intervention_type` values

| `intervention_type` | Brief introduction | `trigger_event` example | `trigger_reason` example | `content` example |
|---|---|---|---|---|
| `popup` | A modal popup box shown to the participant, either as a gentle suggestion (dismissible with "OK") or as a **blocking** warning (requiring "Post Anyway" / "Edit Post") before a comment can be submitted. Covers both the keyword-based popups and the LLM-based toxicity submit-check popup. | `"onClick"` (e.g. clicking "submit-comment" or a feedback button) | `The user's comment includes the trigger word "stupid"` | The popup's HTML, e.g. `<div class="popup" id="popup">...<p>Your message seems emotional. Want to revise?</p>...</div>` |
| `feedbackBox` | A small positioned text box (e.g. anchored above the reply box) offering contextual writing feedback, revealed on a "See More" button click. | `"onClick"` (e.g. clicking "reply-btn") | `Feedback box conditions were met (e.g. relevant button clicked)` | The feedback box's HTML, e.g. `<div class="feedback-box" id="feedback-box-above">...Consider being more constructive!...</div>` |
| `highlighting` | Highlights specific words or phrases within the participant's live draft text — either via a static keyword list (`TRIGGER_WORDS`) or via an LLM that judges toxicity/tension in context. | `"onText"` (fires continuously as the participant types) | `The user's comment includes the trigger words "hate", "stupid"` or an LLM-provided reason such as `A direct personal insult attacking the recipient's appearance` | A JSON dump of the highlighting payload, e.g. `{"type": "highlighting", "variant": "toxicity", "highlight_indices": [[12, 17, "..."]], ...}` |
