from backend.convo_interface import ConvoInterface

# A tree-shaped debate between 4 people about the best dessert after dinner.
# Note the branching structure: m2, m3, and m4 all reply directly to the
# root (m1), rather than forming a single back-and-forth chain, and m6
# also branches off of m2 instead of continuing the m2 -> m5 line.
DEMO_CONVERSATION = [
    {
        "message_id": "m1",
        "text": "Okay, real talk: what's the best dessert to have after dinner?",
        "speaker_id": "u1",
        "reply_to": None,
        "timestamp": 1
    },
    {
        "message_id": "m2",
        "text": "Tiramisu, no contest. The espresso and mascarpone combo is basically perfect.",
        "speaker_id": "u2",
        "reply_to": "m1",
        "timestamp": 2
    },
    {
        "message_id": "m3",
        "text": "I have to disagree, warm chocolate lava cake beats tiramisu every single time.",
        "speaker_id": "u3",
        "reply_to": "m1",
        "timestamp": 3
    },
    {
        "message_id": "m4",
        "text": "Honestly you're both overcomplicating it, a simple fruit tart is the better way to end a meal.",
        "speaker_id": "u4",
        "reply_to": "m1",
        "timestamp": 4
    },
    {
        "message_id": "m5",
        "text": "A fruit tart after a heavy dinner feels like an afterthought, not a real dessert.",
        "speaker_id": "u2",
        "reply_to": "m4",
        "timestamp": 5
    },
    {
        "message_id": "m6",
        "text": "That's fair, but lava cake is way too rich if you already had a big meal.",
        "speaker_id": "u1",
        "reply_to": "m3",
        "timestamp": 6
    },
    {
        "message_id": "m7",
        "text": "I'd rather feel a little too full than eat something as forgettable as fruit.",
        "speaker_id": "u3",
        "reply_to": "m5",
        "timestamp": 7
    },
    {
        "message_id": "m8",
        "text": "See, this is exactly why tiramisu wins, it's rich enough to satisfy but not overwhelming like lava cake.",
        "speaker_id": "u2",
        "reply_to": "m6",
        "timestamp": 8
    },
    {
        "message_id": "m9",
        "text": "A fruit tart isn't forgettable, it's refreshing, which is exactly what you want after something heavy.",
        "speaker_id": "u4",
        "reply_to": "m7",
        "timestamp": 9
    }
]