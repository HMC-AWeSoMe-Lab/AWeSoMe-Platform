# Data Collection

Before the entire experiment, researchers must initialize the database by running the command: 

**python backend/database/init_db.py**

Initializing the database after the beginning of the experiment will lead to data loss. Data is automatically collected and stored as SQL tables during the experiment. There are four tables in total: the Post table, recording all types of actions the participants do on the chat page including the keystrokes, timestamps of the actions, real-time text in the reply box, and the interaction id; the Trial Mode table, recording the user ids and their assigned groups accordingly (treatment is 1, control is 0); the Questionnaire Response table, recording the responses of each user id to every question in the questionnaires; the Triggered Interventions table, recording the types of triggered interventions, the reasons for triggering, and the contents of the interventions. The researchers can easily export these tables by running export_data.py. 

All data will be stored locally on researchers' server by default. 

## Table 1: POST

## Table 2: Latest ID

## Table 3: Trial Mode

## Table 4: Questionnaire Response

## Table 5: Triggered Interventions
