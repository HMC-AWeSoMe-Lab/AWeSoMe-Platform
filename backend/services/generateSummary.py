import sys
sys.path.append('/home/hrepp/AWeSoMe-Platform')

from backend.services.SCDGenerator import getTrajectorySummary
from backend.services.SCD_helpers import transcript
from backend.convo_interface.interface import ConvoInterface

def generate_summaries(interface: ConvoInterface):

    convos = list(interface.iter_conversations())
    total = len(convos)

    for i, convo in enumerate(convos):
        print(f"Processing {i+1}/{total}: {convo.id}")

        try:
            convo_text = transcript(convo)
            summary = getTrajectorySummary(convo_text)

            convo.add_meta("conversation_summary", summary)

            print("  ✅ Summary stored")

        except Exception as e:
            print(f"  ❌ Failed: {e}")

    print("\n✅ Done!")
if __name__ == "__main__":

    raise RuntimeError(
        "Do not run services directly. Provide a ConvoInterface instance from the application layer."
    )
