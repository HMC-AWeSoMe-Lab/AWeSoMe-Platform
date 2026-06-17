from convokit import Corpus as ConvoKitCorpus
from backend.convo_interface import ConvoInterface, Conversation, Utterance, Speaker
import random


class ConvoKitAdapter(ConvoInterface):
    """
    Adapter that loads a ConvoKit corpus and converts it into
    the ConvoInterface format (Conversation, Utterance, Speaker).

    This is the default adapter for the SCD corpus.
    To use a different corpus, change the path in config.py.
    """

    def __init__(self, corpus_path: str):
        """
        :param corpus_path: path to the ConvoKit corpus directory
        """
        super().__init__()
        self.corpus_path = corpus_path

    def load(self):
        """Load and convert the ConvoKit corpus."""
        print(f"Loading corpus from {self.corpus_path}...")
        ck_corpus = ConvoKitCorpus(self.corpus_path)

        self._speakers = {}
        self._conversations = {}

        # Convert speakers
        for ck_speaker in ck_corpus.iter_speakers():
            self._speakers[ck_speaker.id] = Speaker(
                speaker_id=ck_speaker.id,
                meta=dict(ck_speaker.meta)
            )

        # Convert conversations and utterances
        for ck_convo in ck_corpus.iter_conversations():
            utterances = []
            for ck_utt in ck_convo.iter_utterances():
                sid = ck_utt.speaker.id
                if sid not in self._speakers:
                    self._speakers[sid] = Speaker(sid)

                utt = Utterance(
                    utt_id=ck_utt.id,
                    text=ck_utt.text,
                    speaker_id=sid,
                    reply_to=ck_utt.reply_to,
                    timestamp=ck_utt.timestamp,
                    score=ck_utt.meta.get("score"),
                    meta=dict(ck_utt.meta)
                )
                utterances.append(utt)

            self._conversations[ck_convo.id] = Conversation(
                convo_id=ck_convo.id,
                utterances=utterances,
                meta=dict(ck_convo.meta)
            )

        print(f"Loaded {len(self._conversations)} conversations.")
        return self

    def random_conversation(self) -> Conversation:
        return random.choice(list(self._conversations.values()))

    def get_conversation(self, convo_id: str) -> Conversation:
        return self._conversations[convo_id]

    def iter_conversations(self):
        return iter(self._conversations.values())

    def get_speaker(self, speaker_id: str) -> Speaker:
        return self._speakers[speaker_id]

    def get_utterance(self, convo_id: str, utt_id: str) -> Utterance:
        return self._conversations[convo_id].get_utterance(utt_id)