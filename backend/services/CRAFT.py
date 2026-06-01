import convokit
import time
import random
from convokit import (
    Utterance, Conversation, Speaker,
    download, Corpus, Forecaster, CRAFTModel
)

craftOn = True # Set to False to disable CRAFT functionality

corpus = Corpus(filename=download("conversations-gone-awry-cmv-corpus"))
DEVICE = "cuda"  # or "cpu"

def get_CRAFT_model():
    """
    Initializes and returns a CRAFTModel for forecasting.
    This model is pre-trained on the Conversations Gone Awry (CGA) dataset.
    """
    return CRAFTModel("craft-cmv-finetuned", torch_device=DEVICE)

def get_CRAFT_forecaster(craft_model):
    """
    Initializes and returns a Forecaster using the CRAFT model.
    This forecaster is used to predict whether an utterance will escalate a conversation.
    """
    return Forecaster(craft_model, "has_removed_comment")

def transform_selector(context):
    return True

def getToxicityScore(draft, convo, craft_forecaster ):
    if craftOn:
        utt_list = list(convo.iter_utterances())
        utt = Utterance(
            id="new", 
            speaker=Speaker(), 
            text=draft, 
            conversation_id=convo.id, 
            timestamp=time.time(), 
            reply_to=utt_list[-1].id
        )
        utt_list.append(utt)
        new_corpus = Corpus(utterances=utt_list)

        for convo in new_corpus.iter_conversations():
            convo.add_meta("has_removed_comment", True)  # ground truth

        transformed_corpus = craft_forecaster.transform(new_corpus, transform_selector)
        new_utt_list = list(transformed_corpus.iter_utterances())
        return new_utt_list[-1].meta['forecast_prob']
    else:
        return random.uniform(0, 1)


def get_neutral_reply_text():
    """
    Returns a neutral reply text that can be displayed in the
    ConvoWizard Reply Summary hovering box. 
    This text is designed as a placeholder which will be replaced by actual warnings when the user starts
    drafting their reply.
    """
    return "<h3>ConvoWizard: Reply Summary</h3><p>ConvoWizard will notify you here if it detects anything in your comment draft</p>"

def get_reply_summary(score):
    """
    Returns a string representation of the toxicity score.
    Args:
        score (float): The toxicity score.
    Returns:
        str: A string representation of the toxicity score.
    """
    if score > 0.55:
        return "<h3>ConvoWizard: Reply Summary</h3><p>ConvoWizard thinks this comment might increase the tension in this discussion. Remember that you will be most likely to have a productive discussion with a civil, respectful, and open approach.</p>"
    else:
        return "<h3>ConvoWizard: Reply Summary</h3><p>ConvoWizard thinks this comment might decrease tension in this discussion.</p>"
    
def get_context_summary(score):
    """
    Returns a string representation of the context summary based on the toxicity score.
    Args:
        score (float): The toxicity score.
    Returns:
        str: A string representation of the context summary.
    """
    if score > 0.55:
        return "<h3>ConvoWizard: Context Summary</h3><p>ConvoWizard thinks this discussion is getting tense - some other discussions that started like this one ended up with comments getting removed. Remember that you will be most likely to have a productive discussion with a civil, respectful, and open approach.</p>"
    else:
        return "<h3>ConvoWizard: Context Summary</h3><p>ConvoWizard will notify you here if it detects anything in the preceding conversation.</p>"