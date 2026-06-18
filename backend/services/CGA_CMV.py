from config import active_adapter
import markdown
import os
import json
from datetime import datetime, timezone
import pytz


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  
settings_path = os.path.join(BASE_DIR, 'static', 'settings.json')



# admin_mode allowing for admin features to be toggled on and off
# such as the ability to select a specific conversation to display
admin_mode = False

# print("CGA_CMV loaded and corpus initialized.")

last_utt_id = ""

def get_convo():
    if admin_mode:
        return None
    else:
        while True:
            convo = active_adapter.random_conversation()
            msgs = list(convo.iter_utterances())
            root = next((m for m in msgs if m.reply_to is None), None)
            if root and len(root.text.strip()) > 20:
                return convo


utt_ids = []
user_dict = {}

def display_convo(c, comment_content=None):
    with open(settings_path, "r") as file:
        settings = json.load(file)
        indent_size = settings["theme"]["commentIndentation"] 
        reply_in_comments = bool(settings["commentBox"]["replyInComments"])
        display_score = bool(settings["commentBox"]["displayScore"])
        anon_users = bool(settings["commentBox"]["anon_users"])
    
    reply_list = []
    reply_button_html = ""
    score_html = ""
    timestamp_html = ""
    speakerCount = 1

    # BUILD TREE-ORDERED UTTERANCES — depth-first traversal so each
    # reply is grouped directly under its parent (and ahead of any
    # "uncle" branches), instead of just sorting by depth.
    all_utts = list(c.iter_utterances())

    # Map utt_id -> utterance, and utt_id -> list of its direct replies
    utt_map = {u.id: u for u in all_utts}
    children_map = {}
    roots = []
    for u in all_utts:
        if u.reply_to is not None and u.reply_to in utt_map:
            children_map.setdefault(u.reply_to, []).append(u)
        else:
            # reply_to is None, or points to an utterance we don't have
            # (e.g. a deleted parent) — treat as a root for display purposes
            roots.append(u)

    # Guard against malformed cyclic reply_to chains (shouldn't happen with
    # real corpora, but avoids an infinite recursion / stack overflow if it does)
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
            # break the cycle by promoting this utterance to a root
            children_map[u.reply_to].remove(u)
            roots.append(u)

    # Keep sibling order chronological within each branch
    def _sort_key(u):
        return u.timestamp if u.timestamp is not None else float('inf')

    roots.sort(key=_sort_key)
    for sibs in children_map.values():
        sibs.sort(key=_sort_key)

    # Pre-compute each utterance's true tree depth (root = 1) for indentation
    depth_map = {}

    def assign_depths(utt, depth):
        depth_map[utt.id] = depth
        for child in children_map.get(utt.id, []):
            assign_depths(child, depth + 1)

    for root in roots:
        assign_depths(root, 1)

    # Walk the tree depth-first (pre-order): a node, then all its
    # descendants, before moving on to its next sibling.
    sorted_utts = []

    def visit(utt):
        sorted_utts.append(utt)
        for child in children_map.get(utt.id, []):
            visit(child)

    for root in roots:
        visit(root)

    def get_depth(utt):
        return depth_map.get(utt.id, 1)

    # ADD SUMMARY AS FIRST ITEM
    summary = c.meta.get("conversation_summary", "")
    summary = summary.strip()

    if summary:
        reply_list.append(f'''
            <div class="comment__container" style="margin-left:1rem; margin-top: 1rem;">
                <div id="conversation-summary" class="comment__card">
                    <h3 class="comment__title">Conversation Summary</h3>
                    <p>{summary}</p>
                </div>
            </div>
        ''')

    # FIRST LOOP — build user_dict
    for utt in sorted_utts:
        user_dict[str(utt.speaker_id)] = ""
    
    # SECOND LOOP — build HTML using true tree depth for indentation
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

        if reply_in_comments:
            reply_button_html = "<button class=\"reply\" id=" + str(utt.id) + ">reply</button>"

        if display_score and utt.score is not None:
            score_html = "<div> Score: " + str(utt.score) + "</div>"
        else:
            score_html = ""

        if utt.timestamp:
            la_tz = pytz.timezone("America/Los_Angeles")
            dt = datetime.fromtimestamp(utt.timestamp, tz=timezone.utc).astimezone(la_tz)
            timestamp_html = "<div>" + dt.strftime("%b %d, %Y %I:%M %p PT") + "</div>"

        formatted_text = processed_quotes(utt.text)

        # Use true tree depth for indentation instead of a flat counter
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

    # OPTIONAL: Add user comments at the end
    if comment_content:
        new_comment_score_html = "<div> Score: 0</div>" if display_score else ""
        # User replies go one level deeper than the deepest utterance
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
    """
    Get the ID of the last utterance in the conversation.

    :return: ID of the most recent utterance
    :rtype: str
    """
    with open(settings_path, "r") as file:
        settings = json.load(file)
        anon_users = bool(settings["commentBox"]["anon_users"])

    if anon_users:
        return user_dict[str(utt_ids[-1])]
    else:
        return utt_ids[-1]

def get_convo_depth_css(reply_list):
    """
    Calculate the depth of the conversation for CSS styling purposes.

    :param reply_list: List of conversation reply HTML elements
    :type reply_list: list
    :return: Number of replies in the conversation
    :rtype: int
    """
    return len(reply_list)


def processed_quotes(utt_text):
    """
    Process quoted text formatting in utterances.

    Handles special formatting for quoted text within utterances,
    converting quote markers to proper HTML formatting.

    :param utt_text: Raw utterance text to process
    :type utt_text: str
    :return: Processed text with quote formatting
    :rtype: str
    """
    # if '&gt;' not in utt_text:
    #     return utt_text
    lines = utt_text.split('\n')
    wrapped_lines = []
    quote_block = []

    # print(utt_text)
    

    for line in lines:

        # if line.strip().startswith('&gt'):
        #     quote_block.append(line[4:])
        if '&gt;' in line.strip():
            quote_block.append(line.strip().replace('&gt;', '', 1))
        else:
            if quote_block:
                wrapped_lines.append('<div class="quote-container">\n' + '\n'.join(quote_block) +'\n</div>')
                quote_block = []
            wrapped_lines.append(line)
    if quote_block:
        wrapped_lines.append('<div class="quote-container">\n' + '\n'.join(quote_block) +'\n</div>')
    if '&gt' in '\n'.join(wrapped_lines):
        return processed_quotes('\n'.join(wrapped_lines))
    # print('\n'.join(wrapped_lines))
    return '\n'.join(wrapped_lines)


# c = get_convo()
# print(display_convo(c))