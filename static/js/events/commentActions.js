import { appState } from '../services/appState.js';
import { domManager } from '../dom/domManager.js';
import { utils } from '../services/utils.js';
import { pushToPayloadQueue, dumpPayloadQueue } from '../services/payloadQueue.js';
import { repositionAllElements } from '../services/layoutManager.js';
import { clearAllFeedbackBoxes } from '../interventions/feedbackBox.js';

/**
 * Toggles the comment box visibility and logs the reply button interaction.
 * Shows the reply textarea and hides the reply button, then triggers backend logging.
 * 
 * @returns {Promise<void>} Promise that resolves when comment box is toggled and logged
 */
export async function toggleCommentBox() {
    appState.updateTimestamp();

    const replyBox = document.getElementById('reply-box');
    const replyButton = document.getElementById('reply-button');

    replyBox.style.display = "block";
    replyButton.style.display = "none";

    // Reposition any dynamic UI elements after showing reply box
    setTimeout(() => {
        repositionAllElements();
    }, 50); // Small delay to ensure DOM is updated

    try {
        const result = await utils.fetchJSON('/reply_action', {
            method: 'POST',
            body: JSON.stringify({
                id: appState.latestID,
                actionType: 'BUTTON_CLICK',
                currentTimestamp: appState.latestTimestamp,
                buttonID: 'reply-button'
            })
        });
        console.log("Result from /reply_action:", result);
    } catch (error) {
        console.error("Error in reply action:", error);
    }
}

/**
 * Handles comment submission by posting the comment content to the backend.
 * Retrieves text from the comment textarea, submits it, and updates the conversation display.
 * 
 * @returns {Promise<void>} Promise that resolves when comment is submitted and UI is updated
 */
export async function handleCommentSubmit() {

    
    const textArea = domManager.get('textArea');
    const hoverBox = domManager.get('hoverBox');
    const commentContent = textArea.value;




    // Submit the comment first (this is the critical path)
    const commentPromise = utils.fetchJSON('/comment', {
        method: 'POST',
        body: JSON.stringify({
            comment: commentContent,
            id: appState.latestID,
            actionType: 'FINISH',
            currentTimestamp: appState.latestTimestamp
        })
    });

    try {
        // Handle comment post result first
        const postData = await commentPromise;
        
        if (postData.html) {
            document.getElementById("reddit-convo").insertAdjacentHTML("beforeend", postData.html);
            textArea.value = "";
            hoverBox.style.display = "none";
            
            // Reposition any dynamic UI elements after adding new comment
            setTimeout(() => {
                repositionAllElements();
            }, 50); // Small delay to ensure DOM is updated
        } else if (postData.error) {
            console.error("Server error:", postData.error);
        }

        // Note: Popup on submit functionality disabled (route removed)
        // If you need popup functionality, use the new intervention system in INTERVENTIONS list
        console.log("Submit popup functionality disabled - use intervention system instead");
    } catch (error) {
        console.error("Error posting comment:", error);
    }
}

/**
 * Handles comment cancellation by hiding the reply box and clearing any feedback.
 * Resets the UI to its initial state and clears all active feedback boxes.
 * 
 * @returns {Promise<void>} Promise that resolves when comment is canceled and UI is reset
 */
export async function handleCommentCancel() {
    appState.setLatestAction("BUTTON_CLICK", "cancel-button");
    await pushToPayloadQueue();

    // Clear feedback boxes BEFORE hiding elements to prevent positioning issues
    clearAllFeedbackBoxes();

    const replyBox = document.getElementById('reply-box');
    const replyButton = document.getElementById('reply-button');
    const hoverBox = domManager.get('hoverBox');
    
    replyBox.style.display = "none";
    replyButton.style.display = "block";
    hoverBox.style.display = "none";
}