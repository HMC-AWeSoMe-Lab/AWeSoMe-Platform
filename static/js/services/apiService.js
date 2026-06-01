import { appState } from './appState.js';
import { utils } from './utils.js';
import { pushToPayloadQueue } from './payloadQueue.js';

/**
 * Retrieves a unique interaction ID from the backend for session tracking.
 * Updates the application state with the new ID and timestamp.
 * 
 * @returns {Promise<string>} Promise that resolves to the interaction ID
 * @throws {Error} Throws error if ID retrieval fails
 */
export async function getId() {
    try {
        const data = await utils.fetchJSON('/get_id');
        console.log("Interaction ID:", data.interaction_id);
        appState.latestID = data.interaction_id;
        appState.updateTimestamp();
        return data.interaction_id;
    } catch (error) {
        console.error('Error in retrieving interaction id:', error);
        throw error;
    }
}

// TODOL=: Delete this obsolete function???
/**
 * Retrieves and alerts the current experimental mode from the backend.
 * Updates application state and logs treatment mode activation.
 * 
 * @returns {Promise<void>} Promise that resolves when mode is retrieved and set
 */
export async function alertMode() {
    try {
        const data = await utils.fetchJSON('/mode');
        console.log("Mode:", data.mode);
        appState.mode = data.mode;
        if (data.mode === 1) {
            console.log("Treatment mode activated:", data.mode);
        }
    } catch (error) {
        console.error('Error in retrieving mode:', error);
    }
}

/**
 * Associates the current interaction ID with experimental mode assignment.
 * Sends the interaction ID to backend for mode trial tracking and logs mode to payload queue.
 * 
 * @returns {Promise<void>} Promise that resolves when ID-mode association is complete
 */
export async function idToMode() {
    try {
        // the mode route in app.py grabs the latestID from appState
        // and assigns it to the mode_trial table
        const result = await utils.fetchJSON('/mode', {
            method: 'POST',
            body: JSON.stringify({ id: appState.latestID })
        });
        console.log("Sent id to be dumped into mode_trial", appState.latestID);
        appState.mode = result.mode;
        
        // pushes a new row onto POSTS table in db
        //// describing which group the user's session is in: treatment or control// Log mode assignment to payload queue for database tracking
        const modeText = result.mode === 1 ? 'treatment' : 'control';
        appState.latestAction = 'MODE';
        appState.latestPayload = modeText;
        appState.updateTimestamp();
        
        console.log(`Mode assigned: ${modeText} (${result.mode}) - logging to payload queue`);
        await pushToPayloadQueue();
        
    } catch (error) {
        console.error("Error in payload action:", error);
    }
}

/**
 * Initiates the user session by sending a START action to the backend.
 * Logs the beginning of user interaction for analytics tracking.
 * 
 * @returns {Promise<void>} Promise that resolves when session start is logged
 */
export async function start() {
    try {
        const result = await utils.fetchJSON('/start', {
            method: 'POST',
            body: JSON.stringify({
                id: appState.latestID,
                actionType: "START",
                currentTimestamp: appState.latestTimestamp
            })
        });
        console.log("Result from /start_action:", result);
    } catch (error) {
        console.error("Error in start action:", error);
    }
}

/**
 * Initializes reply button styling based on conversation depth from backend.
 * Fetches conversation depth and applies appropriate visual styling to reply button.
 * 
 * @returns {Promise<void>} Promise that resolves when reply style is initialized
 */
export async function initializeReplyStyle() {
    try {
        // depth grabs how many comments are in the conversation
        const data = await utils.fetchJSON('/reply_style');
        appState.depth = data.convoDepth;
        
        const btn = document.getElementById('reply-button');
        const textBox = document.getElementById('reply-box');
        const hoveringTextbox = document.getElementById('hovering-textbox');

        console.log("convo_depth after fetch:", appState.depth);
        
        // Apply width based on conversation depth
        [btn, textBox, hoveringTextbox].forEach(element => {
            if (element) {
                element.style.marginLeft = `${appState.depth}rem`;
                element.style.width = `calc(100% - ${appState.depth}rem)`;
            }
        });
    } catch (error) {
        console.error('Error in retrieving convo depth:', error);
    }
}