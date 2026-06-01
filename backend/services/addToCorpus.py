import csv
from convokit import (
    Utterance, Conversation, Speaker,
    download, Corpus, Forecaster, CRAFTModel
)
import time

def addToCorpus(corpus, CSVfile):
    with open(CSVfile, newline='', mode='r') as file2:
        reader2 = csv.reader(file2)
        for line in reader2:
            conv_id = line[0]
            if conv_id not in corpus.conversations:
                continue  # skip if conversation not in corpus

            convo = corpus.get_conversation(conv_id)

            # Ensure summary_meta exists
            tempMetaList = convo.meta.get("summary_meta", [])
            tempMetaList.append(line[1])
            convo.meta["summary_meta"] = tempMetaList


from convokit import Corpus

def filterCorpusByLength(corpus, max_len=8):
    def selector(convo):
        return len(list(convo.iter_utterances())) <= max_len

    return corpus.filter_conversations_by(selector)

def filterByPair(corpus):
    def selector(convo):
        return convo.meta["pair_id"] in corpus.get_conversation_ids()
    return corpus.filter_conversations_by(selector)

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

def getCRAFTScore(corpus, craft_forecaster):
    return craft_forecaster.transform(corpus, transform_selector)



def getToxicityScore(draft, convo, craft_forecaster ):

    utt_list = list(convo.iter_utterances())

    new_corpus = Corpus(utterances=utt_list)

    for convo in new_corpus.iter_conversations():
        convo.add_meta("has_removed_comment", True)  # ground truth

    transformed_corpus = craft_forecaster.transform(new_corpus, transform_selector)
    new_utt_list = list(transformed_corpus.iter_utterances())
    return new_utt_list[-1].meta['forecast_prob']


def filterByCraftScore(corpus, score_threshold=.70):
    '''
    TODO: KEEP THE NON-TOXIC PAIR!
    '''
    scored_corpus = getCRAFTScore(corpus, get_CRAFT_forecaster(get_CRAFT_model()))
    def selector(convo):
        return getToxicityScore(convo, get_CRAFT_forecaster(get_CRAFT_model())) > .70
    return scored_corpus.filter_conversations_by(selector)







if __name__ == "__main__":
    # === Step 1: Load base corpus ===
    corpus =  Corpus("/home/ssegal/.convokit/saved-corpora/SCD-corpus")
    print(len(list(corpus.iter_conversations())))
    # === Step 2: Add your custom metadata ===
    #     addToCorpus(corpus, "tweakedSCD.csv")
    # assuming `corpus` is the tweaked corpus you've already created/modified
    filterCorpus = filterCorpusByLength(corpus, max_len=3)
    print(len(list(filterCorpus.iter_conversations())))

    filterCorpusCRAFT = filterByCraftScore(filterCorpus)
    print(len(list(corpus.iter_conversations())))

    filterCorpus2 = filterByPair(filterCorpus)
    print(len(list(filterCorpus2.iter_conversations())))
    # dump filtered corpus
    # filterCorpus2.dump('SCD-corpus-filtered', base_path="/home/ssegal/.convokit/saved-corpora/")


    print("✅ Filtered corpus saved as 'SCD-corpus'.")
