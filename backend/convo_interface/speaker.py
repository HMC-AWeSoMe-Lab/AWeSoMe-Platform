class Speaker:
    """
    Represents a single participant in a conversation.

    Required fields:
        id (str): unique identifier for the speaker

    Optional fields:
        meta (dict): arbitrary metadata about the speaker
                     e.g. {"age": 25, "location": "NY"}
    """

    def __init__(self, speaker_id: str, meta: dict = None):
        """
        :param speaker_id: unique identifier for this speaker
        :param meta: optional metadata dict
        """
        self.id = speaker_id
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

    # --- makes Speaker usable as a dict key (needed by SCD_helpers.py) ---
    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, Speaker):
            return self.id == other.id
        return False

    def __repr__(self):
        return f"Speaker(id={self.id!r})"