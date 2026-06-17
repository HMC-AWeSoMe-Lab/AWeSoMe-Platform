from .utterance import Utterance


class Conversation:
    """
    Represents a conversation made up of utterances.

    Required fields:
        id         (str):   unique identifier for this conversation
        utterances (list):  list of Utterance objects in this conversation

    Optional fields:
        meta       (dict):  arbitrary metadata about the conversation
                            e.g. {"summary_meta": [...], "topic": "politics"}
    """

    def __init__(self, convo_id: str, utterances: list, meta: dict = None):
        """
        :param convo_id: unique identifier for this conversation
        :param utterances: list of Utterance objects
        :param meta: optional metadata dict
        """
        self.id = convo_id
        self._utterances = utterances
        self.meta = meta or {}

    def iter_utterances(self):
        """Iterate over all utterances in insertion order."""
        return iter(self._utterances)

    def get_chronological_utterance_list(self) -> list:
        """
        Return utterances sorted by timestamp (earliest first).
        Utterances with no timestamp are placed at the end.
        """
        return sorted(
            self._utterances,
            key=lambda u: u.timestamp if u.timestamp is not None else float('inf')
        )

    def get_utterance(self, utt_id: str) -> Utterance:
        """
        Look up a specific utterance by its id.
        Raises KeyError if not found.
        """
        for utt in self._utterances:
            if utt.id == utt_id:
                return utt
        raise KeyError(f"Utterance '{utt_id}' not found in conversation '{self.id}'")

    def get_root_utterance(self):
        """
        Return the root utterance of the conversation
        (the one with reply_to == None).
        Returns None if no root is found.
        """
        for utt in self._utterances:
            if utt.reply_to is None:
                return utt
        return None

    def add_meta(self, key: str, value) -> None:
        """Add or update a metadata field."""
        self.meta[key] = value

    def get_meta(self, key: str):
        """
        Retrieve a metadata field by key.
        Returns None if the key does not exist.
        """
        return self.meta.get(key)

    def __repr__(self):
        return f"Conversation(id={self.id!r}, utterances={len(self._utterances)})"