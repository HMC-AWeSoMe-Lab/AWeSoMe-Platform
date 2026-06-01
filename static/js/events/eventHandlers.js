import { appState } from '../services/appState.js';
import { domManager } from '../dom/domManager.js';
import { pushToPayloadQueue } from '../services/payloadQueue.js';

/**
 * Collection of event handler utilities for user interaction tracking.
 * Provides standardized handlers for mouse events, text selection, and element interactions.
 */
export const eventHandlers = {
    /**
     * Creates a text selection handler for tracking highlighted text within an element.
     * 
     * @param {HTMLElement} element - The DOM element to track text selection on
     * @param {string} actionType - The action type identifier for logging purposes
     * @returns {Function} Event handler function for mouseup events
     */
    createHighlightHandler(element, actionType) {
        return async (event) => {
            // Use a slight delay to ensure selection is finalized
            setTimeout(async () => {
                const selection = window.getSelection();
                const selectedText = selection.toString().trim();
                if (selectedText.length > 0) {
                    // Enhanced payload for intervention elements
                    const payload = {
                        elementId: element.id || element.className || "unknown_element",
                        selectedText: selectedText,
                        textLength: selectedText.length,
                        interventionType: element.dataset?.interventionType || null,
                        interventionId: element.dataset?.interventionId || null,
                        timestamp: Date.now()
                    };
                    
                    // Log with enhanced information - this will override any previous action
                    const payloadString = JSON.stringify(payload);
                    appState.setLatestAction(actionType, payloadString);
                    console.log(`Text Selection [${actionType}]:`, payload);
                    await pushToPayloadQueue();
                }
            }, 50); // Longer delay to ensure this fires after the click handler
        };
    },

    /**
     * Creates a mouse enter handler for tracking when users hover over elements.
     * 
     * @param {HTMLElement} element - The DOM element to track mouse enter events on
     * @param {string} actionType - The action type identifier for logging purposes
     * @returns {Function} Event handler function for mouseenter events
     */
    createMouseEnterHandler(element, actionType) {
        return async () => {
            appState.setLatestAction(actionType, element.id);
            console.log("Mouse Enter:", element.id);
            console.log("Event timestamp:", appState.latestTimestamp);
            await pushToPayloadQueue();
        };
    },

/**
 * Creates a click handler for tracking button clicks and general element interactions.
 * Automatically determines if the clicked element is a button and logs appropriately.
 * 
 * @param {HTMLElement} container - The container element that will receive click events
 * @param {string} [fallbackActionType="ELEMENT_CLICK"] - Action type to use for non-button clicks
 * @returns {Function} Event handler function for click events
 */
createClickHandler(container, fallbackActionType = "ELEMENT_CLICK") {
    return async (event) => {
        const clickedEl = event.target;

        const isButton = clickedEl.tagName === "BUTTON";
        const actionType = isButton ? "BUTTON_CLICK" : fallbackActionType;

        const id =
            clickedEl.id ||
            container.id ||
            clickedEl.getAttribute("data-event-id") ||
            container.getAttribute("data-event-id") ||
            "UNKNOWN_ELEMENT";

        appState.setLatestAction(actionType, id);
        console.log(`${actionType}:`, id);

        await pushToPayloadQueue();
    };
},

    /**
     * Creates a mouse leave handler for tracking when users stop hovering over elements.
     * 
     * @param {HTMLElement} element - The DOM element to track mouse leave events on
     * @param {string} actionType - The action type identifier for logging purposes
     * @returns {Function} Event handler function for mouseleave events
     */
    createMouseLeaveHandler(element, actionType) {
        return async () => {
            appState.setLatestAction(actionType, element.id);
            console.log("Mouse Leave:", element.id);
            console.log("Event timestamp:", appState.latestTimestamp);
            await pushToPayloadQueue();
        };
    },

    /**
     * Handles keyboard key press events for user input tracking.
     * Logs individual keystrokes to the application state.
     * 
     * @param {KeyboardEvent} event - The keyboard event object containing key information
     * @returns {Promise<void>} Promise that resolves when keystroke is logged
     */
    async handleKeyDown(event) {
        appState.setLatestAction("KEYSTROKE", event.key);
        console.log("Latest key:", appState.latestPayload);
    },

    /**
     * Handles copy and paste events for tracking clipboard interactions.
     * Logs when users copy or paste content.
     * 
     * @param {ClipboardEvent} event - The clipboard event object (copy/paste)
     * @returns {Promise<void>} Promise that resolves when clipboard action is logged
     */
    async handleCopyPaste(event) {
        appState.setLatestAction("KEYSTROKE", event.type);
        console.log("Latest key:", appState.latestPayload);
    },

    /**
     * Handles text selection events within textarea elements.
     * Tracks when users select text within input areas using keyboard shortcuts.
     * 
     * @returns {Promise<void>} Promise that resolves when text selection is logged
     */
    async handleTextAreaSelect() {
        const selectedContent = document.activeElement;
        const selection = selectedContent.value.substring(
            selectedContent.selectionStart,
            selectedContent.selectionEnd
        );
        console.log("Selected content:", selection);
        appState.setLatestAction("HIGHLIGHT_TEXT_AREA", selection);
        await pushToPayloadQueue();
    },

    /**
     * Handles text input events in textarea elements.
     * Queues payload for processing unless the latest action was a button click.
     * 
     * @returns {Promise<void>} Promise that resolves when input event is processed
     */
    async handleTextAreaInput() {
        if (appState.latestAction !== "BUTTON_CLICK") {
            await pushToPayloadQueue();
        }
    },

    /**
     * Utility function to add text selection logging to any intervention element.
     * Attaches a mouseup event listener that tracks text highlighting within the element.
     * 
     * @param {HTMLElement} element - The DOM element to add text selection tracking to
     * @param {string} [actionTypePrefix="INTERVENTION"] - Prefix for the action type identifier
     * @returns {void}
     */
    addTextSelectionLogging(element, actionTypePrefix = "INTERVENTION") {
        if (!element) {
            console.warn("Cannot add text selection logging: element is null");
            return;
        }
        
        const actionType = `${actionTypePrefix}_TEXT_SELECT`;
        const handler = this.createHighlightHandler(element, actionType);
        element.addEventListener("mouseup", handler);
        
        console.log(`Added text selection logging to element:`, element.id || element.className, `with action type: ${actionType}`);
    }
};