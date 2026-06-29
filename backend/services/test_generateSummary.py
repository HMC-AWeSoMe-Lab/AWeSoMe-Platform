from backend.services.generateSummary import generate_summaries
from backend.convo_interface.interface import ConvoInterface
from backend.convo_interface.conversation import Conversation
from backend.convo_interface.message import Message
from backend.convo_interface.user import User

class FakeInterface(ConvoInterface):

    def __init__(self):
        super().__init__()

        # build fake data
        u1 = User("u1")
        u2 = User("u2")

        m1 = Message("m1", "Hello world", "u1", None, 1)
        m2 = Message("m2", "Hi there", "u2", "m1", 2)

        convo = Conversation("c1", [m1, m2])

        self._conversations = {"c1": convo}
        self._users = {"u1": u1, "u2": u2}

    def load(self):
        return self

    def get_conversation_ids(self):
        return list(self._conversations.keys())

    def get_conversation(self, convo_id):
        return self._conversations[convo_id]

    def get_user(self, user_id):
        return self._users[user_id]

    def get_message(self, convo_id, message_id):
        return self._conversations[convo_id].get_message(message_id)

def test_generate_summary():

    interface = FakeInterface()

    generate_summaries(interface)

    convo = interface.get_conversation("c1")

    print("\nRESULT META:")
    print(convo.meta)

    assert "conversation_summary" in convo.meta
    print("✅ TEST PASSED")


if __name__ == "__main__":
    test_generate_summary()