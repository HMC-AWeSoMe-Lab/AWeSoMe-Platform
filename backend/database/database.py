import sqlite3
from backend.database.init_db import BASE_DIR
import os


"""
database.py handles all actions related to the databse that occur in app.py.
It provides a set of functions that can establish a connection to the database, insert new rows into 
the 'posts' table, retrieve the latest interaction ID from the 'latest_id' table, and update this ID.

Database schema assumptions: the table 'posts' and 'latest_id" have already been created, and
'latest_id" has been initialized with a single row containing the first interaction ID (0).
"""



def get_db_connection():
    """
    Establish a connection to the SQLite database.

    Initializes the row factory so columns can be accessed by name.
    See: https://stackoverflow.com/questions/44009452/what-is-the-purpose-of-the-row-factory-method-of-an-sqlite3-connection-object

    :return: A connection object to the SQLite database
    :rtype: sqlite3.Connection
    """
    conn = sqlite3.connect(os.path.join(BASE_DIR, 'database.db'))    # makes columns accessible by name, not just by index
    conn.row_factory = sqlite3.Row 
    return conn

def insert_posts(action_type, interaction_id, current_timestamp, current_text=None, payload=None):
    """
    Insert a new post into the 'posts' table in the database.

    :param action_type: The type of action (e.g., 'START', 'KEYSTROKE')
    :type action_type: str
    :param interaction_id: Unique ID for the interaction (starts on load of webpage)
    :type interaction_id: int
    :param current_timestamp: Date/Time of the action
    :type current_timestamp: datetime
    :param current_text: The text of the comment or post, defaults to None
    :type current_text: str or None, optional
    :param payload: Additional data associated with the post, defaults to None
    :type payload: str or None, optional
    """
    conn = get_db_connection()

    query = """INSERT INTO posts (action_type, interaction_id, payload, current_text, current_timestamp)
    VALUES (?, ?, ?, ?, ?)"""
    #not every action has a payload or current text, so entry will show up as "" in the db
    conn.execute(query, (action_type, interaction_id, payload, current_text, current_timestamp))
    conn.commit()
    conn.close()

def insert_trial_mode(interaction_id, mode):
    """
    Insert an interaction_id with its corresponding mode into the trial_mode table.

    :param interaction_id: Unique ID for the interaction (starts on load of webpage)
    :type interaction_id: int
    :param mode: The current mode of the session (treatment or control group)
    :type mode: str
    """
    conn = get_db_connection()

    query = """INSERT INTO trial_mode (interaction_id, mode) VALUES (?,?)"""
    conn.execute(query, (interaction_id, mode))

    conn.commit()
    conn.close()

def get_latest_interaction_id():
    """
    Retrieve the latest interaction ID from the 'latest_id' table in the database.

    Note: latest_id has only one row and one column.

    :return: The latest interaction ID
    :rtype: int
    :raises ValueError: If the 'latest_id' table is empty or not found
    """
    
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM latest_id").fetchone()
    conn.close()
    if row:
        return row[0]
    else:
        # raises error when app is being run
        raise ValueError("Buggy interaction id table")
        
    

def update_latest_interaction_id():
    """
    Update the 'latest_id' table with a new interaction ID, incremented by 1.

    :return: The new interaction ID
    :rtype: int
    """
    # increment old ID to get new ID
    latest_id = get_latest_interaction_id()
    new_id = latest_id + 1

    conn = get_db_connection()
    conn.execute(f'UPDATE latest_id SET interaction_id = {new_id} WHERE interaction_id = {new_id-1};')
    conn.commit()
    conn.close()

    return new_id



def insert_questionnaire_response(interaction_id, questionnaire, question_name, answer, current_timestamp):
    """
    Insert a single questionnaire answer into the 'questionnaire_responses' table.

    :param interaction_id: The interaction ID for this session
    :param questionnaire: Which questionnaire (e.g. 'beginning' or 'ending')
    :param question_name: The form field name (e.g. 'q1', 'eq1')
    :param answer: The selected answer value
    :param current_timestamp: When the response was submitted
    """
    conn = get_db_connection()
    query = """INSERT INTO questionnaire_responses
               (interaction_id, questionnaire, question_name, answer, current_timestamp)
               VALUES (?, ?, ?, ?, ?)"""
    conn.execute(query, (interaction_id, questionnaire, question_name, answer, current_timestamp))
    conn.commit()
    conn.close()

def dump_payloads_db(data):
    """
    Insert multiple posts from the payload queue dump into the 'posts' table.

    :param data: List of dictionaries from script.js, each containing 
                'actionType', 'id', 'payload', 'currentTimestamp', and 'currentText'
    :type data: list[dict]
    """
    conn = get_db_connection()

    insert_query = "INSERT INTO posts (action_type, interaction_id, payload, current_text, current_timestamp) VALUES (?, ?, ?, ?, ?)"
    # prepares the data for insertion all at once
    rows_to_insert = [(item['actionType'], item['id'], item['payload'], item['currentText'], item['currentTimestamp']) for item in data]

    conn.executemany(insert_query, rows_to_insert)
    conn.commit()
    conn.close()