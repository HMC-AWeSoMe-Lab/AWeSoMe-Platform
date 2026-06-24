from flask import *
from backend.services.CGA_CMV import get_convo, display_convo, get_reply_id, get_convo_depth_css, get_trajectory_summary
from config import active_adapter
from backend.database.database import insert_posts, update_latest_interaction_id, dump_payloads_db, insert_trial_mode
from backend.services.mode_assignment import add_intervention
from backend.interventions.interventionHelpers import *
from backend.interventions.popup import PopupIntervention
from backend.interventions.feedbackBox import feedbackBoxIntervention
from backend.interventions.highlighting import HighlightingIntervention
from backend.interventions.interventionHelpers import *
import os
import json
import re

 
# Initialize your interventions here !
 
INTERVENTIONS = [
    feedbackBoxIntervention(
        trigger_event="onClick",
        text_func=lambda text: "Consider being more constructive!",
        button_id="reply-btn",
        parent_id="reply-box",
        relation="above",
        width="100%"
    ),
    HighlightingIntervention(
        trigger_event="onText",
        highlight_func=target_phrase_highlight_logic
    ),
    HighlightingIntervention(
        trigger_event="onText",
        highlight_func=simple_highlight_logic
    ),
    PopupIntervention(
        trigger_event="onClick",
        text_func=default_popup_logic,
        button_id="feedback-button-above"
    ),
    PopupIntervention(
        trigger_event="onClick",
        text_func=submit_check_logic,
        button_id="submit-comment",
        blocking=True
    )
]
 
# PRIORITY TODOs:
# COMPLETED: interventions now only run if interaction_ID is associated with TREATMENT group (mode == 1)
# TODO: ensure popup text is logged in database, along with feedback box text.
# TODO: comb through all JS files and delete obsolete code, along with deleting obsolete python files
# TODO: better document data entry patterns across files, needs a more intuitive writeup
# TODO: find out how we could enable popupOnSubmit to not actually submit the comment until a certain button is pressed
 
 
 
# Initializes app as an instance of Flask
app = Flask(__name__)
 
# need secret key to use session stuff
app.secret_key = os.urandom(24)
 
 
# Cache to store conversations by ID
# This allows us to avoid re-fetching from the database for each request
# and keeps the latest conversation in memory.
# can't store conversations in session because they
# are not jsonify-able
convo_cache = {}
 
# Loads corpus only once at startup
 
 
def is_treatment():
    """
    Check if the current session is in treatment mode.
 
    :return: True if the session mode is 1 (treatment), False otherwise
    :rtype: bool
    """
    return session.get('mode') == 1

def get_or_create_convo():
    convo_id = session.get('convo_id')
    if convo_id and convo_id in convo_cache:
        print(f"📖 Resuming existing conversation: {convo_id}")
        return convo_cache[convo_id]

    print(f"🆕 Loading new conversation")
    convo = get_convo()
    convo_cache[convo.id] = convo
    session['convo_id'] = convo.id
    return convo
 
# Grabs path to FLASK_WEBSITE/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
settings_path = os.path.join(BASE_DIR, 'static', 'settings.json')
 
# Grabs current settings from settings.json
with open(settings_path, "r") as file:
    settings = json.load(file)
    placeholder_text = settings["commentBox"]["placeholderText"]
    submit_button_text = settings["commentBox"]["submitButtonText"]
    # Intervention toggles — edit these in static/settings.json
    reading_timer_enabled = settings["interventions"]["readingTimerEnabled"]
    min_comment_length = settings["interventions"]["minCommentLength"]
 
@app.route('/')
def root():
    """
    Root route — redirects to the welcome page.
    """
    return redirect(url_for('welcome'))
 
 
@app.route('/welcome', methods=['GET'])
def welcome():
    """
    Render the welcome page shown before the main conversation interface.
 
    :return: Rendered welcome HTML template
    :rtype: str
    """
    return render_template('welcome.html')

@app.route('/trajectory-summary', methods=['GET'])
def trajectory_summary():
    convo = get_or_create_convo()
    summary = get_trajectory_summary(convo)

    return render_template(
        'trajectory_summary.html',
        trajectory_summary=summary or "Insert Trajectory Summary here."
    )
 
@app.route('/chat', methods=['POST', 'GET'])
def index():
    """
    Main route handler for the home page.

    Gets a new conversation from the corpus, caches it, and renders the main template
    with conversation data and UI settings. Resumes existing conversation if one is
    already in the session.

    :return: Rendered HTML template with conversation data
    :rtype: str
    """
    # Assign mode to session if not already assigned (ensures randomization per user)
    if 'mode' not in session:
        session['mode'] = add_intervention()
        print(f"🎲 New user assigned to mode: {session['mode']} ({'Treatment' if session['mode'] == 1 else 'Control'})")
    else:
        print(f"📋 Existing user in mode: {session['mode']} ({'Treatment' if session['mode'] == 1 else 'Control'})")

    convo = get_or_create_convo()

    # Generate HTML for the conversation to pass to the HTML template
    reply_list = display_convo(convo)

    # Compute reading time: 1 minute per 1000 words
    all_text = " ".join(utt.text for utt in convo.iter_utterances() if utt.text)
    word_count = len(re.findall(r'\w+', all_text))
    reading_seconds = max(10, (word_count / 1000) * 60)

    return render_template(
        'index.html',
        reply_list=reply_list,
        placeholder_text=placeholder_text,
        reply_id=get_reply_id(),
        convo_depth=get_convo_depth_css(reply_list),
        submit_button_text=submit_button_text,
        reading_seconds=reading_seconds,
        reading_timer_enabled=reading_timer_enabled,
        min_comment_length=min_comment_length
    )
 
 
@app.route('/interventions', methods=['POST'])
def get_all_interventions():
    """
    Process intervention triggers and return applicable interventions.
 
    Iterates through all configured interventions and checks which ones should
    be triggered based on the provided trigger event and context data.
    Only processes interventions if the user is in the treatment group (mode == 1).
 
    :return: JSON list of intervention data for triggered interventions
    :rtype: flask.Response
    """
    # Check if user is in treatment group before processing interventions
    if not is_treatment():
        return jsonify([])
 
    # Grab data from the request
    data = request.get_json() or {}
    # Grab the current conversation from the cache
    convo = convo_cache.get(session.get('convo_id'))
 
    results = []
 
    # loop through all interventions and check if they should be triggered
    # because of the kwargs, we can add more parameters to the update method
    for intervention in INTERVENTIONS:
        try:
            result = intervention.update(
                convo=convo,
                trigger_event=data.get("triggerEvent"),
                text=data.get("text"),
                latest_id=data.get("latestID"),
                current_timestamp=data.get("currentTimestamp"),
                button_id=data.get("buttonID"),
                click_count=data.get("clickCount", 0)
            )
            if result is not None:
                results.append(result)
        except ValueError as e:
            error_message = f"Intervention Configuration Error: {str(e)}"
            print(f"❌ {error_message}")
            return jsonify({"error": error_message, "interventionError": True}), 400
        except Exception as e:
            error_message = f"Unexpected intervention error: {str(e)}"
            print(f"❌ {error_message}")
            return jsonify({"error": error_message, "interventionError": True}), 500
 
    return jsonify(results)
 
 
@app.route('/comment', methods=['POST'])
def submit_comment():
    """
    Handle the submission of a comment from the user.
 
    Expects JSON data with 'comment' field containing the comment content.
    Updates the database with the text content of the comment and the action type.
 
    :return: JSON response with new comment HTML or error message
    :rtype: flask.Response
    """
    data = request.get_json()
    comment = data.get('comment')
 
    # Grab current session's convo
    convo_id = session.get('convo_id')
    convo = convo_cache.get(convo_id)
 
    # Ensures the comment is not empty before returning a response
    if comment:
        print(f"Comment: {comment}")
        html_snippets = display_convo(convo, comment_content=[comment])
        # Grab only the HTML for the new comment
        new_comment_html = html_snippets[-1]
        return jsonify({'html': new_comment_html})
 
    return jsonify({'error': 'No comment'})
 
@app.route('/reply_style', methods=['GET'])
def reply_style():
    """
    Get conversation depth information for CSS styling.
 
    :return: JSON response with conversation depth data
    :rtype: flask.Response
    """
    convo_id = session.get('convo_id')
    convo = convo_cache.get(convo_id)
 
    return jsonify({'convoDepth': get_convo_depth_css(display_convo(convo))})
 
 
@app.route('/get_id', methods=['GET'])
def get_next_interaction_id():
    """
    Retrieve the next interaction ID from the database and send to the frontend.
 
    :return: JSON object containing the next interaction ID
    :rtype: flask.Response
    :raises: Returns 400 if there is an issue with the interaction ID table
    """
    interaction_id = update_latest_interaction_id()
    data = {'interaction_id': interaction_id}
    return jsonify(data)
 
 
@app.route('/start', methods=['POST'])
def start():
    """
    Handle the start action for a user interaction session.
 
    Extracts interaction ID, action type, and timestamp from the request,
    then inserts the data into the posts table.
 
    :return: JSON response with completion status or error
    :rtype: flask.Response
    """
    data = request.get_json()
    latest_id = data.get('id')
    action_type = data.get('actionType')
    current_timestamp = data.get('currentTimestamp')
 
    insert_posts(action_type, latest_id, current_timestamp)
 
    if latest_id and action_type and current_timestamp:
        print(f"latest_id: {latest_id}")
        print(f"action_type: {action_type}")
        print(f"current_timestamp: {current_timestamp}")
        return jsonify({"Complete": latest_id})
 
    return "Error", 400
 
 
@app.route('/reply_action', methods=['POST'])
def reply_action():
    """
    Handle reply button action logging.
 
    Extracts interaction data from the request and logs button interactions
    to the database with the button ID as payload.
 
    :return: JSON response with completion status or error
    :rtype: flask.Response
    """
    data = request.get_json()
    latest_id = data.get('id')
    action_type = data.get('actionType')
    current_timestamp = data.get('currentTimestamp')
    button_id = data.get('buttonID')
 
    insert_posts(action_type, latest_id, current_timestamp, payload=button_id)
 
    if latest_id and action_type and current_timestamp:
        return jsonify({"Complete": latest_id})
    return "Error", 400
 
 
@app.route('/dump_payload', methods=['POST'])
def dump_payload():
    """
    Dump payload queue data to the database.
 
    Receives a queue of user actions and their content (e.g., keystrokes, clicks)
    and stores them in the database for analysis.
 
    :return: JSON response with completion status or error
    :rtype: flask.Response
    """
    data = request.get_json()
    dump_payloads_db(data)
 
    if data:
        return jsonify({"Complete": data})
    return "Error", 400
 
 
@app.route('/mode', methods=['GET', 'POST'])
def get_group():
    """
    Handle group assignment and mode management.
 
    Assigns a random mode to the session if not already assigned,
    and optionally inserts trial mode data when receiving a POST request with interaction ID.
    This ensures each user is randomly assigned to either control (0) or treatment (1) group.
 
    :return: JSON response with mode information
    :rtype: flask.Response
    """
    if 'mode' not in session:
        session['mode'] = add_intervention()
 
    print("mode: " + str(session.get('mode')))
 
    user_mode = session['mode']
    print("is_treatment result: " + str(is_treatment()))
 
    if request.method == 'POST':
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({'error': 'Missing interaction ID'}), 400
        latest_id = data.get('id')
        insert_trial_mode(latest_id, user_mode)
 
    print(f"User assigned to mode: {user_mode} ({'Treatment' if user_mode == 1 else 'Control'})")
 
    data = {'mode': user_mode}
    return jsonify(data)
 
 
# Prevents the Flask app from running when imported as a module
if __name__ == '__main__':
    app.run(debug=True, port=5001, use_reloader=False)