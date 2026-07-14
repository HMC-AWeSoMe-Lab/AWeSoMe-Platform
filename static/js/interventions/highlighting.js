import { appState } from '../services/appState.js';
import { domManager } from '../dom/domManager.js';
import { utils, debounce } from '../services/utils.js';

let highlightFeatureEnabled = null;

// ── Variant config ────────────────────────────────────────────────────────────
// Add a new entry here whenever a new HighlightingIntervention variant is added
// on the backend.  Each entry maps the variant name to:
//   cssClass   – class applied to highlighted <span>s in the overlay
//   hoverClass – class applied on mouseover
//   label      – grey header text shown in the tooltip
//   body       – main tooltip text
const VARIANTS = {
    default: {
        cssClass:   'trigger-word',
        hoverClass: 'trigger-word-hover',
        label:      'Trigger Word',
        body:       'Please consider avoiding this word'
    },
};
// ─────────────────────────────────────────────────────────────────────────────

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
        // Collect ALL highlighting payloads (there may be more than one variant).
        // Convert each payload's index pairs into {start, end, variant} objects
        // so the render layer can style them independently.
        const allRanges = [];
        interventions
            .filter(i => i.type === "highlighting" && i.enabled)
            .forEach(i => {
                const variant = i.variant || "default";
                (i.highlight_indices || []).forEach(([s, e]) => {
                    allRanges.push({ start: s, end: e, variant });
                });
            });
        return allRanges;
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
        /* Each variant renders into its own absolutely-positioned, fully
           transparent-background layer stacked on top of the others.
           Because every layer independently spans the whole textarea and
           only paints its own spans, overlapping ranges from different
           variants never compete for the same DOM text run - each variant
           keeps its own underline/background no matter what else overlaps it. */
        .highlights-container .highlight-layer {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            background: transparent;
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

// Current highlight ranges kept in memory so mousemove can check them.
// Each entry: { start, end, variant } — variant drives CSS class + tooltip.
let currentRanges = [];

// Shared tooltip
let tooltip = null;
function getTooltip() {
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.className = 'hw-tooltip';
        // Content is set dynamically in showTooltip() based on the hovered variant
        tooltip.innerHTML = `
            <span class="tt-label"></span>
            <span class="tt-body"></span>
        `;
        tooltip.style.display = 'none';
        document.body.appendChild(tooltip);
    }
    return tooltip;
}

function showTooltip(x, y, variant) {
    const tt = getTooltip();
    const cfg = VARIANTS[variant] || VARIANTS.default;
    tt.querySelector('.tt-label').textContent = cfg.label;
    tt.querySelector('.tt-body').textContent  = cfg.body;
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
    currentRanges.forEach(({ start: s, end: e }) => {
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
    for (const r of currentRanges) {
        if (charIndex >= r.start && charIndex <= r.end) return r;
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
        const rangeKey = range.start + '-' + range.end + '-' + range.variant;
        const hoveredKey = hoveredRange
            ? hoveredRange.start + '-' + hoveredRange.end + '-' + hoveredRange.variant
            : null;

        if (rangeKey !== hoveredKey) {
            clearHoveredSpan();
            hoveredRange = range;
            setHoveredSpan(range);
        }

        // Position tooltip below mouse cursor, passing variant for dynamic content
        showTooltip(e.clientX, e.clientY + 16, range.variant);
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
    const cfg = VARIANTS[range.variant] || VARIANTS.default;
    // Only hover the exact span that matches both start position and variant
    container
        .querySelectorAll(`.${cfg.cssClass}[data-start="${range.start}"][data-variant="${range.variant}"]`)
        .forEach(span => span.classList.add('hovered'));
}

function clearHoveredSpan() {
    const textarea = domManager.get('textArea');
    if (!textarea) return;
    const container = textarea.parentNode?.querySelector('.highlights-container');
    if (!container) return;
    // Clear hovered state from every variant class
    container.querySelectorAll('.hovered').forEach(span => span.classList.remove('hovered'));
}

// Builds the inner HTML for a single variant's layer: the full text, with
// only that variant's (already-merged, non-overlapping) ranges wrapped in
// highlight spans and everything else passed through untouched. Because
// each variant gets its own layer, this function never needs to know
// about any other variant's ranges, so overlapping highlights from other
// variants simply render in a different stacked layer instead of
// competing for the same span.
function buildLayerHTML(text, variantRanges) {
    const cfg = VARIANTS[variantRanges.variant] || VARIANTS.default;
    let html = '';
    let pos = 0;
    for (const [start, end] of variantRanges.pairs) {
        if (pos < start) html += escapeHTML(text.slice(pos, start));
        html += `<span class="${cfg.cssClass}" data-start="${start}" data-variant="${variantRanges.variant}">`
              + escapeHTML(text.slice(start, end + 1))
              + `</span>`;
        pos = end + 1;
    }
    if (pos < text.length) html += escapeHTML(text.slice(pos));
    return html;
}

export function applyHighlights(textarea, ranges) {
    if (!textarea || !ranges || ranges.length === 0) {
        removeHighlights();
        return;
    }

    ensureStyles();

    // Merge ranges within each variant separately. Variants are kept fully
    // separate all the way through rendering (see the per-variant layers
    // below) so that overlapping words of different colours/variants never
    // fight over the same DOM span - each variant owns its own layer no
    // matter how many other variants' ranges overlap the same characters.
    const byVariant = {};
    ranges.forEach(r => {
        const v = r.variant || 'default';
        (byVariant[v] = byVariant[v] || []).push([r.start, r.end]);
    });

    currentRanges = [];
    const mergedByVariant = [];
    Object.entries(byVariant).forEach(([variant, pairs]) => {
        const merged = mergeRanges(pairs);
        mergedByVariant.push({ variant, pairs: merged });
        merged.forEach(([s, e]) => {
            currentRanges.push({ start: s, end: e, variant });
        });
    });
    // Sorted purely for hover/lookup convenience elsewhere - rendering
    // below no longer depends on a single global left-to-right ordering.
    currentRanges.sort((a, b) => a.start - b.start);

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

    // Render one independent, fully-stacked layer per variant. Each layer
    // contains the *entire* text, with only its own variant's spans
    // highlighted - identical characters can therefore be wrapped in a
    // <span> in more than one layer simultaneously (e.g. a trigger word
    // that also happens to be a salad word), and both variants' styling
    // (underline colour, hover background, tooltip) render correctly at
    // once instead of one clobbering the other. Adding a new variant in
    // the future needs no changes here - it just gets its own layer.
    mergedByVariant.forEach(({ variant, pairs }) => {
        if (!pairs.length) return;
        const layer = document.createElement('div');
        layer.className = 'highlight-layer';
        layer.dataset.variant = variant;
        layer.innerHTML = buildLayerHTML(text, { variant, pairs });
        container.appendChild(layer);
    });

    parent.insertBefore(container, textarea);

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
        const ranges = await getHighlights(text);  // [{start,end,variant}, ...]
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
        const ranges = await getHighlights(text);  // [{start,end,variant}, ...]
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
    // Convert raw [[start,end]] pairs to {start,end,variant} objects so
    // applyHighlights can pick the right CSS class and tooltip per variant.
    const variant = data.variant || 'default';
    const ranges = data.highlight_indices.map(([s, e]) => ({ start: s, end: e, variant }));
    applyHighlights(textArea, ranges);
}

// Renders MULTIPLE "highlighting" intervention payloads in a single pass.
//
// Why this exists: applyHighlights() replaces the entire .highlights-container
// every time it runs, so calling renderHighlighting(data) once per payload
// (once per variant) means each call wipes out the previous variant's spans -
// only the last-processed variant would ever end up visible, even though the
// rendering layer itself supports overlapping/independent variants just fine.
// The fix is to combine every fired highlighting payload's ranges up front
// and hand them to applyHighlights() together, exactly once, regardless of
// how many separate HighlightingIntervention instances fired this round.
// Any number of future variants work automatically - this function doesn't
// need to know about specific variant names, just the generic payload shape.
export function renderHighlightingBatch(dataList) {
    const textArea = domManager.get('textArea');
    if (!textArea) return;

    const allRanges = [];
    (dataList || []).forEach(data => {
        if (!data || !data.enabled || !data.highlight_indices?.length) return;
        const variant = data.variant || 'default';
        data.highlight_indices.forEach(([s, e]) => {
            allRanges.push({ start: s, end: e, variant });
        });
    });

    if (allRanges.length === 0) {
        removeHighlights();
        return;
    }

    applyHighlights(textArea, allRanges);
}