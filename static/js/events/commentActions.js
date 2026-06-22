import { appState } from '../services/appState.js';
import { domManager } from '../dom/domManager.js';
import { utils } from '../services/utils.js';
import { pushToPayloadQueue, dumpPayloadQueue } from '../services/payloadQueue.js';
import { repositionAllElements } from '../services/layoutManager.js';
import { clearAllFeedbackBoxes } from '../interventions/feedbackBox.js';
import { triggerInterventions } from '../main.js';
import { removeHighlights } from '../interventions/highlighting.js';

const MIN_COMMENT_LENGTH = 10;

let activeReplyContainer = null;

function readingTimeDone() {
    return window.readingTimer?.done === true;
}

export async function toggleCommentBox(btn) {
    appState.updateTimestamp();

    const replyBox = document.getElementById('reply-box');

    if (btn) {
        const commentContainer = btn.closest('.comment__container');
        if (commentContainer) {
            activeReplyContainer = commentContainer;
            commentContainer.insertAdjacentElement('afterend', replyBox);
            const parentMargin = parseFloat(commentContainer.style.marginLeft) || 0;
            replyBox.style.marginLeft = `-${parentMargin}rem`;
            replyBox.style.width = `calc(100% + ${parentMargin}rem)`;
        }
    }

    replyBox.style.display = 'block';

    const textArea = document.getElementById('content');
    if (textArea) {
        setTimeout(() => textArea.focus(), 50);
        updateSubmitButton(textArea.value);
    }

    setTimeout(() => repositionAllElements(), 50);

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

export function initCommentLengthGuard() {
    const textArea = document.getElementById('content');
    if (!textArea) return;
    textArea.addEventListener('input', () => updateSubmitButton(textArea.value));
}

function updateSubmitButton(text) {
    const submitBtn     = document.getElementById('submit-comment');
    const minLengthMsg  = document.getElementById('min-length-msg');
    const readingMsg    = document.getElementById('reading-time-msg');
    if (!submitBtn) return;

    const tooShort    = text.trim().length < MIN_COMMENT_LENGTH;
    const timerActive = !readingTimeDone();
    const blocked     = tooShort || timerActive;

    submitBtn.disabled = blocked;

    // "too short" message: only when box is non-empty but short
    if (minLengthMsg)
        minLengthMsg.style.display = (tooShort && text.length > 0) ? 'block' : 'none';

    // "read more carefully" message: only when timer is still running
    if (readingMsg)
        readingMsg.style.display = timerActive ? 'block' : 'none';
}

export async function handleCommentSubmit() {
    const textArea = domManager.get('textArea');
    const commentContent = textArea.value;

    // Hard guards — belt and suspenders
    if (commentContent.trim().length < MIN_COMMENT_LENGTH) {
        updateSubmitButton(commentContent);
        return;
    }
    if (!readingTimeDone()) {
        updateSubmitButton(commentContent);
        return;
    }

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
            replyBox.insertAdjacentHTML('beforebegin', postData.html);

            textArea.value = "";
            removeHighlights();
            updateSubmitButton("");
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
    if (document.getElementById("popup")) return;

    const wrapper = document.createElement("div");
    wrapper.innerHTML = data.html;
    const popupElement = wrapper.firstElementChild;
    document.body.appendChild(popupElement);

    popupElement.querySelector("#popup-post-anyway-button")?.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();
        popupElement.remove();
        await postComment(commentContent);
    });

    popupElement.querySelector("#popup-edit-button")?.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();
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