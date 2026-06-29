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

            def get_conversation_ids(self):
                return list(self._conversations.keys())

            def get_conversation(self, convo_id):
                return self._conversations[convo_id]

            def get_speaker(self, speaker_id):
                return self._speakers[speaker_id]

            def get_utterance(self, convo_id, utt_id):
                return self._conversations[convo_id].get_utterance(utt_id)

    Helper patterns (no longer abstract methods):
        - Iterate all conversations:
            for cid in adapter.get_conversation_ids():
                convo = adapter.get_conversation(cid)
        - Pick a random conversation:
            import random
            convo = adapter.get_conversation(random.choice(adapter.get_conversation_ids()))
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
    def get_conversation_ids(self) -> list:
        """Return a list of all conversation ids."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_conversation(self, convo_id: str) -> Conversation:
        """Return a Conversation by id."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_speaker(self, speaker_id: str) -> Speaker:
        """Return a Speaker by id."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_utterance(self, convo_id: str, utt_id: str) -> Utterance:
        """Return a specific Utterance from a specific Conversation."""
        raise NotImplementedError