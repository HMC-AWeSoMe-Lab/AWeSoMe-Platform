from config import active_adapter
from backend.services.CGA_CMV import processed_quotes
import markdown
import os
import json
import random
from datetime import datetime, timezone
import pytz

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
settings_path = os.path.join(BASE_DIR, 'static', 'settings.json')

admin_mode = False

def get_convo():
    if admin_mode:
        return None

    with open(settings_path, "r") as file:
        settings = json.load(file)
    convo_setting = settings.get("interventions", {}).get("conversation", "Random")

    if convo_setting == "Random":
        while True:
            convo = active_adapter.get_conversation(random.choice(active_adapter.get_conversation_ids()))
            msgs = list(convo.iter_utterances())
            root = next((m for m in msgs if m.reply_to is None), None)
            if root and len(root.text.strip()) > 20:
                return convo
    else:
        return active_adapter.get_conversation(convo_setting)

utt_ids = []
user_dict = {}

def display_convo(c, comment_content=None):
    with open(settings_path, "r") as file:
        settings = json.load(file)
        indent_size = settings["theme"]["commentIndentation"] 
        reply_in_comments = bool(settings["commentBox"]["replyInComments"])
        display_score = bool(settings["commentBox"]["displayScore"])
        anon_users = bool(settings["commentBox"]["anon_users"])
        reply_to_anywhere = bool(settings["interventions"].get("replyToAnywhere", True))
    
    reply_list = []
    reply_button_html = ""
    score_html = ""
    timestamp_html = ""
    speakerCount = 1

    all_utts = list(c.iter_utterances())

    utt_map = {u.id: u for u in all_utts}
    children_map = {}
    roots = []
    for u in all_utts:
        if u.reply_to is not None and u.reply_to in utt_map:
            children_map.setdefault(u.reply_to, []).append(u)
        else:
            roots.append(u)

    def _has_cycle(start_id):
        seen = set()
        current_id = start_id
        while current_id is not None:
            if current_id in seen:
                return True
            seen.add(current_id)
            parent = utt_map.get(current_id)
            current_id = parent.reply_to if parent else None
        return False

    for u in list(all_utts):
        if u not in roots and _has_cycle(u.id):
            children_map[u.reply_to].remove(u)
            roots.append(u)

    def _sort_key(u):
        return u.timestamp if u.timestamp is not None else float('inf')

    roots.sort(key=_sort_key)
    for sibs in children_map.values():
        sibs.sort(key=_sort_key)

    depth_map = {}

    def assign_depths(utt, depth):
        depth_map[utt.id] = depth
        for child in children_map.get(utt.id, []):
            assign_depths(child, depth + 1)

    for root in roots:
        assign_depths(root, 1)

    sorted_utts = []

    def visit(utt):
        sorted_utts.append(utt)
        for child in children_map.get(utt.id, []):
            visit(child)

    for root in roots:
        visit(root)

    def get_depth(utt):
        return depth_map.get(utt.id, 1)

    for utt in sorted_utts:
        user_dict[str(utt.speaker_id)] = ""
    
    is_first = True
    for utt in sorted_utts:
        if anon_users:
            utt_ids.append(str(utt.speaker_id))
            if user_dict[str(utt.speaker_id)] != "":
                pass
            else:
                user_dict[str(utt.speaker_id)] = "Speaker " + str(speakerCount)
                speakerCount += 1
        else:
            utt_ids.append(str(utt.speaker_id))
            user_dict[str(utt.speaker_id)] = str(utt.speaker_id)

        if reply_in_comments and reply_to_anywhere:
            reply_button_html = f'<button class="reply" data-utt-id="{utt.id}" onclick="toggleCommentBox(this)">↩ reply</button>'
        else:
            reply_button_html = ""

        if display_score and utt.score is not None:
            score_html = "<div> Score: " + str(utt.score) + "</div>"
        else:
            score_html = ""

        if utt.timestamp:
            la_tz = pytz.timezone("America/Los_Angeles")
            dt = datetime.fromtimestamp(utt.timestamp, tz=timezone.utc).astimezone(la_tz)
            timestamp_html = "<div>" + dt.strftime("%b %d, %Y %I:%M %p PT") + "</div>"

        formatted_text = processed_quotes(utt.text)

        depth = get_depth(utt)
        margin = depth * indent_size

        card_id = "first-comment" if is_first else str(utt.id)
        is_first = False

        reply_list.append("<div class=\"comment__container\" style=\"margin-left:"+ str(margin) + "rem; margin-top: 1rem;\">" + 
                          "<div id=\"" + card_id + "\" class=\"comment__card\">"
                          + "<h3 class=\"comment__title\">" + user_dict[str(utt.speaker_id)] + "</h3>"
                          + markdown.markdown(formatted_text, extensions=['extra'], output_format='html5') 
                          + "<div class=\"comment-card-footer\">" + reply_button_html + score_html + timestamp_html +
                          "</div>" + "</div>" + "</div>")

    if comment_content:
        new_comment_score_html = "<div> Score: 0</div>" if display_score else ""
        max_depth = max((get_depth(u) for u in sorted_utts), default=1)
        user_margin = (max_depth + 1) * indent_size
        for comment in comment_content:
            formatted = markdown.markdown(processed_quotes(comment), extensions=['extra'])
            reply_list.append(f'''
                <div class="comment__container" style="margin-left:{user_margin}rem; margin-top: 1rem;">
                    <div id="UserID" class="comment__card">
                        <h3 class="comment__title">SODA</h3>
                        {formatted}
                        <div class="comment-card-footer">{new_comment_score_html}</div>
                    </div>
                </div>
            ''')

    return reply_list
        
def get_reply_id():
    with open(settings_path, "r") as file:
        settings = json.load(file)
        anon_users = bool(settings["commentBox"]["anon_users"])

    if anon_users:
        return user_dict[str(utt_ids[-1])]
    else:
        return utt_ids[-1]

def get_convo_depth_css(reply_list):
    return len(reply_list)

def get_trajectory_summary(convo):
    if convo is None:
        return None
    summary = (convo.meta.get("trajectory_summary") or "").strip()
    return summary or None