DROP TABLE IF EXISTS posts;
CREATE TABLE posts (
    action_type TEXT NOT NULL,
    interaction_id INTEGER,
    payload TEXT,
    current_text TEXT,
    current_timestamp DATETIME NOT NULL
);

DROP TABLE IF EXISTS latest_id;
CREATE TABLE latest_id (
    interaction_id INTEGER
);

DROP TABLE IF EXISTS trial_mode;
CREATE TABLE trial_mode (
    interaction_id INTEGER,
    mode TEXT
);

DROP TABLE IF EXISTS questionnaire_responses;
CREATE TABLE questionnaire_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interaction_id INTEGER,
    questionnaire TEXT NOT NULL,
    question_name TEXT NOT NULL,
    answer TEXT NOT NULL,
    current_timestamp DATETIME NOT NULL
);

-- Records every time an intervention actually fires (i.e. get_payload
-- returned a non-None result), so researchers can analyze what triggered,
-- why, and what was shown. This table is intentionally generic: it makes
-- no assumptions about which intervention types or trigger reasons exist,
-- so any current or future custom intervention a researcher adds is
-- captured the same way without needing a schema change.
DROP TABLE IF EXISTS triggered_interventions;
CREATE TABLE triggered_interventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interaction_id INTEGER,
    intervention_type TEXT NOT NULL,     -- e.g. 'popup', 'feedbackBox', 'highlighting', or any future custom type
    trigger_event TEXT,                  -- e.g. 'onClick', 'onText', 'onLoad'
    trigger_reason TEXT NOT NULL,        -- e.g. 'trigger word "hate" found in comment', 'comment tone flagged as emotional'
    content TEXT,                        -- the actual content shown to the participant (e.g. popup HTML/message)
    current_timestamp DATETIME NOT NULL
);