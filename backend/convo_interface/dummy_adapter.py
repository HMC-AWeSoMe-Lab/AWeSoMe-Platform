from backend.convo_interface import ConvoInterface, Conversation, Utterance, Speaker
from typing import List, Dict
import random


class DummyAdapter(ConvoInterface):
    """
    A simple in-memory adapter for testing without a real corpus.

    Accepts a list of dicts (see test_data.py for the expected format)
    and builds Conversation / Utterance / Speaker objects from them.
    All utterances are placed into a single conversation with id "dummy_convo".

    To use this adapter, update config.py:
        from backend.convo_interface.dummy_adapter import DummyAdapter
        from backend.convo_interface.test_data import DUMMY_CONVERSATION
        active_adapter = DummyAdapter(DUMMY_CONVERSATION)
        active_adapter.load()
    """

    def __init__(self, data: List[Dict]):
        """
        :param data: list of dicts, each representing one utterance.
                     Required keys: message_id, text, speaker_id
                     Optional keys: reply_to, timestamp, score, meta
        """
        super().__init__()
        self.raw_data = data

    def load(self):
        """Build Conversation, Utterance, and Speaker objects from raw_data."""
        self._conversations = {}
        self._speakers = {}

        utterances = []
        convo_id = "dummy_convo"

        for item in self.raw_data:
            utt = Utterance(
                utt_id=item["message_id"],
                text=item["text"],
                speaker_id=item["speaker_id"],
                reply_to=item.get("reply_to"),
                timestamp=item.get("timestamp"),
                score=item.get("score"),
                meta=item.get("meta", {})
            )
            utterances.append(utt)

            # register speaker if not seen yet
            sid = item["speaker_id"]
            if sid not in self._speakers:
                self._speakers[sid] = Speaker(sid)

        convo = Conversation(
            convo_id=convo_id,
            utterances=utterances
        )
        self._conversations[convo_id] = convo

        return self

    def random_conversation(self) -> Conversation:
        """Return a random conversation (only one exists in dummy data)."""
        return random.choice(list(self._conversations.values()))

    def get_conversation(self, convo_id: str) -> Conversation:
        return self._conversations[convo_id]

    def iter_conversations(self):
        return iter(self._conversations.values())

    def get_speaker(self, speaker_id: str) -> Speaker:
        return self._speakers[speaker_id]

    def get_utterance(self, convo_id: str, utt_id: str) -> Utterance:
        return self._conversations[convo_id].get_utterance(utt_id)