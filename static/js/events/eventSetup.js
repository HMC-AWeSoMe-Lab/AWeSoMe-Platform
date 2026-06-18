import { domManager } from '../dom/domManager.js';
import { appState } from '../services/appState.js';
import { eventHandlers } from './eventHandlers.js';
import { handleCommentSubmit, handleCommentCancel } from '../events/commentActions.js';
import { dumpPayloadQueue } from '../services/payloadQueue.js';
import { pushToPayloadQueue } from '../services/payloadQueue.js';
import { getId } from '../services/apiService.js';
import { triggerInterventions } from '../main.js';
import { debounce } from '../services/utils.js';

/**
 * Sets up core event listeners for user interaction tracking.
 * Configures listeners for comment areas, text input, buttons, and global events.
 * 
 * @returns {void}
 */
export function setupEventListeners() {
    const elements = domManager.elements;
    

    // Comment area events
    Array.from(elements.commentArea).forEach((commentCard, i) => {
        commentCard.addEventListener("mouseup", eventHandlers.createHighlightHandler(commentCard, "HIGHLIGHT_COMMENT"));
        commentCard.addEventListener("mouseenter", eventHandlers.createMouseEnterHandler(commentCard, "MOUSE_ENTER"));
        commentCard.addEventListener("mouseleave", eventHandlers.createMouseLeaveHandler(commentCard, "MOUSE_LEAVE"));
    });





    // Global events
    window.addEventListener('keydown', eventHandlers.handleKeyDown);
    window.addEventListener("copy", eventHandlers.handleCopyPaste);
    window.addEventListener("paste", eventHandlers.handleCopyPaste);

    // Text area events
    elements.textArea.addEventListener("select", eventHandlers.handleTextAreaSelect);
    elements.textArea.addEventListener("input", eventHandlers.handleTextAreaInput);

    // Post button event
    elements.postButton.addEventListener('click', async (e) => {
        e.preventDefault();
        await handleCommentSubmit();
    });

    // Cancel button event
    elements.cancelButton.addEventListener('click', async () => {
        await handleCommentCancel();
    });

    // Before unload event
    window.addEventListener('beforeunload', async () => {
        if (appState.payloadQueue.length > 0) {
            await dumpPayloadQueue();
        }
    });
}

/**
 * Sets up intervention trigger event listeners for dynamic content.
 * Configures text input triggers and button click handlers for interventions.
 * 
 * @returns {void}
 */
export function setupInterventionTriggers() {
  // Note: onLoad interventions are triggered from main.js after app initialization
  
  // On comment input
  const commentBox = document.getElementById('content');
  if (commentBox) {
    commentBox.addEventListener('input', debounce(async function (e) {
      const draft = e.target.value;
      // Use existing interaction ID, don't increment it
      triggerInterventions(draft, appState.latestID, "onText");
    }, 300));
  }

    // 🔘 General onClick intervention buttons
  const clickableButtons = document.querySelectorAll("button:not(#submit-comment)");
  clickableButtons.forEach((btn) => {
    btn.addEventListener("click", async () => {
      // Use existing interaction ID, don't increment it
      const draft = document.getElementById('content')?.value || "";
      const buttonID = btn.id;

      triggerInterventions(draft, appState.latestID, "onClick", buttonID);
    });
  });

}

// adds general mouse enter/leave tracking for all elements with data-event-id
document.addEventListener("mouseenter", (e) => {
    const el = e.target;
    if (!(el instanceof Element)) return;

    const target = el.closest("[data-event-id]");
    if (target) {
        const id = target.getAttribute("data-event-id");
        const handler = eventHandlers.createMouseEnterHandler(target, `${id}_MOUSE_ENTER`);
        if (handler) handler(e);
        console.log("Mouse Enter:", target.id);
    }
}, true);

document.addEventListener("mouseleave", (e) => {
    const el = e.target;
    if (!(el instanceof Element)) return;

    const target = el.closest("[data-event-id]");
    if (target) {
        const id = target.getAttribute("data-event-id");
        const handler = eventHandlers.createMouseLeaveHandler(target, `${id}_MOUSE_LEAVE`);
        if (handler) handler(e);
        console.log("Mouse Leave:", target.id);
    }
}, true);


document.addEventListener("click", async (e) => {
  const el = e.target;
  if (!(el instanceof Element)) return;

  // Check if there's a text selection - if so, don't log as a click
  const selection = window.getSelection();
  const hasTextSelection = selection && selection.toString().trim().length > 0;
  
  if (hasTextSelection) {
    console.log("Skipping click logging due to text selection");
    return; // Let the text selection handler deal with this
  }

  const button = el.closest("button");
  if (button) {
    const buttonID = button.id || "unknown_button";
    const count = appState.incrementButtonClick(buttonID);

    appState.setLatestAction("BUTTON_CLICK", JSON.stringify({
      button_id: buttonID,
      click_count: count
    }));
    await pushToPayloadQueue();
    
    // Trigger interventions for dynamic buttons (like feedback buttons)
    if (buttonID.startsWith("feedback_button")) {
      const draft = document.getElementById('content')?.value || "";
      await triggerInterventions(draft, appState.latestID, "onClick", buttonID);
    }
  } else {
    // Optional: log generic element click
    const elementID = el.id || "unknown_element";
    appState.setLatestAction("ELEMENT_CLICK", elementID);
    await pushToPayloadQueue();
  }
  
}, true);  // Use capture so it works on all dynamic buttons