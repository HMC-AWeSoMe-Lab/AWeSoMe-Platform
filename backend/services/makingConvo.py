from convokit import Corpus, download, Utterance, Speaker
import time

# THIS FILE WAS USED TO MAKE A CUSTOM CONVERSATION
# FOR OUR ACADEMIC POSTER
corpus = Corpus(filename=download("conversations-gone-awry-cmv-corpus"))
speaker1 = Speaker(id="CommonSense42")
speaker2 = Speaker(id="BananaBread")

utt1 = Utterance(
    id="utt1", 
    speaker=speaker1, 
    text="If you ignorantly vote based off gender alone, you're destroying democracy. I worry about you feminists.", 
    conversation_id="1", 
    timestamp=time.time(), 
    reply_to=None,
    meta={"score": 2}
)

utt2 = Utterance(
    id="utt2", 
    speaker=speaker2, 
    text="How does it destroy democracy? There's nothing \"ignorant\" about representation.", 
    conversation_id="1", 
    timestamp=time.time(), 
    reply_to=utt1.id,
    meta={"score": -4}
)

utt3 = Utterance(
    id="utt3", 
    speaker=speaker1, 
    text="Correct me if I'm wrong but are you a woman?", 
    conversation_id="1", 
    timestamp=time.time(), 
    reply_to=utt2.id,
    meta={"score": 16}
)
utt_list = [utt1, utt2, utt3]
new_corpus = Corpus(utterances=utt_list)

def get_presentation_convo():
    """
    Returns a sample conversation object for presentation purposes.
    This conversation is designed to illustrate the kind of interactions
    that can occur in the CMV corpus.
    """
    return new_corpus.get_conversation("1")