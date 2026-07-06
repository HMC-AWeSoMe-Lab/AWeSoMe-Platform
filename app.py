from flask import *
from backend.convo_manager.convo_manager import get_convo, display_convo, get_reply_id, get_convo_depth_css, get_trajectory_summary
from backend.mode_assignment import add_intervention
from config import active_adapter
from backend.database.database import insert_posts, update_latest_interaction_id, dump_payloads_db, insert_trial_mode, insert_questionnaire_response
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
convo_cache = {}
 
 
def is_treatment():
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
    reply_to_anywhere = settings["interventions"].get("replyToAnywhere", True)
    # instructionEnabled toggles the whole Instruction page (route)
    instruction_enabled = settings["interventions"].get("instructionEnabled", True)
    # trajectorySummaryBoxEnabled toggles just the trajectory summary box within the page;
    # the box is only ever shown if a summary actually exists for the conversation
    trajectory_summary_box_enabled = settings["interventions"].get("trajectorySummaryBoxEnabled", True)
    welcome_page_enabled = settings["interventions"].get("welcomePageEnabled", True)
    # entryQuestionnaireEnabled is only meaningful if welcomePageEnabled is True
    entry_questionnaire_enabled = welcome_page_enabled and settings["interventions"].get("entryQuestionnaireEnabled", True)
    exit_page_enabled = settings["interventions"].get("exitPageEnabled", True)
    # exitQuestionnaireEnabled is only meaningful if exitPageEnabled is True
    exit_questionnaire_enabled = exit_page_enabled and settings["interventions"].get("exitQuestionnaireEnabled", True)

@app.route('/')
def root():
    if welcome_page_enabled:
        return redirect(url_for('welcome'))
    if instruction_enabled:
        return redirect(url_for('instruction'))
    return redirect(url_for('index'))

@app.route('/welcome', methods=['GET'])
def welcome():
    if not welcome_page_enabled:
        if instruction_enabled:
            return redirect(url_for('instruction'))
        return redirect(url_for('index'))
    return render_template('welcome.html', entry_questionnaire_enabled=entry_questionnaire_enabled)

@app.route('/instruction', methods=['GET'])
def instruction():
    if not instruction_enabled:
        return redirect(url_for('index'))

    convo = get_or_create_convo()
    summary = get_trajectory_summary(convo)

    # Only show the trajectory summary box if a summary exists for this conversation
    # AND the box is toggled on in settings.json. If no summary exists, it never shows.
    show_trajectory_summary = bool(summary) and trajectory_summary_box_enabled

    return render_template(
        'instruction.html',
        trajectory_summary=summary,
        show_trajectory_summary=show_trajectory_summary
    )

@app.route('/ending', methods=['GET'])
def ending():
    if not exit_page_enabled:
        return redirect(url_for('done'))
    if not session.get('has_commented'):
        return redirect(url_for('index'))
    return render_template('ending.html', exit_questionnaire_enabled=exit_questionnaire_enabled)
 
@app.route('/chat', methods=['POST', 'GET'])
def index():
    if 'mode' not in session:
        session['mode'] = add_intervention()
        print(f"🎲 New user assigned to mode: {session['mode']} ({'Treatment' if session['mode'] == 1 else 'Control'})")
    else:
        print(f"📋 Existing user in mode: {session['mode']} ({'Treatment' if session['mode'] == 1 else 'Control'})")

    convo = get_or_create_convo()

    reply_list = display_convo(convo)

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
        min_comment_length=min_comment_length,
        reply_to_anywhere=reply_to_anywhere,
        has_commented=session.get('has_commented', False)
    )
 
 
@app.route('/interventions', methods=['POST'])
def get_all_interventions():
    if not is_treatment():
        return jsonify([])
 
    data = request.get_json() or {}
    convo = convo_cache.get(session.get('convo_id'))
 
    results = []
 
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
    data = request.get_json()
    comment = data.get('comment')
 
    convo_id = session.get('convo_id')
    convo = convo_cache.get(convo_id)
 
    if comment:
        session['has_commented'] = True
        session.modified = True
        print(f"Comment: {comment}")
        html_snippets = display_convo(convo, comment_content=[comment])
        new_comment_html = html_snippets[-1]
        return jsonify({'html': new_comment_html})
 
    return jsonify({'error': 'No comment'})
 
@app.route('/reply_style', methods=['GET'])
def reply_style():
    convo_id = session.get('convo_id')
    convo = convo_cache.get(convo_id)
 
    return jsonify({'convoDepth': get_convo_depth_css(display_convo(convo))})
 
 
@app.route('/get_id', methods=['GET'])
def get_next_interaction_id():
    interaction_id = update_latest_interaction_id()
    data = {'interaction_id': interaction_id}
    return jsonify(data)
 
 
@app.route('/start', methods=['POST'])
def start():
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
    data = request.get_json()
    dump_payloads_db(data)
 
    if data:
        return jsonify({"Complete": data})
    return "Error", 400
 
 
@app.route('/mode', methods=['GET', 'POST'])
def get_group():
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
 
@app.route('/submit_questionnaire', methods=['POST'])
def submit_questionnaire():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    questionnaire = data.get('questionnaire')
    responses = data.get('responses', {})
    current_timestamp = data.get('currentTimestamp')
    interaction_id = data.get('interaction_id') or session.get('interaction_id')

    if not questionnaire or not responses:
        return jsonify({'error': 'Missing questionnaire or responses'}), 400

    for question_name, answer in responses.items():
        insert_questionnaire_response(
            interaction_id=interaction_id,
            questionnaire=questionnaire,
            question_name=question_name,
            answer=str(answer),
            current_timestamp=current_timestamp
        )

    print(f"📋 Stored {len(responses)} response(s) for '{questionnaire}' questionnaire (interaction_id={interaction_id})")
    return jsonify({'ok': True, 'stored': len(responses)})




@app.route('/done', methods=['GET'])
def done():
    session.clear()
    return "<h2 style='font-family:Lato,sans-serif;text-align:center;margin-top:4rem;'>You're all done! You may now close this tab.</h2>"
 


if __name__ == '__main__':
    app.run(debug=True, port=5001, use_reloader=False)