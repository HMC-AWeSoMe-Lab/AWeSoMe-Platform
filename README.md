# A Platform for Pro-Social Interventions

This platform provides researchers of the AWeSoMe Lab with a flexible framework for studying and implementing interventions in simulated online discussions. Built around a conversation thread from Convokit's CGA-CMV dataset, it enables the creation of various intervention tools such as popups, highlighting, and feedback boxes, to name a few. The system also enables the creation of custom interventions through an object oriented programming paradigm (explained more in [Our vision](#our-vision) ).

The system supports real-time intervention deployment with sophisticated triggering mechanisms, allowing researchers to test various approaches to improving online discourse quality while maintaining detailed analytics on user interactions with heavy database logging.


## Our vision
This platform was designed using Object Oriented Programming (OOP) for ease of use and extensibility. Here's how our intervention abstract class works: All interventions inherit from `BaseIntervention`, which defines a common interface with two key methods: `update()` (which processes trigger events and parameters) and `get_payload()` (which generates the specific intervention content). This design allows researchers to create new intervention types by simply inheriting from the base class and implementing their unique `get_payload()` logic, while the framework automatically handles trigger detection, parameter validation, and error management. The OOP approach means adding a new intervention type requires no changes to the core system - just create a new class, define its behavior, and add it to the `INTERVENTIONS` list.

   ![diagram](static/images/interventionViz.svg)


## Quick Start

1. Configure interventions in `app.py` by populating the `INTERVENTIONS` list with the desired interventions (instances of classes found in `/backend/interventions`).   
2. If the file `database.db` does not exist in `/backend/database`. run `init_db.py` to create the database (and autopopulate the latest_id table with the value 0, initializing the interaction IDs).
3. Run the Flask application: `python3 app.py`
4. Visit `http://localhost:5001` to see the platform in action

## Configuring Your Convokit Corpus

This platform is designed to work with any Convokit corpus, but requires proper configuration and preprocessing to function correctly. Users must configure their chosen corpus in the `/backend/services` directory following the patterns established in our CGA-CMV implementation.

### Corpus Preprocessing

Create a corpus configuration file in `/backend/services` (following the pattern of `CGA_CMV.py`) that includes:

1. **Corpus Loading Function**: A `get_corpus()` function that loads your specific corpus
2. **Conversation Selection**: A `get_convo(corpus)` function for selecting conversations
3. **Display Processing**: A `display_convo()` function that formats conversations for web display
4. **Text Processing**: Any corpus-specific text formatting (see `processed_quotes()` in CGA_CMV.py)

### Conversation Length Considerations

**Critical**: If your corpus has functionality similar to CGA-CMV's conversation pairs or threading structure, you must account for this in your corpus processing. Consider:

- How conversations are structured in your corpus (linear threads vs. tree structures)  
- Maximum conversation depth for display purposes
- Whether conversations should be truncated or filtered by length
- How reply chains should be handled and displayed

### Framework Settings Configuration

Configure conversation display settings in `static/settings.json`:

```json
{
    "commentBox": {
        "replyInComments": true/false,     // Enable reply buttons in comments
        "displayScore": true/false,        // Show comment scores (if applicable)
        "displayCancel": true/false        // Show cancel button
    },
    "theme": {
        "commentIndentation": 1            // Indentation per reply level
    }
}
```

**For social media data**: The `"displayScore"` setting may be particularly relevant if your corpus includes engagement metrics like upvotes, likes, or scores.

### Username Handling

**Privacy & Anonymization**: Your corpus processing must handle usernames appropriately:

- **Anonymize usernames** if working with real user data to protect privacy
- Use placeholder usernames (e.g., "User1", "User2") or generated pseudonyms
- Ensure consistent username mapping across conversations
- Consider using the `Speaker.id` field in Convokit for unique identification

See how `CGA_CMV.py` handles speaker IDs in the `display_convo()` function for reference implementation.

### Score Metadata Generalization

**Lower Priority Enhancement**: The current "score" metadata code is specifically designed for CGA-CMV corpus format. For other corpora:

- Modify the score display logic in your corpus configuration file
- Update the `meta["score"]` references to match your corpus structure  
- Consider whether engagement metrics (likes, upvotes, etc.) should be displayed
- Implement fallback behavior for corpora without scoring systems

The score functionality can be found in `display_convo()` where `utt.meta["score"]` is accessed and displayed.

## Required Technical Skills

While the code you write will be mostly Python, small amounts of HTML and CSS are required to power new interventions. Below we detail a diagram of the HTML for the already implemented Popup class to help people new to web development. 

_Note that when writing HTML, things in quotes like "popup" or "popup-close-button" are entirely user-decided. We could have an intervention called fooBar with corresponding element IDs "prof" and "chang", but that would be pretty confusing! Try to match HTML element class and id names with the corresponding intervention._

_**HOWEVER**, to maintain consistent database logging, you are required to attach **data_intervention_type** to the parent wrapper of your interventions, along with **data_event_id** wherever you desire event logging for the database._ 


![diagram](static/images/HTMLexplan.drawio.svg)


Feel free to copy-paste [this starter code](#sample-intervention-html) to start building your intervention with HTML! For example CSS, see `/static/styles`. If you're stuck, ask your favorite LLM to generate styling for your intervention.


## Existing Intervention Classes

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

Real-time highlights that appear as a user drafts their reply in the text area. Hghlights only interact with text actively being typed. 

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `trigger_event` | string | Yes | When to show highlights: `"onLoad"`, `"onClick"`, `"onText"` |
| `highlight_func` | function | Yes | Function that generates box content (receives user text) |

## How to Use Interventions

1. Open `app.py` and locate the `INTERVENTIONS` list
2. Add your desired intervention instances using the classes from `/backend/interventions/`
3. Configure each intervention with appropriate parameters (see [Examples](#examples) below)
4. Run the application to see your interventions in action


## How to Create Custom Interventions

1. Create a new file `yourIntervention.py` in the `/backend/interventions/` directory
2. Import the base class:
   ```python
   from backend.interventions.base import BaseIntervention
   ```
3. Create a subclass of `BaseIntervention`:
   - Implement `get_payload()` method to return HTML content for your intervention
   - Set `trigger_event` to control when the intervention activates: `"onLoad"`, `"onClick"`, or `"onText"`
   - For onClick events, specify `button_id` to target specific buttons

4. Add helper functions to `interventionHelpers.py` ........
5. Create a CSS file `yourIntervention.css` in `/static/styles/` and link it in `index.html`:
   ```html
   <link rel="stylesheet" href="/static/styles/yourIntervention.css">
   ```

6. Necessary functions from `interventionHelpers.py` are already imported at the top of `app.py` with the line
    ```python
    from backend.interventions.interventionHelpers import *
    ```
    However, if in the future you create functions in alternate files, remember to import them in `app.py` before using them to initialize the `INTERVENTIONS` list!



## Data Collection

The platform automatically logs user interactions and intervention events with a sophisticated batching system for research analysis:

### Automatic Logging (No Setup Required)

**Standard Events**: The following user actions are automatically captured without any additional code:
- **Mouse Events**: Mouse enter/leave for all elements with `data-event-id` attributes
- **Button Clicks**: All button clicks with click counts and button IDs  
- **Text Selection**: Text highlighting within intervention elements (popups, feedback boxes)
- **Keyboard Events**: Keystrokes and key combinations in text areas
- **Navigation Events**: Page loads, comment submissions, reply toggles

### Data Flow Architecture

1. **Action Capture**: User interactions trigger `appState.setLatestAction(actionType, payload)`
2. **Queue Batching**: Actions are added to a payload queue via `pushToPayloadQueue()`
3. **Automatic Dumping**: Queue is sent to database via `/dump_payload` route when threshold is reached
4. **Database Storage**: All data stored in SQLite with timestamps and interaction IDs for analysis

### Custom Event Logging (Advanced Usage Only)

**⚠️ Only needed for custom intervention behaviors beyond standard mouse/click/select events**

If you're creating an intervention with unique interactions (e.g., drag-and-drop, custom sliders, multi-step wizards), you'll need to add custom event logging:

#### When You Need Custom Logging:
- Custom UI controls (sliders, toggles, drag-drop)
- Multi-step intervention flows  
- Timing-based interactions (hover duration, reading time)
- Custom validation or form submissions within interventions

#### How to Implement Custom Logging:

**Step 1: Add Event Listeners in Your Intervention Renderer**
```javascript
// In your intervention's JavaScript file (yourIntervention.js, which needs to be placed in /static/js/interventions)
export function renderYourIntervention(data) {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = data.html;
    const interventionElement = wrapper.firstChild;
    
    // Add custom event listener
    const customSlider = interventionElement.querySelector('.custom-slider');
    if (customSlider) {
        customSlider.addEventListener('change', async (event) => {
            // Step 2: Log the custom action
            appState.setLatestAction("SLIDER_CHANGE", {
                value: event.target.value,
                interventionId: interventionElement.id,
                timestamp: Date.now()
            });
            
            // Step 3: Queue for database storage
            await pushToPayloadQueue();
        });
    }
    
    document.body.appendChild(interventionElement);
}
```

**Step 2: Import Required Functions**
```javascript
import { appState } from '../services/appState.js';
import { pushToPayloadQueue } from '../services/payloadQueue.js';
```

#### Function Reference:

**`appState.setLatestAction(actionType, payload)`**
- **Purpose**: Records a user action with associated data
- **actionType**: String identifier (for example, "BUTTON_CLICK")  
- **payload**: Any data associated with the action (strings, objects, numbers)
- **Auto-timestamps**: Automatically adds timestamp to the action

**`pushToPayloadQueue()`**
- **Purpose**: Queues the latest action for database storage
- **Batching**: Automatically dumps queue when threshold reached (default: 10 actions)
- **Async**: Always use `await` when calling this function

**`dumpPayloadQueue()`** 
- **Purpose**: Immediately sends all queued actions to database
- **Use Case**: End of session, critical events, or manual queue clearing
- **Auto-called**: Usually handled automatically by `pushToPayloadQueue()`

### Database Schema

All logged data in the _posts_ table includes:
- **interaction_id**: Unique session identifier
- **action_type**: Type of user action (BUTTON_CLICK, TEXT_SELECT, etc.)
- **payload**: Action-specific data (button IDs, selected text, custom values)
- **current_text**: Text area content at time of action
- **timestamp**: Precise timing of user action






## Examples

### Basic Intervention Configuration
```python
INTERVENTIONS = [
    PopupIntervention(
        trigger_event="onLoad",        # Popup on page load
        text_func=default_popup_logic  # you can change this to customize the popup content
    ),

    PopupIntervention(
        trigger_event="onClick",       # different trigger event
        text_func=default_popup_logic, 
        button_id="submit-comment"     # specific button ID to trigger this popup
    ),

    feedbackBoxIntervention(  
        trigger_event="onClick",
        text_func=default_popup_logic,
        button_id="reply-button",      # Only trigger on reply button click
        parent_id="reply-box",         # ID of parent element to attach to
        relation="above",              # relative placement
        width="600px"                  # Custom width from backend
    ),
]
```


### Custom Text Functions

```python
def toxicity_warning(user_text):
    if len(user_text) > 200:
        return "Consider shortening your message for better clarity."
    elif any(word in user_text.lower() for word in ["angry", "hate", "stupid"]):
        return "Your message may come across as hostile. Consider revising."
    return "Your message looks good!"

def character_count_feedback(user_text):
    count = len(user_text)
    if count > 500:
        return f"Long message ({count} chars). Consider breaking into multiple comments."
    return f"Message length: {count} characters"
```

### Sample intervention HTML

```HTML
        <div class="your-intervention" id="your-intervention"                 
            data-intervention-type="your-intervention"                              
            data-event-id="YOUR-INTERVENTION">                                                                                  
                <h2>Your header here!</h2>                                              
                <p>Your intervention text here!</p>                                                 
                <button class="your-intervention-button" id="your-intervention-button">OK</button>   
        </div>

```
