from backend.services.SCD_helpers import get_SCD

def text_to_insert(convo):
    """
    Get SCD (Stance Change Dialog) text for a conversation.

    :param convo: Conversation object to generate SCD text for
    :type convo: convokit.Conversation
    :return: SCD text generated for the conversation
    :rtype: str
    """
    return get_SCD(convo)

def get_summary_popup_logic(convo):
    from backend.services.SCD_helpers import get_SCD
    return get_SCD(convo)  # reads from convo.meta["conversation_summary"]

def default_popup_logic(text):
    """
    Default logic for determining popup text based on user input.

    Analyzes the input text and returns appropriate popup messages
    based on content and characteristics.

    :param text: User input text to analyze
    :type text: str
    :return: Popup message text
    :rtype: str
    """
    if not text:
        return "Start typing something..."
    elif "angry" in text.lower():
        return "Your message seems emotional. Want to revise?"
    elif len(text) > 200:
        return "That's a long message — want to simplify?"
    return "Looks good — just double-check your tone!"

def always_please(_):
    """
    Simple function that always returns a popup message.

    Used for testing popup functionality regardless of input.

    :param _: Unused parameter (accepts any input)
    :return: Static popup message
    :rtype: str
    """
    return "POPUP PLEASE"

def simple_highlight_logic(text):
    """
    Simple highlighting function for testing - highlights potentially problematic words.

    Scans text for predefined problematic words and returns character ranges
    to highlight in the text.

    :param text: Input text to analyze for highlighting
    :type text: str
    :return: List of [start, end] tuples indicating character ranges to highlight
    :rtype: list[list[int]]
    """
    if not text:
        return []
    
    ranges = []
    text_lower = text.lower()
    # Test with some words
    words = ["test", "stupid", "hate", "angry"]
    
    for word in words:
        start = 0
        while True:
            pos = text_lower.find(word, start)
            if pos == -1:
                break
            # Check if it's a whole word (not part of another word)
            if (pos == 0 or not text[pos-1].isalnum()) and \
               (pos + len(word) == len(text) or not text[pos + len(word)].isalnum()):
                ranges.append([pos, pos + len(word) - 1])  # inclusive end
            start = pos + 1
    
    return ranges


def target_phrase_highlight_logic(text: str) -> list:
    """
    Highlight the specific phrase "this makes no sense" in text input.
    
    :param text: Input text to analyze for the target phrase
    :type text: str
    :return: List of [start, end] tuples indicating character ranges to highlight
    :rtype: list[list[int]]
    """
    if not text:
        return []
    
    ranges = []
    text_lower = text.lower()
    target_phrase = "this makes no sense"
    
    start = 0
    while True:
        pos = text_lower.find(target_phrase, start)
        if pos == -1:
            break
        # Add the range for the entire phrase (inclusive end index)
        ranges.append([pos, pos + len(target_phrase) - 1])
        start = pos + 1
    
    return ranges


def get_relative_feedback_position(parent_id: str, relation: str) -> dict:
    """
    Return positioning instruction to place a feedback box relative to a parent element.

    :param parent_id: The HTML ID of the parent element (e.g., 'comment1')
    :type parent_id: str
    :param relation: The relative placement: 'right', 'left', 'above', 'below', 'inside'
    :type relation: str
    :return: Positioning instructions including parent_id, relation, and CSS adjustments
    :rtype: dict
    """

    relation = relation.lower().strip()
    offsets = {
        "right":  {"css": {"position": "absolute", "margin-left": "10px"}, "insert": "after"},
        "left":   {"css": {"position": "absolute", "margin-right": "10px"}, "insert": "before"},
        "below":  {"css": {"position": "absolute", "margin-top": "10px", "display": "block"}, "insert": "after"},
        "above":  {"css": {"position": "absolute", "margin-bottom": "10px", "display": "block"}, "insert": "before"},
        "inside": {"css": {"position": "relative", "padding": "10px"}, "insert": "inside"}
    }

    # default to below
    settings = offsets.get(relation, offsets["below"])

    return {
        "parent_id": parent_id,
        "relation": relation,
        "css": settings["css"],
        "insert_mode": settings["insert"]
    }


def get_highlights(draft):
    """
    Get highlight ranges for testing purposes.

    Returns hardcoded highlight ranges for testing the highlighting system.

    :param draft: Text to analyze (unused in this test implementation)
    :type draft: str
    :return: List of tuples representing character ranges to highlight
    :rtype: list[tuple[int, int]]
    """
    return [(0, 3), (6, 8)]  # highlight from index 0-3 and 6-8 inclusive


def default_highlight_logic(text):
    """
    Default highlighting logic - highlights potentially problematic words.

    :param text: Text input to analyze
    :type text: str
    :return: List of [start, end] tuples indicating character ranges to highlight
    :rtype: list[list[int]]
    """
    if not text:
        return []
        
    # Example: highlight words that might be problematic
    problematic_words = ["stupid", "idiot", "hate", "terrible", "awful", "dumb"]
    ranges = []
    text_lower = text.lower()
    
    for word in problematic_words:
        start = 0
        while True:
            pos = text_lower.find(word, start)
            if pos == -1:
                break
            # Check if it's a whole word (not part of another word)
            if (pos == 0 or not text[pos-1].isalnum()) and \
                (pos + len(word) == len(text) or not text[pos + len(word)].isalnum()):
                ranges.append([pos, pos + len(word) - 1])  # inclusive end
            start = pos + 1
            
    return ranges


TRIGGER_WORDS = ["stupid", "idiot", "hate", "angry", "dumb", "terrible", "awful"]

def submit_check_logic(text):
    """
    Checks the draft comment for trigger words before posting.

    :param text: User input text to analyze
    :type text: str
    :return: Warning message if a trigger word is found, otherwise None
    :rtype: str or None
    """
    if not text:
        return None

    text_lower = text.lower()
    for word in TRIGGER_WORDS:
        if word in text_lower:
            return "Your message may come across as harsh. Consider revising before posting."

    return None