import sys
sys.path.append('/home/hrepp/AWeSoMe-Platform')

from backend.services.SCDGenerator import getTrajectorySummary
from backend.services.SCD_helpers import transcript
from backend.convo_interface.interface import ConvoInterface

CHECKPOINT_EVERY = 500

def generate_summaries(interface: ConvoInterface, overwrite=False):
    convo_ids = interface.get_conversation_ids()
    total = len(convo_ids)
    generated = 0

    for i, convo_id in enumerate(convo_ids):
        convo = interface.get_conversation(convo_id)
        existing = (convo.meta.get("trajectory_summary") or "").strip()
        if existing and not overwrite:
            print(f"[{i+1}/{total}] {convo.id} — skipping (already has summary)")
            continue

        print(f"[{i+1}/{total}] {convo.id} — generating ...", end=" ", flush=True)

        try:
            convo_text = transcript(convo)
            summary = getTrajectorySummary(convo_text)
            convo.meta["trajectory_summary"] = summary.strip()
            generated += 1
            print(f"✅ ({len(summary.split())} words)")

            if generated % CHECKPOINT_EVERY == 0:
                if hasattr(interface, "save"):
                    print(f"  💾 Checkpoint: saving after {generated} summaries...")
                    interface.save()

        except Exception as e:
            print(f"❌ Failed: {e}")

    if generated > 0 and hasattr(interface, "save"):
        print(f"💾 Saving {generated} summaries to disk...")
        interface.save()
    elif generated == 0:
        print("Nothing new to save.")

    print(f"\n✅ Done! Generated {generated} / {total} summaries.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true",
                        help="Re-generate summaries even if they already exist")
    args = parser.parse_args()

    from config import active_adapter
    generate_summaries(active_adapter, overwrite=args.overwrite)