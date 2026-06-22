from convokit import Corpus as ConvoKitCorpus, download as convokit_download
from backend.convo_interface import ConvoInterface, Conversation, Utterance, Speaker
import random


class ConvoKitAdapter(ConvoInterface):
    """
    Adapter that loads a ConvoKit corpus and converts it into the
    ConvoInterface format (Conversation, Utterance, Speaker).

    Works for both linear and tree-shaped (branching) corpora —
    the reply_to field on each Utterance encodes the thread structure
    when present, and is None for linear conversations.

    Accepts:
      - A ``"download:<corpus-name>"`` string — corpus is downloaded via
        convokit.download() and cached locally after the first run.
      - A local file path string — loaded directly from disk.
      - A pre-loaded ConvoKit Corpus object — used as-is.

    Examples (set in config.py only)::

        ConvoKitAdapter("download:reddit-corpus-small")
        ConvoKitAdapter("/path/to/local/corpus")
        ConvoKitAdapter(some_preloaded_corpus_object)
    """

    _DOWNLOAD_PREFIX = "download:"

    def __init__(self, corpus_source):
        """
        :param corpus_source: A ``"download:<corpus-name>"`` string, a local
                              corpus path string, or a pre-loaded ConvoKit Corpus.
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
                print(f"Loading corpus from '{self._corpus_source}'...")
                ck_corpus = ConvoKitCorpus(self._corpus_source)

        else:
            raise TypeError(
                f"corpus_source must be a 'download:<name>' string, a local path "
                f"string, or a ConvoKit Corpus object. Got: {type(self._corpus_source)}"
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
                    reply_to=ck_utt.reply_to,  # None for linear; non-None encodes tree structure
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