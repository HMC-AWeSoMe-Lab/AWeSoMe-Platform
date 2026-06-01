import { appState } from './appState.js';
import { domManager } from '../dom/domManager.js';
import { utils } from './utils.js';

/**
 * Adds the current user action to the payload queue for batch processing.
 * Automatically triggers queue dump when threshold is reached.
 * 
 * @returns {Promise<void>} Promise that resolves when payload is queued and optionally dumped
 */
export async function pushToPayloadQueue() {
    // grabs current draft of user input from the textarea
    const newValue = domManager.get('textArea').value;

    // push all vals that represent columns of the database
    appState.payloadQueue.push({
        id: appState.latestID,
        actionType: appState.latestAction,
        payload: appState.latestPayload,
        currentText: newValue,
        currentTimestamp: appState.latestTimestamp
    });

    console.log(appState.payloadQueue);
    
    if (appState.queueThreshold === appState.payloadQueue.length) {
        await dumpPayloadQueue();
    }
}

/**
 * Sends the current payload queue to the backend and clears the queue.
 * Batches user actions for efficient database storage and network usage.
 * 
 * @returns {Promise<void>} Promise that resolves when payload queue is successfully dumped
 */
export async function dumpPayloadQueue() {
    if (appState.payloadQueue.length === 0) return;

    try {
        const result = await utils.fetchJSON('/dump_payload', {
            method: 'POST',
            body: JSON.stringify(appState.payloadQueue)
        });
        
        console.log("Result from /dump_payload:", result);
        // clear the payload queue after it has been dumped
        appState.payloadQueue = [];
    } catch (error) {
        console.error("Error in payload action:", error);
    }
}