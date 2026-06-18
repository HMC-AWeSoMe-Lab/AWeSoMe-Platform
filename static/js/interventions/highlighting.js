import { appState } from '../services/appState.js';
import { domManager } from '../dom/domManager.js';
import { utils, debounce } from '../services/utils.js';

let highlightFeatureEnabled = null;

async function checkHighlightingEnabled() {
    if (highlightFeatureEnabled !== null) return highlightFeatureEnabled;
    highlightFeatureEnabled = true;
    return highlightFeatureEnabled;
}

export async function getHighlights(text) {
    appState.setLatestAction("HIGHLIGHT_INTERVENTION", text);
    try {
        const response = await fetch('/interventions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                triggerEvent: "onText",
                latestID: appState.latestID,
                currentTimestamp: appState.latestTimestamp
            })
        });
        const interventions = await response.json();
        const highlightIntervention = interventions.find(i => i.type === "highlighting");
        if (highlightIntervention && highlightIntervention.enabled) {
            return highlightIntervention.highlight_indices || [];
        }
        return [];
    } catch (error) {
        console.error("[Highlight] Error fetching highlights:", error);
        return [];
    }
}

function escapeHTML(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/ /g, '&nbsp;')
        .replace(/\n/g, '<br>');
}

function mergeRanges(ranges) {
    if (!ranges.length) return [];
    ranges.sort((a, b) => a[0] - b[0]);
    const merged = [ranges[0].slice()];
    for (let i = 1; i < ranges.length; i++) {
        const [lastStart, lastEnd] = merged[merged.length - 1];
        const [currStart, currEnd] = ranges[i];
        if (currStart <= lastEnd + 1) {
            merged[merged.length - 1][1] = Math.max(lastEnd, currEnd);
        } else {
            merged.push(ranges[i].slice());
        }
    }
    return merged;
}

function ensureStyles() {
    if (document.querySelector('#highlight-styles')) return;
    const style = document.createElement('style');
    style.id = 'highlight-styles';
    style.textContent = `
        .highlights-container {
            pointer-events: none;
            user-select: none;
            overflow: hidden;
        }
        .highlights-container .trigger-word {
            color: transparent;
            border-bottom: 2px solid #e53935;
            border-radius: 0;
        }
        .highlights-container .trigger-word.hovered {
            background-color: rgba(229, 57, 53, 0.18);
        }
        .hw-tooltip {
            position: fixed;
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            padding: 6px 10px;
            pointer-events: none;
            z-index: 9999;
            white-space: nowrap;
        }
        .hw-tooltip .tt-label {
            font-size: 0.72rem;
            color: #888;
            display: block;
            margin-bottom: 2px;
        }
        .hw-tooltip .tt-body {
            font-size: 0.85rem;
            color: #111;
            display: block;
        }
    `;
    document.head.appendChild(style);
}

// Current highlight ranges kept in memory so mousemove can check them
let currentRanges = [];

// Shared tooltip
let tooltip = null;
function getTooltip() {
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.className = 'hw-tooltip';
        tooltip.innerHTML = `
            <span class="tt-label">Trigger Word</span>
            <span class="tt-body">Please consider avoiding this word</span>
        `;
        tooltip.style.display = 'none';
        document.body.appendChild(tooltip);
    }
    return tooltip;
}

function showTooltip(x, y) {
    const tt = getTooltip();
    tt.style.display = 'block';
    tt.style.left = x + 'px';
    tt.style.top  = (y + 4) + 'px';
}

function hideTooltip() {
    if (tooltip) tooltip.style.display = 'none';
}

// Returns the character index under the mouse inside a textarea,
// by using a hidden mirror div with the same styles.
function getCharIndexAtMouse(textarea, mouseX, mouseY) {
    // Build a temporary mirror div
    const mirror = document.createElement('div');
    mirror.style.cssText = `
        position: fixed;
        visibility: hidden;
        pointer-events: none;
        overflow: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
    `;

    const cs = window.getComputedStyle(textarea);
    const props = [
        'fontFamily','fontSize','fontWeight','lineHeight',
        'letterSpacing','wordSpacing','padding','border',
        'boxSizing','width'
    ];
    props.forEach(p => { mirror.style[p] = cs[p]; });

    // Place the mirror at the same position as the textarea
    const rect = textarea.getBoundingClientRect();
    mirror.style.left   = rect.left + 'px';
    mirror.style.top    = rect.top  + 'px';
    mirror.style.width  = rect.width + 'px';
    mirror.style.height = rect.height + 'px';

    document.body.appendChild(mirror);

    const text = textarea.value;
    let charIndex = -1;

    // Binary search: find the character whose span contains (mouseX, mouseY)
    // We wrap each character in a span and use range/caretPositionFromPoint if available,
    // otherwise fall back to iterating spans.

    // Fast path: use caretPositionFromPoint / caretRangeFromPoint
    // These work on the real document, not a mirror — but we can use them on the textarea directly.
    let node = null;
    let offset = -1;

    if (document.caretPositionFromPoint) {
        const pos = document.caretPositionFromPoint(mouseX, mouseY);
        if (pos) { node = pos.offsetNode; offset = pos.offset; }
    } else if (document.caretRangeFromPoint) {
        const range = document.caretRangeFromPoint(mouseX, mouseY);
        if (range) { node = range.startContainer; offset = range.startOffset; }
    }

    document.body.removeChild(mirror);

    // caretPositionFromPoint gives caret position in the document, not textarea char index.
    // We need the char index in textarea.value. We'll use the mirror approach with spans instead.

    // Rebuild mirror with per-character spans
    const mirror2 = document.createElement('div');
    mirror2.style.cssText = `
        position: fixed;
        visibility: hidden;
        pointer-events: none;
        overflow: hidden;
        white-space: pre-wrap;
        word-wrap: break-word;
    `;
    props.forEach(p => { mirror2.style[p] = cs[p]; });
    mirror2.style.left   = rect.left + 'px';
    mirror2.style.top    = rect.top  + 'px';
    mirror2.style.width  = rect.width + 'px';
    mirror2.style.height = rect.height + 'px';
    // Offset for scroll
    mirror2.style.marginTop = (-textarea.scrollTop) + 'px';

    // Only wrap characters that are in trigger ranges to keep DOM small
    const inRange = new Set();
    currentRanges.forEach(([s, e]) => {
        for (let i = s; i <= e; i++) inRange.add(i);
    });

    // Build HTML with spans only on trigger-range chars
    let html = '';
    for (let i = 0; i < text.length; i++) {
        const ch = text[i];
        const escaped = ch === ' ' ? '&nbsp;'
                      : ch === '\n' ? '<br>'
                      : ch.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
        if (inRange.has(i)) {
            html += `<span data-idx="${i}">${escaped}</span>`;
        } else {
            html += escaped;
        }
    }
    mirror2.innerHTML = html;
    document.body.appendChild(mirror2);

    // Find which span contains the mouse point
    const spans = mirror2.querySelectorAll('span[data-idx]');
    for (const span of spans) {
        const sr = span.getBoundingClientRect();
        if (mouseX >= sr.left && mouseX <= sr.right &&
            mouseY >= sr.top  && mouseY <= sr.bottom) {
            charIndex = parseInt(span.dataset.idx, 10);
            break;
        }
    }

    document.body.removeChild(mirror2);
    return charIndex;
}

// Find which trigger range (if any) a char index falls in
function getRangeForChar(charIndex) {
    if (charIndex < 0) return null;
    for (const [s, e] of currentRanges) {
        if (charIndex >= s && charIndex <= e) return [s, e];
    }
    return null;
}

// Track which range is currently hovered so we don't flicker on every mousemove
let hoveredRange = null;

function onTextareaMouseMove(e) {
    const textarea = e.currentTarget;
    const charIndex = getCharIndexAtMouse(textarea, e.clientX, e.clientY);
    const range = getRangeForChar(charIndex);

    if (range) {
        const rangeKey = range[0] + '-' + range[1];
        const hoveredKey = hoveredRange ? hoveredRange[0] + '-' + hoveredRange[1] : null;

        if (rangeKey !== hoveredKey) {
            // Clear previous hover
            clearHoveredSpan();
            hoveredRange = range;
            setHoveredSpan(range);
        }

        // Position tooltip below mouse cursor
        showTooltip(e.clientX, e.clientY + 16);
    } else {
        if (hoveredRange) {
            clearHoveredSpan();
            hoveredRange = null;
            hideTooltip();
        }
    }
}

function onTextareaMouseLeave() {
    clearHoveredSpan();
    hoveredRange = null;
    hideTooltip();
}

function setHoveredSpan(range) {
    const textarea = domManager.get('textArea');
    if (!textarea) return;
    const container = textarea.parentNode?.querySelector('.highlights-container');
    if (!container) return;
    container.querySelectorAll('.trigger-word').forEach(span => {
        // Match spans by their text offset — find the span whose position in the
        // container's text node matches our range. We identify them by order.
        span.classList.add('hovered');
    });
    // More precisely: only add .hovered to spans that correspond to this range
    // We mark them by data-range attribute during build
    container.querySelectorAll(`.trigger-word[data-start="${range[0]}"]`).forEach(span => {
        span.classList.add('hovered');
    });
}

function clearHoveredSpan() {
    const textarea = domManager.get('textArea');
    if (!textarea) return;
    const container = textarea.parentNode?.querySelector('.highlights-container');
    if (!container) return;
    container.querySelectorAll('.trigger-word.hovered').forEach(span => {
        span.classList.remove('hovered');
    });
}

export function applyHighlights(textarea, ranges) {
    if (!textarea || !ranges || ranges.length === 0) {
        removeHighlights();
        return;
    }

    ensureStyles();
    currentRanges = mergeRanges(ranges);

    const text = textarea.value;

    const old = textarea.parentNode.querySelector('.highlights-container');
    if (old) old.remove();

    const container = document.createElement('div');
    container.className = 'highlights-container';

    const parent = textarea.parentNode;
    if (getComputedStyle(parent).position === 'static') {
        parent.style.position = 'relative';
    }

    const cs = window.getComputedStyle(textarea);
    Object.assign(container.style, {
        position:      'absolute',
        top:           textarea.offsetTop + 'px',
        left:          textarea.offsetLeft + 'px',
        width:         textarea.offsetWidth + 'px',
        height:        textarea.offsetHeight + 'px',
        padding:       cs.padding,
        border:        cs.border,
        margin:        cs.margin,
        fontFamily:    cs.fontFamily,
        fontSize:      cs.fontSize,
        fontWeight:    cs.fontWeight,
        lineHeight:    cs.lineHeight,
        letterSpacing: cs.letterSpacing,
        wordSpacing:   cs.wordSpacing,
        textAlign:     cs.textAlign,
        whiteSpace:    cs.whiteSpace,
        wordWrap:      cs.wordWrap,
        boxSizing:     cs.boxSizing,
        overflow:      'hidden',
        background:    'transparent',
        color:         'transparent',
        zIndex:        '1'
    });

    Object.assign(textarea.style, {
        background: 'transparent',
        position:   'relative',
        zIndex:     '2'
    });

    // Build HTML, tagging each trigger-word span with its start index
    let html = '';
    let pos = 0;
    for (const [start, end] of currentRanges) {
        if (pos < start) html += escapeHTML(text.slice(pos, start));
        html += `<span class="trigger-word" data-start="${start}">${escapeHTML(text.slice(start, end + 1))}</span>`;
        pos = end + 1;
    }
    if (pos < text.length) html += escapeHTML(text.slice(pos));

    container.innerHTML = html;
    parent.insertBefore(container, textarea);

    // Attach mouse tracking to the textarea itself (it's on top)
    textarea.removeEventListener('mousemove',  onTextareaMouseMove);
    textarea.removeEventListener('mouseleave', onTextareaMouseLeave);
    textarea.addEventListener('mousemove',  onTextareaMouseMove);
    textarea.addEventListener('mouseleave', onTextareaMouseLeave);

    console.log("[Highlight] Applied underline highlights");
    return container;
}

export const updateHighlights = debounce(async () => {
    const enabled = await checkHighlightingEnabled();
    if (appState.mode !== 1 || !enabled) return;

    const textArea = domManager.get('textArea');
    if (!textArea) return;

    const text = textArea.value;
    if (!text?.trim()) {
        removeHighlights();
        return;
    }

    try {
        const ranges = await getHighlights(text);
        if (ranges.length > 0) {
            applyHighlights(textArea, ranges);
        } else {
            removeHighlights();
        }
    } catch (error) {
        console.error("[Highlight] Error updating highlights:", error);
    }
}, 300);

export function removeHighlights() {
    const textArea = domManager.get('textArea');
    if (!textArea) return;

    const container = textArea.parentNode?.querySelector('.highlights-container');
    if (container) container.remove();

    textArea.style.background = '';
    textArea.removeEventListener('mousemove',  onTextareaMouseMove);
    textArea.removeEventListener('mouseleave', onTextareaMouseLeave);

    currentRanges = [];
    hoveredRange  = null;
    hideTooltip();
}

export function syncScroll() {
    const textArea = domManager.get('textArea');
    if (!textArea) return;
    const container = textArea.parentNode?.querySelector('.highlights-container');
    if (container) {
        container.scrollTop  = textArea.scrollTop;
        container.scrollLeft = textArea.scrollLeft;
    }
}

export async function initializeHighlighting() {
    console.log("[Highlight] Initializing...");
    const enabled = await checkHighlightingEnabled();
    if (appState.mode !== 1 || !enabled) return;

    const waitForTextArea = () => new Promise(resolve => {
        const check = () => {
            const ta = domManager.get('textArea');
            if (ta) resolve(ta);
            else setTimeout(check, 100);
        };
        check();
    });

    const textArea = await waitForTextArea();
    textArea.removeEventListener('input', updateHighlights);
    textArea.removeEventListener('scroll', syncScroll);
    textArea.addEventListener('input', updateHighlights);
    textArea.addEventListener('scroll', syncScroll);

    const handleResize = () => {
        const container = textArea.parentNode?.querySelector('.highlights-container');
        if (container) {
            Object.assign(container.style, {
                top:    textArea.offsetTop + 'px',
                left:   textArea.offsetLeft + 'px',
                width:  textArea.offsetWidth + 'px',
                height: textArea.offsetHeight + 'px'
            });
        }
    };
    window.removeEventListener('resize', handleResize);
    window.addEventListener('resize', handleResize);

    console.log("[Highlight] Initialization complete");
}

export async function triggerHighlighting() {
    const enabled = await checkHighlightingEnabled();
    if (appState.mode !== 1 || !enabled) return;

    const textArea = domManager.get('textArea');
    if (!textArea) return;

    const text = textArea.value;
    if (!text?.trim()) return;

    try {
        const ranges = await getHighlights(text);
        if (ranges.length > 0) applyHighlights(textArea, ranges);
    } catch (error) {
        console.error("[Highlight] Error in manual trigger:", error);
    }
}

export function renderHighlighting(data) {
    if (!data.enabled || !data.highlight_indices?.length) {
        removeHighlights();
        return;
    }
    const textArea = domManager.get('textArea');
    if (!textArea) return;
    applyHighlights(textArea, data.highlight_indices);
}