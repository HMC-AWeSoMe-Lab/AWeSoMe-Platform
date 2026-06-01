// frontend/js/interventions/feedbackBox.js
import { eventHandlers } from '../events/eventHandlers.js';
import { trackElementForRepositioning, untrackElement } from '../services/layoutManager.js';
import { triggerInterventions } from '../main.js';
import { appState } from '../services/appState.js';

// Track feedback box specific data
let activeFeedbackBoxes = [];

/**
 * Renders a feedback box intervention in the DOM.
 * Creates the feedback box element, adds event listeners, and positions it relative to a parent.
 * 
 * @param {Object} data - The feedback box data from the backend
 * @param {string} data.html - The HTML content for the feedback box
 * @param {string} [data.parentId] - ID of the parent element to position relative to
 * @param {string} [data.relation] - Positioning relation ('above', 'below', etc.)
 * @returns {void}
 */
export function renderFeedbackBox(data) {
    console.log(`[FeedbackBox] Rendering feedback box with data:`, data);
    
    // Create the box container and insert backend-provided HTML
    const wrapper = document.createElement("div");
    wrapper.innerHTML = data.html.trim();
    const box = wrapper.firstChild;

    if (!box) {
        console.error(`[FeedbackBox] Failed to create feedback box from HTML:`, data.html);
        return;
    }

    console.log(`[FeedbackBox] Created feedback box element:`, box);

    // Add text selection logging to this feedback box
    eventHandlers.addTextSelectionLogging(box, "FEEDBACKBOX");

    // Add click event listener for the feedback button to trigger interventions
    const feedbackButton = box.querySelector('button');
    if (feedbackButton) {
        feedbackButton.addEventListener('click', async () => {
            const draft = document.getElementById('content')?.value || "";
            const buttonID = feedbackButton.id;
            console.log(`Feedback button clicked: ${buttonID}`);
            
            // Trigger interventions for this button click
            await triggerInterventions(draft, appState.latestID, "onClick", buttonID);
        });
    }

    console.log(`[FeedbackBox] Processing relation: ${data.relation}, parentId: ${data.parentId}`);

    // Strategic DOM insertion based on relation
    if (data.relation === "above" && data.parentId === "reply-box") {
        console.log(`[FeedbackBox] Attempting to insert above reply-box`);
        
        // Insert the feedback box right after the last comment, before the reply-box
        const commentContainer = document.getElementById('reddit-convo');
        const replyBox = document.getElementById('reply-box');
        
        console.log(`[FeedbackBox] Found commentContainer:`, commentContainer);
        console.log(`[FeedbackBox] Found replyBox:`, replyBox);
        
        if (commentContainer && replyBox) {
            // Create a wrapper div to maintain spacing
            const feedbackWrapper = document.createElement('div');
            feedbackWrapper.style.margin = '10px 0';
            feedbackWrapper.style.textAlign = 'center';
            feedbackWrapper.style.display = 'flex';
            feedbackWrapper.style.justifyContent = 'center';
            feedbackWrapper.appendChild(box);
            
            // Insert right before the reply-box
            replyBox.parentNode.insertBefore(feedbackWrapper, replyBox);
            
            // Make the feedback box visible and ensure it's centered
            box.style.display = 'block';
            box.style.margin = '0 auto';
            
            console.log(`[FeedbackBox] Successfully inserted feedback box above reply-box`);
        } else {
            console.warn(`[FeedbackBox] Could not find comment container or reply-box, using body positioning`);
            // Fallback to body positioning
            document.body.appendChild(box);
            box.style.position = 'absolute';
            box.style.top = '100px';
            box.style.left = '50%';
            box.style.transform = 'translateX(-50%)';
            box.style.zIndex = '9999';
            box.style.display = 'block';
        }
    } else if (data.relation === "below" && data.parentId === "reply-box") {
        console.log(`[FeedbackBox] Attempting to insert below reply-box`);
        
        // Insert the feedback box right after the reply-box
        const replyBox = document.getElementById('reply-box');
        
        console.log(`[FeedbackBox] Found replyBox for below:`, replyBox);
        
        if (replyBox) {
            const feedbackWrapper = document.createElement('div');
            feedbackWrapper.style.margin = '10px 0';
            feedbackWrapper.style.textAlign = 'center';
            feedbackWrapper.style.display = 'flex';
            feedbackWrapper.style.justifyContent = 'center';
            feedbackWrapper.appendChild(box);
            
            // Insert right after the reply-box
            replyBox.parentNode.insertBefore(feedbackWrapper, replyBox.nextSibling);
            
            // Make the feedback box visible and ensure it's centered
            box.style.display = 'block';
            box.style.margin = '0 auto';
            
            console.log(`[FeedbackBox] Successfully inserted feedback box below reply-box`);
        } else {
            console.warn(`[FeedbackBox] Could not find reply-box, using body positioning`);
            // Fallback to body positioning
            document.body.appendChild(box);
            box.style.position = 'absolute';
            box.style.top = '200px';
            box.style.left = '50%';
            box.style.transform = 'translateX(-50%)';
            box.style.zIndex = '9999';
            box.style.display = 'block';
        }
    } else {
        console.log(`[FeedbackBox] Using absolute positioning for relation: ${data.relation}, parentId: ${data.parentId}`);
        
        // For other relations or parent IDs, fall back to absolute positioning
        document.body.appendChild(box);
        box.style.display = "block";
        box.style.position = "absolute";
        box.style.zIndex = "9999";
        
        // Use the old positioning logic for non-reply-box cases
        if (data.parentId && data.relation) {
            // Check if the parent element exists first
            const parentElement = document.getElementById(data.parentId);
            if (parentElement) {
                console.log(`[FeedbackBox] Parent element found: ${data.parentId}, positioning ${data.relation}`);
                // Use a longer timeout for elements that might not be fully rendered yet
                setTimeout(() => {
                    const recheckParent = document.getElementById(data.parentId);
                    if (recheckParent) {
                        positionRelativeToParent(box, data.parentId, data.relation);
                    } else {
                        console.warn(`[FeedbackBox] Parent element disappeared: ${data.parentId}, using fallback`);
                        box.style.top = '100px';
                        box.style.left = '50%';
                        box.style.transform = 'translateX(-50%)';
                    }
                }, 100);
            } else {
                console.warn(`[FeedbackBox] Parent element not found: ${data.parentId}, using fallback positioning`);
                // Fallback to center positioning
                box.style.top = '100px';
                box.style.left = '50%';
                box.style.transform = 'translateX(-50%)';
            }
        } else {
            console.warn(`[FeedbackBox] Missing parentId or relation, using fallback positioning`);
            // Fallback to center positioning
            box.style.top = '100px';
            box.style.left = '50%';
            box.style.transform = 'translateX(-50%)';
        }
    }

    // Track this feedback box (but we don't need layout manager for DOM-inserted ones)
    const feedbackBoxData = {
        element: box,
        parentId: data.parentId,
        relation: data.relation,
        originalData: data,
        isDOMInserted: data.parentId === "reply-box" // Track if this was inserted into DOM flow
    };
    
    activeFeedbackBoxes.push(feedbackBoxData);
    console.log(`[FeedbackBox] Added to tracking, total boxes: ${activeFeedbackBoxes.length}`);

    // Only register with layout manager if we're using absolute positioning
    if (!feedbackBoxData.isDOMInserted) {
        console.log(`[FeedbackBox] Registering with layout manager for absolute positioning`);
        const trackingId = trackElementForRepositioning(
            box,
            repositionFeedbackBox,
            { parentId: data.parentId, relation: data.relation }
        );
        feedbackBoxData.trackingId = trackingId;
    } else {
        console.log(`[FeedbackBox] Skipping layout manager registration for DOM-inserted element`);
    }
}

/**
 * Reposition function for feedback boxes used by the layout manager.
 * Called automatically when layout changes are detected.
 * 
 * @param {HTMLElement} element - The feedback box element to reposition
 * @param {Object} metadata - Positioning metadata including parentId and relation
 * @returns {void}
 */
function repositionFeedbackBox(element, metadata) {
    if (metadata.parentId && metadata.relation) {
        positionRelativeToParent(element, metadata.parentId, metadata.relation);
    }
}

/**
 * Repositions all active feedback boxes when the layout changes.
 * Cleans up stale references and ensures all feedback boxes maintain correct positioning.
 * 
 * @returns {void}
 */
export function repositionAllFeedbackBoxes() {
    console.log(`[FeedbackBox] Repositioning ${activeFeedbackBoxes.length} active feedback boxes`);
    
    // Reset any layout modifications first
    resetLayoutModifications();
    
    activeFeedbackBoxes.forEach((boxData, index) => {
        if (boxData.element && document.body.contains(boxData.element)) {
            if (boxData.parentId && boxData.relation) {
                console.log(`[FeedbackBox] Repositioning box ${index + 1} relative to ${boxData.parentId}`);
                positionRelativeToParent(boxData.element, boxData.parentId, boxData.relation);
            }
        } else {
            // Remove boxes that are no longer in the DOM
            console.log(`[FeedbackBox] Removing stale feedback box reference ${index + 1}`);
            activeFeedbackBoxes.splice(index, 1);
        }
    });
}

/**
 * Removes a specific feedback box from the DOM and cleans up tracking.
 * Unregisters the box from the layout manager and removes it from active tracking.
 * 
 * @param {HTMLElement} boxElement - The feedback box element to remove
 * @returns {void}
 */
export function removeFeedbackBox(boxElement) {
    const index = activeFeedbackBoxes.findIndex(boxData => boxData.element === boxElement);
    if (index !== -1) {
        const boxData = activeFeedbackBoxes[index];
        
        // Untrack from layout manager only if it was tracked
        if (boxData.trackingId) {
            untrackElement(boxData.trackingId);
        }
        
        activeFeedbackBoxes.splice(index, 1);
        console.log(`[FeedbackBox] Removed feedback box from tracking. ${activeFeedbackBoxes.length} remaining.`);
    }
    
    // Remove from DOM - handle both wrapper and direct insertion
    if (boxElement && document.body.contains(boxElement)) {
        const parent = boxElement.parentNode;
        
        // If the parent is a wrapper div we created, remove the wrapper
        if (parent && parent !== document.body && parent.children.length === 1) {
            parent.parentNode.removeChild(parent);
            console.log(`[FeedbackBox] Removed feedback box wrapper from DOM`);
        } else {
            // Otherwise just remove the element itself
            parent.removeChild(boxElement);
            console.log(`[FeedbackBox] Removed feedback box element from DOM`);
        }
    }
    
    // Reset layout modifications if no feedback boxes remain
    if (activeFeedbackBoxes.length === 0) {
        resetLayoutModifications();
    }
}

/**
 * Clears all active feedback boxes from the DOM and tracking.
 * Removes all feedback boxes and resets any layout modifications.
 * 
 * @returns {void}
 */
export function clearAllFeedbackBoxes() {
    console.log(`[FeedbackBox] Clearing all ${activeFeedbackBoxes.length} feedback boxes`);
    
    activeFeedbackBoxes.forEach(boxData => {
        // Untrack from layout manager only if it was tracked
        if (boxData.trackingId) {
            untrackElement(boxData.trackingId);
        }
        
        // Remove from DOM - handle both wrapper and direct insertion
        if (boxData.element && document.body.contains(boxData.element)) {
            const parent = boxData.element.parentNode;
            
            // If the parent is a wrapper div we created, remove the wrapper
            if (parent && parent !== document.body && parent.children.length === 1) {
                parent.parentNode.removeChild(parent);
            } else {
                // Otherwise just remove the element itself
                parent.removeChild(boxData.element);
            }
        }
    });
    
    activeFeedbackBoxes = [];
    resetLayoutModifications();
}

/**
 * Resets any layout modifications made for positioning feedback boxes.
 * Clears margins and other style changes that were added to accommodate feedback boxes.
 * 
 * @returns {void}
 */
function resetLayoutModifications() {
    const replyBox = document.getElementById('reply-box');
    if (replyBox) {
        replyBox.style.marginTop = '';
        console.log(`[FeedbackBox] Reset reply-box margin`);
    }
}

/**
 * Positions the feedback box relative to a parent element with collision detection.
 * Supports positioning: right, left, above, below, inside.
 * Auto-flips above/below positioning if collision is detected with other elements.
 * 
 * @param {HTMLElement} box - The feedback box element to position
 * @param {string} parentId - ID of the parent element to position relative to
 * @param {string} relation - Positioning relation ('above', 'below', 'left', 'right', 'inside')
 * @returns {void}
 */
function positionRelativeToParent(box, parentId, relation) {
    const parent = document.getElementById(parentId);
    if (!parent) {
        console.warn(`[FeedbackBox] Parent element not found: ${parentId}`);
        return;
    }

    // Check if parent is visible - if not, don't position
    if (parent.style.display === 'none' || !parent.offsetParent) {
        console.warn(`[FeedbackBox] Parent element ${parentId} is not visible, skipping positioning`);
        return;
    }

    // Get parent's position relative to the document
    const rect = parent.getBoundingClientRect();
    
    // Additional check - if rect is all zeros, parent is likely hidden
    if (rect.width === 0 && rect.height === 0 && rect.top === 0 && rect.left === 0) {
        console.warn(`[FeedbackBox] Parent element ${parentId} has zero dimensions, likely hidden`);
        return;
    }
    
    const margin = 10;
    
    console.log(`[FeedbackBox] Positioning ${relation} relative to ${parentId}`, {
        parentRect: rect,
        boxSize: { width: box.offsetWidth, height: box.offsetHeight },
        parentId: parentId,
        relation: relation
    });
    
    // Calculate absolute positions relative to the document
    const parentTop = rect.top + window.scrollY;
    const parentLeft = rect.left + window.scrollX;
    const parentRight = rect.right + window.scrollX;
    const parentBottom = rect.bottom + window.scrollY;

    let top, left;

    // Initial positioning
    switch (relation) {
        case "above":
            // Simple positioning above the parent element
            top = parentTop - box.offsetHeight - margin;
            left = parentLeft + (rect.width / 2) - (box.offsetWidth / 2);
            break;
        case "below":
            top = parentBottom + margin;
            left = parentLeft + (rect.width / 2) - (box.offsetWidth / 2);
            break;
        case "right":
            // Center vertically relative to parent
            top = parentTop + (rect.height / 2) - (box.offsetHeight / 2);
            left = parentRight + margin;
            // Ensure we don't go off screen to the right
            if (left + box.offsetWidth > window.innerWidth + window.scrollX) {
                left = parentLeft - box.offsetWidth - margin; // fallback to left
            }
            break;
        case "left":
            // Center vertically relative to parent
            top = parentTop + (rect.height / 2) - (box.offsetHeight / 2);
            left = parentLeft - box.offsetWidth - margin;
            // Ensure we don't go off screen to the left
            if (left < window.scrollX) {
                left = parentRight + margin; // fallback to right
            }
            break;
        case "inside":
            parent.appendChild(box);
            box.style.position = "relative";
            return;
        default:
            // Default to below if relation is unknown
            top = parentBottom + margin;
            left = parentLeft;
    }

    // Apply computed position with safety checks
    console.log(`[FeedbackBox] Final position for ${relation}:`, { top, left });
    
    // Ensure we have valid positioning values
    if (isNaN(top) || isNaN(left) || top < 0 || left < 0) {
        console.error(`[FeedbackBox] Invalid positioning values calculated: top=${top}, left=${left}`);
        return;
    }
    
    box.style.position = "absolute";
    box.style.top = `${top}px`;
    box.style.left = `${left}px`;
}
