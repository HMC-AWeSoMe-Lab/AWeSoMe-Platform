// frontend/js/interventions/feedbackBox.js
import { eventHandlers } from '../events/eventHandlers.js';
import { trackElementForRepositioning, untrackElement } from '../services/layoutManager.js';
import { triggerInterventions } from '../main.js';
import { appState } from '../services/appState.js';

// Track feedback box specific data
let activeFeedbackBoxes = [];

/**
 * Refreshes an already-rendered feedback box's content in place (text may
 * have changed since the box was first shown, e.g. the user kept typing),
 * and re-attaches the "See more" click handler so it keeps working after
 * the content is swapped out — otherwise the box would freeze after its
 * first render and clicking the button would silently do nothing new.
 *
 * @param {HTMLElement} existingBox - The feedback box element already in the DOM
 * @param {Object} data - The latest feedback box data from the backend
 */
function updateFeedbackBoxContent(existingBox, data) {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = data.html.trim();
    const freshBox = wrapper.firstChild;

    if (!freshBox) {
        console.error(`[FeedbackBox] Failed to parse refreshed feedback box HTML:`, data.html);
        return;
    }

    // Swap in the fresh inner content but keep the existing DOM node/id so
    // any external references (positioning, tracking) stay valid.
    existingBox.innerHTML = freshBox.innerHTML;

    // Preserve the visibility/display state the box already had.
    existingBox.style.display = existingBox.style.display || 'block';

    // Re-add text selection logging on the refreshed content.
    eventHandlers.addTextSelectionLogging(existingBox, "FEEDBACKBOX");

    // The button was just replaced via innerHTML, so its old listener is
    // gone — re-attach it so "See more" keeps working every time.
    const feedbackButton = existingBox.querySelector('button');
    if (feedbackButton) {
        feedbackButton.addEventListener('click', async () => {
            const draft = document.getElementById('content')?.value || "";
            const buttonID = feedbackButton.id;
            console.log(`Feedback button clicked: ${buttonID}`);
            await triggerInterventions(draft, appState.latestID, "onClick", buttonID);
        });
    }
}

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

    // If a feedback box already exists, refresh its content (the underlying
    // text may have changed since the user is still typing) and reposition
    // it, rather than freezing it at whatever it first showed.
    const uniqueId = `feedback-box-${data.relation}`;
    const existing = document.getElementById(uniqueId);
    if (existing) {
        updateFeedbackBoxContent(existing, data);

        const replyBox = document.getElementById('reply-box');
        const wrapper = existing.parentNode;
        if (replyBox && wrapper) {
            replyBox.parentNode.insertBefore(wrapper, replyBox);
        }
        return;
    }

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
            
            box.style.display = 'block';
            box.style.margin = '0 auto';
            
            console.log(`[FeedbackBox] Successfully inserted feedback box below reply-box`);
        } else {
            console.warn(`[FeedbackBox] Could not find reply-box, using body positioning`);
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
        
        document.body.appendChild(box);
        box.style.display = "block";
        box.style.position = "absolute";
        box.style.zIndex = "9999";
        
        if (data.parentId && data.relation) {
            const parentElement = document.getElementById(data.parentId);
            if (parentElement) {
                console.log(`[FeedbackBox] Parent element found: ${data.parentId}, positioning ${data.relation}`);
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
                box.style.top = '100px';
                box.style.left = '50%';
                box.style.transform = 'translateX(-50%)';
            }
        } else {
            console.warn(`[FeedbackBox] Missing parentId or relation, using fallback positioning`);
            box.style.top = '100px';
            box.style.left = '50%';
            box.style.transform = 'translateX(-50%)';
        }
    }

    // Track this feedback box
    const feedbackBoxData = {
        element: box,
        parentId: data.parentId,
        relation: data.relation,
        originalData: data,
        isDOMInserted: data.parentId === "reply-box"
    };
    
    activeFeedbackBoxes.push(feedbackBoxData);
    console.log(`[FeedbackBox] Added to tracking, total boxes: ${activeFeedbackBoxes.length}`);

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
 */
function repositionFeedbackBox(element, metadata) {
    if (metadata.parentId && metadata.relation) {
        positionRelativeToParent(element, metadata.parentId, metadata.relation);
    }
}

/**
 * Repositions all active feedback boxes when the layout changes.
 */
export function repositionAllFeedbackBoxes() {
    console.log(`[FeedbackBox] Repositioning ${activeFeedbackBoxes.length} active feedback boxes`);
    
    resetLayoutModifications();
    
    activeFeedbackBoxes.forEach((boxData, index) => {
        if (boxData.element && document.body.contains(boxData.element)) {
            if (boxData.parentId && boxData.relation) {
                console.log(`[FeedbackBox] Repositioning box ${index + 1} relative to ${boxData.parentId}`);
                positionRelativeToParent(boxData.element, boxData.parentId, boxData.relation);
            }
        } else {
            console.log(`[FeedbackBox] Removing stale feedback box reference ${index + 1}`);
            activeFeedbackBoxes.splice(index, 1);
        }
    });
}

/**
 * Removes a specific feedback box from the DOM and cleans up tracking.
 */
export function removeFeedbackBox(boxElement) {
    const index = activeFeedbackBoxes.findIndex(boxData => boxData.element === boxElement);
    if (index !== -1) {
        const boxData = activeFeedbackBoxes[index];
        
        if (boxData.trackingId) {
            untrackElement(boxData.trackingId);
        }
        
        activeFeedbackBoxes.splice(index, 1);
        console.log(`[FeedbackBox] Removed feedback box from tracking. ${activeFeedbackBoxes.length} remaining.`);
    }
    
    if (boxElement && document.body.contains(boxElement)) {
        const parent = boxElement.parentNode;
        
        if (parent && parent !== document.body && parent.children.length === 1) {
            parent.parentNode.removeChild(parent);
            console.log(`[FeedbackBox] Removed feedback box wrapper from DOM`);
        } else {
            parent.removeChild(boxElement);
            console.log(`[FeedbackBox] Removed feedback box element from DOM`);
        }
    }
    
    if (activeFeedbackBoxes.length === 0) {
        resetLayoutModifications();
    }
}

/**
 * Clears all active feedback boxes from the DOM and tracking.
 */
export function clearAllFeedbackBoxes() {
    console.log(`[FeedbackBox] Clearing all ${activeFeedbackBoxes.length} feedback boxes`);
    
    activeFeedbackBoxes.forEach(boxData => {
        if (boxData.trackingId) {
            untrackElement(boxData.trackingId);
        }
        
        if (boxData.element && document.body.contains(boxData.element)) {
            const parent = boxData.element.parentNode;
            
            if (parent && parent !== document.body && parent.children.length === 1) {
                parent.parentNode.removeChild(parent);
            } else {
                parent.removeChild(boxData.element);
            }
        }
    });
    
    activeFeedbackBoxes = [];
    resetLayoutModifications();
}

/**
 * Resets any layout modifications made for positioning feedback boxes.
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
 */
function positionRelativeToParent(box, parentId, relation) {
    const parent = document.getElementById(parentId);
    if (!parent) {
        console.warn(`[FeedbackBox] Parent element not found: ${parentId}`);
        return;
    }

    if (parent.style.display === 'none' || !parent.offsetParent) {
        console.warn(`[FeedbackBox] Parent element ${parentId} is not visible, skipping positioning`);
        return;
    }

    const rect = parent.getBoundingClientRect();
    
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
    
    const parentTop = rect.top + window.scrollY;
    const parentLeft = rect.left + window.scrollX;
    const parentRight = rect.right + window.scrollX;
    const parentBottom = rect.bottom + window.scrollY;

    let top, left;

    switch (relation) {
        case "above":
            top = parentTop - box.offsetHeight - margin;
            left = parentLeft + (rect.width / 2) - (box.offsetWidth / 2);
            break;
        case "below":
            top = parentBottom + margin;
            left = parentLeft + (rect.width / 2) - (box.offsetWidth / 2);
            break;
        case "right":
            top = parentTop + (rect.height / 2) - (box.offsetHeight / 2);
            left = parentRight + margin;
            if (left + box.offsetWidth > window.innerWidth + window.scrollX) {
                left = parentLeft - box.offsetWidth - margin;
            }
            break;
        case "left":
            top = parentTop + (rect.height / 2) - (box.offsetHeight / 2);
            left = parentLeft - box.offsetWidth - margin;
            if (left < window.scrollX) {
                left = parentRight + margin;
            }
            break;
        case "inside":
            parent.appendChild(box);
            box.style.position = "relative";
            return;
        default:
            top = parentBottom + margin;
            left = parentLeft;
    }

    console.log(`[FeedbackBox] Final position for ${relation}:`, { top, left });
    
    if (isNaN(top) || isNaN(left) || top < 0 || left < 0) {
        console.error(`[FeedbackBox] Invalid positioning values calculated: top=${top}, left=${left}`);
        return;
    }
    
    box.style.position = "absolute";
    box.style.top = `${top}px`;
    box.style.left = `${left}px`;
}