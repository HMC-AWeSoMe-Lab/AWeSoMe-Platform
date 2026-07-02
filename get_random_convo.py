#Test file to get a random conversation

from config import active_adapter
import random

convo_id = random.choice(active_adapter.get_conversation_ids())
print("ID:", convo_id)

convo = active_adapter.get_conversation(convo_id)
for utt in convo.iter_utterances():
    print(f"{utt.speaker_id}: {utt.text}\n")