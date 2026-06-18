import { appState } from '../services/appState.js';
import { domManager } from '../dom/domManager.js';
import { utils } from '../services/utils.js';
import { pushToPayloadQueue, dumpPayloadQueue } from '../services/payloadQueue.js';
import { repositionAllElements } from '../services/layoutManager.js';
import { clearAllFeedbackBoxes } from '../interventions/feedbackBox.js';
import { triggerInterventions } from '../main.js';

let activeReplyContainer = null;

export async function toggleCommentBox(btn) {
    appState.updateTimestamp();

    const replyBox = document.getElementById('reply-box');

    if (btn) {
        const commentContainer = btn.closest('.comment__container');
        if (commentContainer) {
            activeReplyContainer = commentContainer;
            commentContainer.insertAdjacentElement('afterend', replyBox);
        }
    }

    replyBox.style.display = 'block';

    const textArea = document.getElementById('content');
    if (textArea) setTimeout(() => textArea.focus(), 50);

    setTimeout(() => repositionAllElements(), 50);

    // Fire the popup intervention for treatment group (backend gates on is_treatment())
    triggerInterventions("", appState.latestID, "onClick", "reply-btn");

    try {
        const result = await utils.fetchJSON('/reply_action', {
            method: 'POST',
            body: JSON.stringify({
                id: appState.latestID,
                actionType: 'BUTTON_CLICK',
                currentTimestamp: appState.latestTimestamp,
                buttonID: btn ? (btn.getAttribute('data-utt-id') || 'reply-btn') : 'reply-btn'
            })
        });
        console.log("Result from /reply_action:", result);
    } catch (error) {
        console.error("Error in reply action:", error);
    }
}

export async function handleCommentSubmit() {
    const textArea = domManager.get('textArea');
    const hoverBox = domManager.get('hoverBox');
    const commentContent = textArea.value;

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
        showBlockingPopup(blockingPopup, commentContent);
        return;
    }

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
            const replyBox = document.getElementById('reply-box');
            // Insert new comment directly above the reply-box so it appears
            // right under the comment that was replied to
            replyBox.insertAdjacentHTML('beforebegin', postData.html);

            textArea.value = "";
            replyBox.style.display = "none";
            if (hoverBox) hoverBox.style.display = "none";
            activeReplyContainer = null;
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

    document.getElementById("popup-post-anyway-button")?.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();
        popupElement.remove();
        await postComment(commentContent);
    });

    document.getElementById("popup-edit-button")?.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        popupElement.remove();
    });
}

export async function handleCommentCancel() {
    appState.setLatestAction("BUTTON_CLICK", "cancel-button");
    await pushToPayloadQueue();

    clearAllFeedbackBoxes();

    const replyBox = document.getElementById('reply-box');
    const hoverBox = domManager.get('hoverBox');

    replyBox.style.display = "none";
    if (hoverBox) hoverBox.style.display = "none";
    activeReplyContainer = null;
}