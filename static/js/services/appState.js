/**
 * Application state management class.
 * Maintains global state for user interactions, payload queuing, and timestamp tracking.
 */
class AppState {
    /**
     * Initialize the application state with default values.
     */
    constructor() {
        // Unique interaction ID for session tracking
        this.latestID = null;

        // Initialize empty payload queue, meant to hold database paylaods
        this.payloadQueue = [];

        // 3 is an arbitrary number, needs further testing to determine optimal value
        this.queueThreshold = 3;

        // Latest action of the user (e.g, 'BUTTON_CLICK")
        this.latestAction = null;

        // Latest payload associated with the latest action
        this.latestPayload = null;

        // Latest timestamp of the last action
        this.latestTimestamp = null;

        // Depth of the conversation (how many comments)
        this.depth = 0;

        // TODO: test if this is needed
        // this.submitClickCount = 0;

        // Mode: treatment (1) or control (0)
        // This is set by the backend and used to determine which interventions to apply
        this.mode = null;
        
        // Initialize button click counts for tracking
        this.buttonClickCounts = {};
    }

    /**
     * Updates the latest timestamp to the current ISO string.
     * 
     * @returns {void}
     */
    updateTimestamp() {
        this.latestTimestamp = new Date().toISOString();
    }

    /**
     * Sets the latest user action and payload, automatically updating the timestamp.
     * 
     * @param {string} action - The type of action performed by the user
     * @param {*} payload - The data associated with the action
     * @returns {void}
     */
    setLatestAction(action, payload) {
        this.latestAction = action;
        this.latestPayload = payload;
        this.updateTimestamp();
    }

    /**
     * Increments the click count for a specific button and returns the new count.
     * 
     * @param {string} buttonID - The ID of the button that was clicked
     * @returns {number} The new click count for this button
     */
    incrementButtonClick(buttonID) {
        if (!this.buttonClickCounts[buttonID]) {
            this.buttonClickCounts[buttonID] = 0;
        }
        this.buttonClickCounts[buttonID] += 1;
        return this.buttonClickCounts[buttonID];
    }
}


// Export singleton instance
export const appState = new AppState();