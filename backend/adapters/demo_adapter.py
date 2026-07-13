from backend.convo_interface import ConvoInterface, Conversation, Utterance, Speaker
from backend.adapters.demo_data import DEMO_CONVERSATIONS_META
from typing import Dict, List


class DemoAdapter(ConvoInterface):
    """
    An in-memory adapter that holds multiple named, distinct conversations.

    Each conversation is a list of utterance dicts keyed by conversation id.
    Conversations are never picked randomly — pick_conversation() always
    returns the first conversation in the dict (insertion order), so each
    conversation stays independently addressable via get_conversation(convo_id).

    Conversation-level metadata (e.g. a hardcoded trajectory_summary) is
    looked up from DEMO_CONVERSATIONS_META in demo_data.py by convo_id.

    Example usage in config.py:
        from backend.adapters.demo_adapter import DemoAdapter
        from backend.adapters.demo_data import DEMO_CONVERSATIONS
        active_adapter = DemoAdapter(DEMO_CONVERSATIONS)
        active_adapter.load()

    Expected format:
        {
            "convo_id_1": [ {utterance dict}, ... ],
            "convo_id_2": [ {utterance dict}, ... ],
        }

    Utterance dict keys:
        Required: message_id, text, speaker_id
        Optional: reply_to, timestamp, score, meta
    """

    def __init__(self, data: Dict[str, List[dict]]):
        super().__init__()
        self.raw_data = data

    def load(self):
        self._conversations = {}
        self._speakers = {}

        for convo_id, utterance_dicts in self.raw_data.items():
            utterances = []
            for item in utterance_dicts:
                sid = item["speaker_id"]
                if sid not in self._speakers:
                    self._speakers[sid] = Speaker(sid)

                utt = Utterance(
                    utt_id=item["message_id"],
                    text=item["text"],
                    speaker_id=sid,
                    reply_to=item.get("reply_to"),
                    timestamp=item.get("timestamp"),
                    score=item.get("score"),
                    meta=item.get("meta", {})
                )
                utterances.append(utt)

            self._conversations[convo_id] = Conversation(
                convo_id=convo_id,
                utterances=utterances,
                meta=DEMO_CONVERSATIONS_META.get(convo_id, {})
            )

        print(f"DemoAdapter loaded {len(self._conversations)} conversation(s).")
        return self

    def get_conversation_ids(self) -> list:
        return list(self._conversations.keys())

    def get_conversation(self, convo_id: str) -> Conversation:
        return self._conversations[convo_id]

    def pick_conversation(self) -> Conversation:
        """
        Deterministic — no randomness. Always returns the first conversation
        (by insertion order) so each conversation stays distinct and stable
        instead of being randomly swapped between page loads.
        """
        first_id = self.get_conversation_ids()[0]
        return self._conversations[first_id]

    def get_speaker(self, speaker_id: str) -> Speaker:
        return self._speakers[speaker_id]

    def get_utterance(self, convo_id: str, utt_id: str) -> Utterance:
        return self._conversations[convo_id].get_utterance(utt_id)