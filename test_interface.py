# test_interface.py  (project root)
import sys
sys.path.insert(0, '.')

from backend.convo_interface.interface import ConvoInterface
from backend.convo_interface.conversation import Conversation
from backend.convo_interface.message import Message
from backend.convo_interface.user import User

class MockFetcher(ConvoInterface):
    """Minimal test fetcher — no file, no ConvoKit, just hardcoded data."""

    def load(self):
        u1 = User("alice")
        u2 = User("bob")

        self._conversations = [
            Conversation(
                convo_id="test_convo_1",
                messages=[
                    Message("m1", "I think we should lower taxes.", "alice", reply_to=None, timestamp=1700000000, score=5),
                    Message("m2", "I disagree, that increases the deficit.", "bob", reply_to="m1", timestamp=1700000060, score=3),
                    Message("m3", "But growth offsets that.", "alice", reply_to="m2", timestamp=1700000120, score=7),
                ]
            ),
            Conversation(
                convo_id="test_convo_2",
                messages=[
                    Message("m4", "Pineapple belongs on pizza.", "alice", reply_to=None, timestamp=1700001000, score=2),
                    Message("m5", "That is objectively wrong.", "bob", reply_to="m4", timestamp=1700001060, score=10),
                ]
            )
        ]
        return self

    def get_conversation_ids(self):
        return [c.id for c in self._conversations]

    def get_conversation(self, convo_id):
        return next(c for c in self._conversations if c.id == convo_id)


if __name__ == "__main__":
    import random
    fetcher = MockFetcher()
    fetcher.load()

    convo = fetcher.get_conversation(random.choice(fetcher.get_conversation_ids()))
    print("Conversation:", convo.id)
    for msg in convo.get_chronological_message_list():
        print(f"  [{msg.speaker_id}] {msg.text}")
    print("Root:", convo.get_root_message().text)