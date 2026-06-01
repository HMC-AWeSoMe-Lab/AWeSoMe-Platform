from convokit import Corpus, download
import markdown
import os
import json


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  
settings_path = os.path.join(BASE_DIR, 'static', 'settings.json')

def get_corpus():
    """
    Load and return the corpus from ConvoKit.

    :return: ConvoKit Corpus object containing conversation data
    :rtype: convokit.Corpus
    """
    # alerts python that we want to use the global var
    # otherwise _reddit_corpus would be treated locally
    # ----- FILL IN PATH TO CORPUS HERE -----
    return Corpus("/home/ssegal/.convokit/saved-corpora/SCD-corpus")

# admin_mode allowing for admin features to be toggled on and off
# such as the ability to select a specific conversation to display
admin_mode = False

# print("CGA_CMV loaded and corpus initialized.")

last_utt_id = ""

def get_convo(corpus):
    """
    Fetch a conversation from the CMV corpus.

    If admin_mode is True, fetches a specific conversation from the CMV corpus.
    If admin_mode is False, fetches a random conversation from the CMV corpus.

    :param corpus: ConvoKit corpus object to select conversation from
    :type corpus: convokit.Corpus
    :return: A conversation object from the corpus
    :rtype: convokit.Conversation
    """
    print("get_convo() called")

    if admin_mode:
        return None
    else:
        return corpus.random_conversation()

utt_ids = []
user_dict = {}

def display_convo(c, comment_content=None):
    """
    Generate HTML elements for displaying a conversation with progressive indentation.

    Converts a ConvoKit conversation object into a list of HTML strings,
    each representing an utterance with appropriate indentation and styling.

    :param c: The conversation object to display
    :type c: convokit.Conversation
    :param comment_content: Optional additional comment content to append
    :type comment_content: list or None
    :return: List of HTML strings representing each utterance in the conversation
    :rtype: list[str]
    """
    with open(settings_path, "r") as file:
        settings = json.load(file)
        indent_size = settings["theme"]["commentIndentation"] 
        reply_in_comments = bool(settings["commentBox"]["replyInComments"])
        display_score = bool(settings["commentBox"]["displayScore"])
        anon_users = bool(settings["commentBox"]["anon_users"])
    reply_list =[]
    depth_counter = 1

    reply_button_html = ""
    score_html = ""

    speakerCount = 1

    for utt in c.iter_utterances():
        user_dict[str(utt.speaker.id)] = ""

    for utt in c.iter_utterances():
        if anon_users:
            utt_ids.append(str(utt.speaker.id))
            if user_dict[str(utt.speaker.id)] != "":
                pass
            else:
                user_dict[str(utt.speaker.id)] = "Speaker " + str(speakerCount)
                speakerCount += 1
        else:
            utt_ids.append(str(utt.speaker.id))
            user_dict[str(utt.speaker.id)] = str(utt.speaker.id)


        if reply_in_comments:
            reply_button_html = "<button class=\"reply\" id=" + str(utt.id) + ">reply</button>"

        if display_score:
            score_html = "<div> Score: "+ str(utt.meta["score"]) +"</div>"


        formatted_text = processed_quotes(utt.text)

        reply_list.append("<div class=\"comment__container\" style=\"margin-left:"+ str(depth_counter) + "rem; margin-top: 1rem;\">" + "<div id = \"" + str(utt.id) + "\" class=\"comment__card\">"
                            + "<h3 class=\"comment__title\">" + user_dict[str(utt.speaker.id)] + "</h3>"
                             + markdown.markdown(formatted_text, extensions=['extra'], output_format='html5') + "<div class=\"comment-card-footer\">" + reply_button_html + score_html +
                            "</div>" + "</div>" + "</div>")
        depth_counter += indent_size
    # Optional: Add user comments at the end
    if comment_content:
        for comment in comment_content:
            formatted = markdown.markdown(processed_quotes(comment), extensions=['extra'])
            reply_list.append(f'''
                <div class="comment__container" style="margin-left:{depth_counter}rem; margin-top: 1rem;">
                    <div id="UserID" class="comment__card">
                        <h3 class="comment__title">SODA</h3>
                        {formatted}
                        <div class="comment-card-footer"><div> Score: -100</div></div>
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