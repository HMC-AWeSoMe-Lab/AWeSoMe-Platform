import { appState } from '../services/appState.js';
import { domManager } from '../dom/domManager.js';
import { utils, debounce } from '../services/utils.js';

// Internal flag to cache result
let highlightFeatureEnabled = null;

// Check server-side setting - highlighting is now enabled via intervention system
async function checkHighlightingEnabled() {
    if (highlightFeatureEnabled !== null) return highlightFeatureEnabled;

    // Highlighting is enabled through the intervention system
    // We'll check this when we actually call the intervention
    highlightFeatureEnabled = true;
    console.log("[Highlight] Feature enabled via intervention system");
    return highlightFeatureEnabled;
}

// Fetch highlight ranges from server via intervention system
export async function getHighlights(text) {
    appState.setLatestAction("HIGHLIGHT_INTERVENTION", text);

    try {
        const response = await fetch('/interventions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                triggerEvent: "onText",
                latestID: appState.latestID,
                currentTimestamp: appState.latestTimestamp
            })
        });

        const interventions = await response.json();
        
        // Find the highlighting intervention in the response
        const highlightIntervention = interventions.find(intervention => 
            intervention.type === "highlighting"
        );
        
        if (highlightIntervention && highlightIntervention.enabled) {
            const ranges = highlightIntervention.highlight_indices || [];
            console.log("[Highlight] Received ranges:", ranges);
            return ranges;
        } else {
            console.log("[Highlight] No highlighting intervention found or disabled");
            return [];
        }
    } catch (error) {
        console.error("[Highlight] Error fetching highlights:", error);
        return [];
    }
}

// Escape HTML special chars and convert spaces/newlines
function escapeHTML(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/ /g, '&nbsp;')
        .replace(/\n/g, '<br>');
}

// Merge overlapping or adjacent ranges
function mergeRanges(ranges) {
    if (!ranges.length) return [];

    // Sort ranges by start index
    ranges.sort((a, b) => a[0] - b[0]);

    const merged = [ranges[0].slice()]; // clone first range

    for (let i = 1; i < ranges.length; i++) {
        const [lastStart, lastEnd] = merged[merged.length - 1];
        const [currStart, currEnd] = ranges[i];

        if (currStart <= lastEnd + 1) {
            // Overlapping or adjacent — merge
            merged[merged.length - 1][1] = Math.max(lastEnd, currEnd);
        } else {
            merged.push(ranges[i].slice());
        }
    }
    return merged;
}

// Apply highlights to textarea
export function applyHighlights(textarea, ranges) {
    if (!textarea || !ranges || ranges.length === 0) {
        console.log("[Highlight] No textarea or ranges to apply");
        return;
    }

    const text = textarea.value;
    console.log("[Highlight] Applying highlights to text length:", text.length, "with ranges:", ranges);

    // Remove existing highlights container if present
    const old = textarea.parentNode.querySelector('.highlights-container');
    if (old) {
        old.remove();
        console.log("[Highlight] Removed existing highlights");
    }

    // Create highlights container
    const container = document.createElement('div');
    container.className = 'highlights-container';

    const parent = textarea.parentNode;
    if (getComputedStyle(parent).position === 'static') {
        parent.style.position = 'relative';
    }

    const computedStyles = window.getComputedStyle(textarea);

    Object.assign(container.style, {
        position: 'absolute',
        top: textarea.offsetTop + 'px',
        left: textarea.offsetLeft + 'px',
        width: textarea.offsetWidth + 'px',
        height: textarea.offsetHeight + 'px',
        padding: computedStyles.padding,
        border: computedStyles.border,
        margin: computedStyles.margin,
        fontFamily: computedStyles.fontFamily,
        fontSize: computedStyles.fontSize,
        fontWeight: computedStyles.fontWeight,
        lineHeight: computedStyles.lineHeight,
        letterSpacing: computedStyles.letterSpacing,
        wordSpacing: computedStyles.wordSpacing,
        textAlign: computedStyles.textAlign,
        whiteSpace: computedStyles.whiteSpace,
        wordWrap: computedStyles.wordWrap,
        boxSizing: computedStyles.boxSizing,
        overflow: 'hidden',
        pointerEvents: 'none',
        background: 'transparent',
        color: 'transparent',
        zIndex: '1'
    });

    Object.assign(textarea.style, {
        background: 'transparent',
        position: 'relative',
        zIndex: '2'
    });

    // Add CSS for highlights if not present
    if (!document.querySelector('#highlight-styles')) {
        const style = document.createElement('style');
        style.id = 'highlight-styles';
        style.textContent = `
            .highlight {
                background-color: #ff4d4f !important;  /* red highlight */
                padding: 1px 2px;
                border-radius: 2px;
                color: #000 !important;
            }
            .highlights-container {
                pointer-events: none;
                user-select: none;
            }
        `;
        document.head.appendChild(style);
    }

    // Merge and build highlighted HTML
    const mergedRanges = mergeRanges(ranges);

    let highlighted = '';
    let pos = 0;

    for (const [start, end] of mergedRanges) {
        if (pos < start) {
            highlighted += escapeHTML(text.slice(pos, start));
        }
        // highlight range is inclusive, so +1 on end index
        highlighted += `<span class="highlight">${escapeHTML(text.slice(start, end + 1))}</span>`;
        pos = end + 1;
    }

    if (pos < text.length) {
        highlighted += escapeHTML(text.slice(pos));
    }

    container.innerHTML = highlighted;
    parent.insertBefore(container, textarea);

    console.log("[Highlight] Applied highlights container");
    return container;
}

// Debounced update function
export const updateHighlights = debounce(async () => {
    console.log("[Highlight] Update highlights called");

    const enabled = await checkHighlightingEnabled();
    console.log("[Highlight] Enabled:", enabled, "Mode:", appState.mode);

    if (appState.mode !== 1 || !enabled) {
        console.log("[Highlight] Skipping - mode or feature disabled");
        return;
    }

    const textArea = domManager.get('textArea');
    if (!textArea) {
        console.warn("[Highlight] TextArea not found");
        return;
    }

    const text = textArea.value;
    if (!text?.trim()) {
        console.log("[Highlight] No text to highlight");
        removeHighlights();
        return;
    }

    try {
        console.log("[Highlight] Getting highlights for text:", text.substring(0, 50) + "...");
        const ranges = await getHighlights(text);
        console.log("[Highlight] Received ranges:", ranges);

        if (ranges.length > 0) {
            applyHighlights(textArea, ranges);
        } else {
            console.log("[Highlight] No ranges returned");
            removeHighlights();
        }
    } catch (error) {
        console.error("[Highlight] Error updating highlights:", error);
    }
}, 300);

// Remove existing highlights
export function removeHighlights() {
    const textArea = domManager.get('textArea');
    if (!textArea) return;

    const highlightsContainer = textArea.parentNode?.querySelector('.highlights-container');
    if (highlightsContainer) {
        highlightsContainer.remove();
        console.log("[Highlight] Removed highlights");
    }

    // Reset textarea background
    textArea.style.background = '';
}

// Sync scroll positions
export function syncScroll() {
    const textArea = domManager.get('textArea');
    if (!textArea) return;

    const highlightsContainer = textArea.parentNode?.querySelector('.highlights-container');
    if (highlightsContainer) {
        highlightsContainer.scrollTop = textArea.scrollTop;
        highlightsContainer.scrollLeft = textArea.scrollLeft;
    }
}

// Setup event listeners
export async function initializeHighlighting() {
    console.log("[Highlight] Initializing highlighting...");

    const enabled = await checkHighlightingEnabled();
    console.log("[Highlight] Feature enabled:", enabled, "Mode:", appState.mode);

    if (appState.mode !== 1 || !enabled) {
        console.log("[Highlight] Skipping init: mode or feature off.");
        return;
    }

    const waitForTextArea = () => {
        return new Promise((resolve) => {
            const checkTextArea = () => {
                const textArea = domManager.get('textArea');
                if (textArea) {
                    resolve(textArea);
                } else {
                    setTimeout(checkTextArea, 100);
                }
            };
            checkTextArea();
        });
    };

    const textArea = await waitForTextArea();
    console.log("[Highlight] TextArea found, setting up listeners");

    textArea.removeEventListener('input', updateHighlights);
    textArea.removeEventListener('scroll', syncScroll);

    textArea.addEventListener('input', updateHighlights);
    textArea.addEventListener('scroll', syncScroll);

    const handleResize = () => {
        const highlightsContainer = textArea.parentNode?.querySelector('.highlights-container');
        if (highlightsContainer) {
            Object.assign(highlightsContainer.style, {
                top: textArea.offsetTop + 'px',
                left: textArea.offsetLeft + 'px',
                width: textArea.offsetWidth + 'px',
                height: textArea.offsetHeight + 'px'
            });
        }
    };

    window.removeEventListener('resize', handleResize);
    window.addEventListener('resize', handleResize);

    console.log("[Highlight] Initialization complete");
}

// Manually trigger highlighting
export async function triggerHighlighting() {
    console.log("[Highlight] Manually triggering highlighting");

    const enabled = await checkHighlightingEnabled();
    if (appState.mode !== 1 || !enabled) {
        console.log("[Highlight] Cannot trigger - mode or feature disabled");
        return;
    }

    const textArea = domManager.get('textArea');
    if (!textArea) {
        console.warn("[Highlight] TextArea not found for manual trigger");
        return;
    }

    const text = textArea.value;
    if (!text?.trim()) {
        console.log("[Highlight] No text to highlight");
        return;
    }

    try {
        console.log("[Highlight] Manually getting highlights for:", text.substring(0, 50) + "...");
        const ranges = await getHighlights(text);
        console.log("[Highlight] Manual trigger received ranges:", ranges);

        if (ranges.length > 0) {
            applyHighlights(textArea, ranges);
        } else {
            console.log("[Highlight] No highlights returned for manual trigger");
        }
    } catch (error) {
        console.error("[Highlight] Error in manual trigger:", error);
    }
}

// Render function for the intervention system
export function renderHighlighting(data) {
    console.log("[Highlight] Rendering highlighting intervention:", data);
    
    if (!data.enabled || !data.highlight_indices || data.highlight_indices.length === 0) {
        console.log("[Highlight] No highlights to render");
        removeHighlights();
        return;
    }
    
    const textArea = domManager.get('textArea');
    if (!textArea) {
        console.warn("[Highlight] TextArea not found for rendering");
        return;
    }
    
    // Apply the highlights using the provided ranges
    const highlightContainer = applyHighlights(textArea, data.highlight_indices);
    
    // Note: No text selection logging needed for highlights since they are visual indicators
    console.log("[Highlight] Applied highlights from intervention system");
}
