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

    // Check for blocking interventions (e.g. trigger words) before posting
    const res = await fetch('/interventions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text: commentContent,
            latestID: appState.latestID,
            currentTimestamp: Date.now(),
            triggerEvent: "onClick",
            buttonID: "submit-comment"
        })
    });

    const interventions = await res.json();
    const blockingPopup = interventions.find(i => i.type === "popup" && i.blocking);

    if (blockingPopup) {
        // Show the popup and wait for the user's choice instead of posting now
        showBlockingPopup(blockingPopup, commentContent);
        return;
    }

    // No trigger word found — post immediately
    await postComment(commentContent);
}

async function postComment(commentContent) {
    const textArea = domManager.get('textArea');
    const hoverBox = domManager.get('hoverBox');

    try {
        const postData = await utils.fetchJSON('/comment', {
            method: 'POST',
            body: JSON.stringify({
                comment: commentContent,
                id: appState.latestID,
                actionType: 'FINISH',
                currentTimestamp: appState.latestTimestamp
            })
        });

        if (postData.html) {
            document.getElementById("reddit-convo").insertAdjacentHTML("beforeend", postData.html);
            textArea.value = "";
            hoverBox.style.display = "none";
            setTimeout(() => repositionAllElements(), 50);
        } else if (postData.error) {
            console.error("Server error:", postData.error);
        }
    } catch (error) {
        console.error("Error posting comment:", error);
    }
}

function showBlockingPopup(data, commentContent) {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = data.html;
    const popupElement = wrapper.firstElementChild;
    document.body.appendChild(popupElement);

    document.getElementById("popup-post-anyway-button")?.addEventListener("click", async () => {
        popupElement.remove();
        await postComment(commentContent);
    });

    document.getElementById("popup-edit-button")?.addEventListener("click", () => {
        popupElement.remove();
        // leave textarea as-is so the user can revise it
    });
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