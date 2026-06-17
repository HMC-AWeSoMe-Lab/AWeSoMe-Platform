class Utterance:
    """
    Represents a single utterance (comment/message) in a conversation.

    Required fields:
        id         (str):  unique identifier for this utterance
        text       (str):  text content of the utterance
        speaker_id (str):  id of the Speaker who made this utterance

    Optional fields:
        reply_to   (str):  id of the utterance this replies to;
                           None if this is the root utterance
        timestamp  (int):  Unix timestamp of when the utterance was posted
        score      (int):  upvote/downvote score (e.g. from Reddit)
        meta       (dict): arbitrary additional metadata
    """

    def __init__(self,
                 utt_id: str,
                 text: str,
                 speaker_id: str,
                 reply_to: str = None,
                 timestamp: int = None,
                 score: int = None,
                 meta: dict = None):
        """
        :param utt_id: unique identifier for this utterance
        :param text: text content of the utterance
        :param speaker_id: id of the speaker who made this utterance
        :param reply_to: id of the parent utterance, or None if root
        :param timestamp: Unix timestamp (optional)
        :param score: upvote score (optional)
        :param meta: optional metadata dict
        """
        self.id = utt_id
        self.text = text
        self.speaker_id = speaker_id
        self.reply_to = reply_to
        self.timestamp = timestamp
        self.score = score
        self.meta = meta or {}

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
        return f"Utterance(id={self.id!r}, speaker_id={self.speaker_id!r})"