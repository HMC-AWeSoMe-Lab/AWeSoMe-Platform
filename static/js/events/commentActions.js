import { appState } from '../services/appState.js';
import { domManager } from '../dom/domManager.js';
import { utils } from '../services/utils.js';
import { pushToPayloadQueue, dumpPayloadQueue } from '../services/payloadQueue.js';
import { repositionAllElements } from '../services/layoutManager.js';
import { clearAllFeedbackBoxes } from '../interventions/feedbackBox.js';
import { triggerInterventions } from '../main.js';
import { removeHighlights } from '../interventions/highlighting.js';
import { renderPopup, resetPopupShownFlag } from '../interventions/popup.js';

// Driven by "toggleable_features.minCommentLength" in static/settings.json (0 = disabled)
const MIN_COMMENT_LENGTH = window.INTERVENTION_CONFIG?.minCommentLength ?? 10;

let activeReplyContainer = null;

function readingTimeDone() {
    return window.readingTimer?.done === true;
}

export async function toggleCommentBox(btn) {
    appState.updateTimestamp();

    const replyBox = document.getElementById('reply-box');
    const replyToAnywhere = window.INTERVENTION_CONFIG?.replyToAnywhere ?? true;

    if (replyToAnywhere) {
        // Original behaviour: move reply box under the clicked comment
        if (btn) {
            const commentContainer = btn.closest('.comment__container');
            if (commentContainer) {
                activeReplyContainer = commentContainer;
                let anchor = commentContainer;
                while (anchor.nextElementSibling && anchor.nextElementSibling !== replyBox && anchor.nextElementSibling.querySelector('.comment__title')?.textContent === 'SODA') {
                    anchor = anchor.nextElementSibling;
                }
                anchor.insertAdjacentElement('afterend', replyBox);
                const parentMargin = parseFloat(commentContainer.style.marginLeft) || 0;
                replyBox.style.marginLeft = `-${parentMargin}rem`;
                replyBox.style.width = `calc(100% + ${parentMargin}rem)`;
            }
        }
    } else {
        // replyToAnywhere=false: reply box sits below the last comment at full width
        // Hide the single reply button while the box is open
        const singleBtnContainer = document.getElementById('single-reply-btn-container');
        if (singleBtnContainer) singleBtnContainer.style.display = 'none';

        // Position reply-box right after the single-reply-btn-container (or at end of thread)
        const thread = document.getElementById('thread');
        if (singleBtnContainer) {
            singleBtnContainer.insertAdjacentElement('afterend', replyBox);
        } else {
            thread.appendChild(replyBox);
        }
        // Match the indentation of the last comment
        const allContainers = document.querySelectorAll('#reddit-convo .comment__container');
        const lastContainer = allContainers.length > 0 ? allContainers[allContainers.length - 1] : null;
        const lastMargin = lastContainer ? (parseFloat(lastContainer.style.marginLeft) || 0) : 0;
        replyBox.style.marginLeft = `${lastMargin}rem`;
        replyBox.style.width = `calc(100% - ${lastMargin}rem)`;

        activeReplyContainer = lastContainer;
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
    textArea.addEventListener('input', () => {
        updateSubmitButton(textArea.value);
        // Note: feedback boxes are intentionally left in place when the
        // textarea becomes blank — they should only go away on cancel/submit,
        // not just because the user temporarily cleared their draft.
    });
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

    if (minLengthMsg)
        minLengthMsg.style.display = (tooShort && text.length > 0) ? 'block' : 'none';

    if (readingMsg)
        readingMsg.style.display = timerActive ? 'block' : 'none';
}

export async function handleCommentSubmit() {
    const textArea = domManager.get('textArea');
    const commentContent = textArea.value;

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
            resetPopupShownFlag();
            const replyBox = document.getElementById('reply-box');

            let insertionAnchor = activeReplyContainer || replyBox;
            if (activeReplyContainer) {
                let sibling = activeReplyContainer.nextElementSibling;
                while (sibling && sibling !== replyBox) {
                    if (sibling.querySelector('.comment__title')?.textContent === 'SODA') {
                        insertionAnchor = sibling;
                    }
                    sibling = sibling.nextElementSibling;
                }
            }
            insertionAnchor.insertAdjacentHTML('afterend', postData.html);

            textArea.value = "";
            removeHighlights();
            updateSubmitButton("");
            replyBox.style.display = "none";
            if (hoverBox) hoverBox.style.display = "none";
            activeReplyContainer = null;

            // Restore single reply button if replyToAnywhere is off
            const singleBtnContainer = document.getElementById('single-reply-btn-container');
            if (singleBtnContainer) singleBtnContainer.style.display = '';

            const finishBtn = document.querySelector('a.back-btn[title="Please submit a comment first"]');
            if (finishBtn) {
                finishBtn.href = '/ending';
                finishBtn.removeAttribute('title');
                finishBtn.style.background = '';
                finishBtn.style.cursor = '';
            }

            clearAllFeedbackBoxes();
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

    resetPopupShownFlag();
    clearAllFeedbackBoxes();

    const replyBox = document.getElementById('reply-box');
    const hoverBox = domManager.get('hoverBox');
    const textArea = document.getElementById('content');

    // Clear the draft so it doesn't reappear if the user opens a different
    // reply box afterward — the textarea element is shared/reused across
    // reply boxes, so its value otherwise persists across cancels.
    if (textArea) {
        textArea.value = '';
        updateSubmitButton(textArea.value);
    }
    removeHighlights();

    replyBox.style.display = "none";
    if (hoverBox) hoverBox.style.display = "none";
    activeReplyContainer = null;

    // Restore single reply button if replyToAnywhere is off
    const singleBtnContainer = document.getElementById('single-reply-btn-container');
    if (singleBtnContainer) singleBtnContainer.style.display = '';
}