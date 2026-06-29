"""
test_dummy.py

Run this file directly to verify that DummyAdapter works correctly
before starting the website.

Usage (from project root):
    python -m backend.convo_interface.test_dummy
"""

from backend.adapters.dummy_adapter import DummyAdapter
from backend.adapters.test_data import DUMMY_CONVERSATION


def run_tests():
    print("=" * 50)
    print("Setting up DummyAdapter...")
    adapter = DummyAdapter(DUMMY_CONVERSATION)
    adapter.load()
    print("Load complete.\n")

    # --- Test 1: iter_conversations() ---
    print("--- Test 1: iter_conversations() ---")
    convos = list(adapter.iter_conversations())
    assert len(convos) == 1, f"Expected 1 conversation, got {len(convos)}"
    print(f"Found {len(convos)} conversation(s). OK\n")

    # --- Test 2: random_conversation() ---
    print("--- Test 2: random_conversation() ---")
    convo = adapter.random_conversation()
    print(f"Random conversation id: {convo.id}")
    assert convo.id == "dummy_convo", "Unexpected conversation id"
    print("OK\n")

    # --- Test 3: iter_utterances() ---
    print("--- Test 3: iter_utterances() ---")
    utts = list(convo.iter_utterances())
    assert len(utts) == len(DUMMY_CONVERSATION), (
        f"Expected {len(DUMMY_CONVERSATION)} utterances, got {len(utts)}"
    )
    print(f"Found {len(utts)} utterances. OK\n")

    # --- Test 4: get_chronological_utterance_list() ---
    print("--- Test 4: get_chronological_utterance_list() ---")
    ordered = convo.get_chronological_utterance_list()
    timestamps = [u.timestamp for u in ordered if u.timestamp is not None]
    assert timestamps == sorted(timestamps), "Utterances are not in chronological order"
    print("Utterances in correct chronological order. OK\n")

    # --- Test 5: root utterance check ---
    print("--- Test 5: root utterance (reply_to is None) ---")
    root = convo.get_root_utterance()
    assert root is not None, "No root utterance found"
    assert root.reply_to is None, "Root utterance should have reply_to == None"
    print(f"Root utterance: [{root.speaker_id}] {root.text[:50]!r}")
    print("OK\n")

    # --- Test 6: utterance fields ---
    print("--- Test 6: utterance fields ---")
    for utt in ordered[:3]:
        assert utt.id is not None,         "utt.id is None"
        assert utt.text is not None,        "utt.text is None"
        assert utt.speaker_id is not None,  "utt.speaker_id is None"
        print(f"  id={utt.id!r} speaker_id={utt.speaker_id!r} "
              f"reply_to={utt.reply_to!r} text={utt.text[:40]!r}")
    print("All utterance fields present. OK\n")

    # --- Test 7: get_speaker() ---
    print("--- Test 7: get_speaker() ---")
    speaker = adapter.get_speaker("u1")
    assert speaker.id == "u1", "Speaker id mismatch"
    print(f"Speaker: {speaker}")
    print("OK\n")

    # --- Test 8: get_utterance() ---
    print("--- Test 8: get_utterance() ---")
    utt = adapter.get_utterance("dummy_convo", "m1")
    assert utt.id == "m1", "Utterance id mismatch"
    print(f"get_utterance('dummy_convo', 'm1'): {utt}")
    print("OK\n")

    # --- Test 9: meta on utterance ---
    print("--- Test 9: utterance meta ---")
    utt_with_meta = adapter.get_utterance("dummy_convo", "m11")
    assert utt_with_meta.meta.get("stance") == "pro-ai", "Meta field 'stance' not found"
    print(f"m11 meta: {utt_with_meta.meta}")
    print("OK\n")

    # --- Test 10: full display simulation ---
    # Simulates what display_convo() does: root first, then rest
    print("--- Test 10: display simulation (root-first ordering) ---")
    all_utts = list(convo.iter_utterances())
    root_utts = [u for u in all_utts if u.reply_to is None]
    non_root_utts = [u for u in all_utts if u.reply_to is not None]
    sorted_utts = root_utts + non_root_utts
    assert sorted_utts[0].reply_to is None, "First utterance should be root"
    print(f"First utterance (root): [{sorted_utts[0].speaker_id}] "
          f"{sorted_utts[0].text[:50]!r}")
    print(f"Total utterances rendered: {len(sorted_utts)}")
    print("OK\n")

    print("=" * 50)
    print("All tests passed! DummyAdapter is ready.")
    print("You can now run app.py to see the conversation on the website.")
    print("=" * 50)


if __name__ == "__main__":
    run_tests()