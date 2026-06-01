// static/js/services/selectionLogger.js
import { appState } from './appState.js';
import { pushToPayloadQueue } from './payloadQueue.js';

/**
 * General text selection logger for all interventions
 * Logs when users select text within intervention elements
 */

let isLoggingEnabled = true;
let lastLoggedSelection = null;

export function enableSelectionLogging() {
    isLoggingEnabled = true;
}

export function disableSelectionLogging() {
    isLoggingEnabled = false;
}

/**
 * Initialize selection logging for intervention elements
 */
export function initializeSelectionLogging() {
    document.addEventListener('mouseup', handleTextSelection);
    document.addEventListener('keyup', handleTextSelection); // For keyboard selections
    console.log('[SelectionLogger] Initialized text selection logging');
}

/**
 * Handle text selection events
 */
async function handleTextSelection(event) {
    if (!isLoggingEnabled) return;

    const selection = window.getSelection();
    const selectedText = selection.toString().trim();
    
    // Only log if there's actually selected text
    if (!selectedText || selectedText.length === 0) return;

    // Find the intervention element that contains this selection
    const interventionElement = findInterventionElement(selection);
    if (!interventionElement) return;

    // Avoid logging the same selection multiple times
    const selectionData = {
        text: selectedText,
        elementId: interventionElement.id,
        elementType: interventionElement.dataset.interventionType
    };

    if (lastLoggedSelection && 
        lastLoggedSelection.text === selectedText && 
        lastLoggedSelection.elementId === interventionElement.id) {
        return; // Same selection, don't log again
    }

    lastLoggedSelection = selectionData;

    // Log the selection
    await logTextSelection(selectionData, event);
}

/**
 * Find the intervention element that contains the current selection
 */
function findInterventionElement(selection) {
    if (selection.rangeCount === 0) return null;

    const range = selection.getRangeAt(0);
    let element = range.commonAncestorContainer;

    // If it's a text node, get its parent element
    if (element.nodeType === Node.TEXT_NODE) {
        element = element.parentElement;
    }

    // Walk up the DOM tree to find an intervention element
    while (element && element !== document.body) {
        if (element.dataset && element.dataset.interventionType) {
            return element;
        }
        // Also check for common intervention class names or IDs
        if (element.classList && (
            element.classList.contains('popup') ||
            element.classList.contains('feedback-box') ||
            element.classList.contains('intervention') ||
            element.id === 'popup' ||
            element.id.includes('feedback') ||
            element.id.includes('intervention')
        )) {
            return element;
        }
        element = element.parentElement;
    }

    return null;
}

/**
 * Log the text selection to the payload queue
 */
async function logTextSelection(selectionData, event) {
    const payload = {
        action: 'TEXT_SELECT',
        selectedText: selectionData.text,
        elementId: selectionData.elementId,
        elementType: selectionData.elementType || 'unknown',
        textLength: selectionData.text.length,
        timestamp: Date.now(),
        eventType: event.type, // 'mouseup' or 'keyup'
        // Additional context
        interventionContext: {
            elementId: selectionData.elementId,
            interventionType: selectionData.elementType
        }
    };

    console.log('[SelectionLogger] Logging text selection:', payload);

    // Set the latest action and push to payload queue
    appState.setLatestAction('TEXT_SELECT', JSON.stringify(payload));
    await pushToPayloadQueue();
}

/**
 * Add intervention-specific attributes to elements when they're created
 * This should be called by intervention renderers
 */
export function markInterventionElement(element, interventionType, interventionId = null) {
    if (!element) return;

    element.dataset.interventionType = interventionType;
    if (interventionId) {
        element.dataset.interventionId = interventionId;
    }

    // Also add a general class for easier identification
    element.classList.add('intervention-element');
    
    console.log(`[SelectionLogger] Marked element as intervention: ${interventionType}`, element);
}

/**
 * Remove selection logging from an element (when intervention is removed)
 */
export function unmarkInterventionElement(element) {
    if (!element) return;
    
    delete element.dataset.interventionType;
    delete element.dataset.interventionId;
    element.classList.remove('intervention-element');
}
