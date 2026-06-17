import abc
from .conversation import Conversation
from .utterance import Utterance
from .speaker import Speaker


class ConvoInterface(abc.ABC):
    """
    Abstract base class for all corpus adapters.

    To plug in a new corpus, create a subclass and implement
    all abstract methods below. Then update config.py to use
    your new adapter. No other files need to change.

    Minimal example:
        class MyAdapter(ConvoInterface):
            def load(self):
                # read your data, build Conversation/Utterance/Speaker objects
                self._conversations = {...}
                self._speakers = {...}
                return self

            def random_conversation(self):
                import random
                return random.choice(list(self._conversations.values()))

            def get_conversation(self, convo_id):
                return self._conversations[convo_id]

            def iter_conversations(self):
                return iter(self._conversations.values())

            def get_speaker(self, speaker_id):
                return self._speakers[speaker_id]

            def get_utterance(self, convo_id, utt_id):
                return self._conversations[convo_id].get_utterance(utt_id)
    """

    @abc.abstractmethod
    def load(self):
        """
        Load data from the source.
        Must be called once before any other method.
        Should populate self._conversations and self._speakers.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def random_conversation(self) -> Conversation:
        """Return a random Conversation."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_conversation(self, convo_id: str) -> Conversation:
        """Return a Conversation by id."""
        raise NotImplementedError

    @abc.abstractmethod
    def iter_conversations(self):
        """Iterate over all Conversations."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_speaker(self, speaker_id: str) -> Speaker:
        """Return a Speaker by id."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_utterance(self, convo_id: str, utt_id: str) -> Utterance:
        """Return a specific Utterance from a specific Conversation."""
        raise NotImplementedError