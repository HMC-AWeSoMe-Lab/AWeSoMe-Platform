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