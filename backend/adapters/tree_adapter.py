from convokit import Corpus as ConvoKitCorpus, download as convokit_download
from backend.convo_interface import ConvoInterface, Conversation, Utterance, Speaker
import random


class TreeAdapter(ConvoInterface):
    """
    Adapter for tree-shaped (branching) ConvoKit corpora such as reddit-corpus-small.

    Each utterance's reply_to field is preserved, so the full branching
    thread structure is available for rendering.

    Accepts either:
      - A ConvoKit dataset name (str) prefixed with "download:" — downloaded
        automatically via convokit.download() and cached locally after first run
      - A pre-loaded ConvoKit Corpus object — used as-is

    Examples (set in config.py, nowhere else):

        TreeAdapter("download:reddit-corpus-small")

        from convokit import Corpus, download
        TreeAdapter(Corpus(filename=download("reddit-corpus-small")))
    """

    _DOWNLOAD_PREFIX = "download:"

    def __init__(self, corpus_source):
        """
        :param corpus_source: Either a "download:<corpus-name>" string
                              or a pre-loaded ConvoKit Corpus object.
        """
        super().__init__()
        self._corpus_source = corpus_source

    def load(self):
        """Resolve corpus_source, load the corpus, and convert to internal types."""

        if isinstance(self._corpus_source, ConvoKitCorpus):
            ck_corpus = self._corpus_source
            print("Using pre-loaded ConvoKit corpus.")

        elif isinstance(self._corpus_source, str):
            if self._corpus_source.startswith(self._DOWNLOAD_PREFIX):
                corpus_name = self._corpus_source[len(self._DOWNLOAD_PREFIX):]
                print(f"Downloading ConvoKit corpus '{corpus_name}'...")
                ck_corpus = ConvoKitCorpus(filename=convokit_download(corpus_name))
            else:
                raise ValueError(
                    f"TreeAdapter expects a 'download:<corpus-name>' string for "
                    f"automatic download. For local paths, use ConvoKitAdapter instead."
                )

        else:
            raise TypeError(
                f"corpus_source must be a 'download:<name>' string or a ConvoKit "
                f"Corpus object. Got: {type(self._corpus_source)}"
            )

        self._speakers = {}
        self._conversations = {}

        for ck_speaker in ck_corpus.iter_speakers():
            self._speakers[ck_speaker.id] = Speaker(
                speaker_id=ck_speaker.id,
                meta=dict(ck_speaker.meta)
            )

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
                    reply_to=ck_utt.reply_to,   # key field — encodes the tree structure
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