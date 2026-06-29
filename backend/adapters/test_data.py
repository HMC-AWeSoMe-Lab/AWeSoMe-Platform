from backend.convo_interface import ConvoInterface

DUMMY_CONVERSATION = [
    {
        "message_id": "m1",
        "text": "Has anyone tried using AI tools for studying neuroscience?",
        "speaker_id": "u1",
        "reply_to": None,
        "timestamp": 1
    },
    {
        "message_id": "m2",
        "text": "Yes, I use them to summarize papers. It helps a lot.",
        "speaker_id": "u2",
        "reply_to": "m1",
        "timestamp": 2
    },
    {
        "message_id": "m3",
        "text": "I tried but I feel like I stop thinking deeply when I rely on summaries.",
        "speaker_id": "u3",
        "reply_to": "m1",
        "timestamp": 3
    },
    {
        "message_id": "m4",
        "text": "That’s interesting. I think it depends on how you use it.",
        "speaker_id": "u2",
        "reply_to": "m3",
        "timestamp": 4
    },
    {
        "message_id": "m5",
        "text": "What tools do you all use? I’ve been trying ChatGPT mostly.",
        "speaker_id": "u4",
        "reply_to": "m2",
        "timestamp": 5
    },
    {
        "message_id": "m6",
        "text": "Same here, but I also use it to generate quiz questions for myself.",
        "speaker_id": "u2",
        "reply_to": "m5",
        "timestamp": 6
    },
    {
        "message_id": "m7",
        "text": "Do you think this is making education too dependent on AI?",
        "speaker_id": "u5",
        "reply_to": "m1",
        "timestamp": 7
    },
    {
        "message_id": "m8",
        "text": "I think it’s like calculators. It depends on whether we still learn fundamentals.",
        "speaker_id": "u3",
        "reply_to": "m7",
        "timestamp": 8
    },
    {
        "message_id": "m9",
        "text": "But calculators didn’t generate explanations or essays.",
        "speaker_id": "u5",
        "reply_to": "m8",
        "timestamp": 9
    },
    {
        "message_id": "m10",
        "text": "True, but maybe we should redesign assignments instead of banning tools.",
        "speaker_id": "u1",
        "reply_to": "m9",
        "timestamp": 10
    },
    {
        "message_id": "m11",
        "text": "I agree. AI is already part of the workflow in research labs.",
        "speaker_id": "u6",
        "reply_to": "m2",
        "timestamp": 11,
        "meta": {"stance": "pro-ai"}
    },
    {
        "message_id": "m12",
        "text": "We should also teach citation and verification skills.",
        "speaker_id": "u6",
        "reply_to": "m11",
        "timestamp": 12
    }
]
