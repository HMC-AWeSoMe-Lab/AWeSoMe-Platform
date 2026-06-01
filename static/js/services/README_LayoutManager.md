# Layout Manager

A generic service for managing dynamic UI elements that need to reposition themselves when the page layout changes.

## Use Cases

- Tooltip-style elements that position relative to other elements
- Feedback boxes that need to avoid overlapping with content
- Floating UI elements that should move when their reference elements change
- Any absolutely positioned elements that depend on other elements' positions

## Basic Usage

```javascript
import { trackElementForRepositioning, untrackElement } from '../services/layoutManager.js';

// Define a repositioning function for your element
function repositionMyElement(element, metadata) {
    // Your positioning logic here
    // metadata contains any data you passed when registering the element
    const { targetId, placement } = metadata;
    // ... positioning code ...
}

// Register an element for automatic repositioning
const trackingId = trackElementForRepositioning(
    myElement,                              // The DOM element to track
    repositionMyElement,                    // Function to call when repositioning
    { targetId: 'some-id', placement: 'right' }  // Metadata for your positioning function
);

// Later, when you want to stop tracking the element
untrackElement(trackingId);
// or
untrackElement(myElement);
```

## What Triggers Repositioning

The layout manager automatically repositions tracked elements when:

1. **Window Resize**: Debounced to avoid excessive calls
2. **DOM Mutations**: Changes to the main content area (comments, forms, etc.)
3. **Manual Trigger**: When you call `repositionAllElements()`

## Safety Features

The layout manager includes several safety features to prevent positioning bugs:

- **Hidden Parent Detection**: Skips repositioning if the parent element is hidden (`display: none` or no `offsetParent`)
- **Stale Reference Cleanup**: Automatically removes elements that are no longer in the DOM
- **Error Handling**: Catches and logs positioning errors without breaking the entire system
- **Debounced Updates**: Prevents excessive repositioning calls during rapid DOM changes

## Advanced Usage

```javascript
import { layoutManager } from '../services/layoutManager.js';

// Direct access to the layout manager instance
const trackingId = layoutManager.trackElement(element, repositionFunction, metadata);

// Manual repositioning of all elements
layoutManager.repositionAll();

// Clear all tracked elements
layoutManager.clearAll();
```

## Implementation Notes

- Repositioning functions should be efficient as they may be called frequently
- The layout manager automatically cleans up references to removed DOM elements
- Resize events are debounced with a 250ms delay
- DOM mutation events are debounced with a 100ms delay
- The layout manager only sets up observers when there are tracked elements

## Example: Feedback Box Integration

```javascript
// This is how the feedback box system uses the layout manager:

function repositionFeedbackBox(element, metadata) {
    const { parentId, relation } = metadata;
    // Position the feedback box relative to its parent
    // Includes safety checks for hidden parents
    positionRelativeToParent(element, parentId, relation);
}

// When creating a feedback box:
const trackingId = trackElementForRepositioning(
    feedbackBoxElement,
    repositionFeedbackBox,
    { parentId: 'reply-box', relation: 'above' }
);

// When removing the feedback box:
untrackElement(trackingId);
```

## Best Practices

1. **Clear tracked elements before hiding their parents**: Always untrack or clear elements before hiding the elements they depend on for positioning
2. **Include parentId in metadata**: When possible, include the parent element ID in metadata so the layout manager can check if the parent is visible
3. **Handle positioning errors gracefully**: Your repositioning functions should include validation and error handling
4. **Use debounced manual triggers**: If you need to manually trigger repositioning, consider debouncing the calls

This approach allows any intervention or UI component to benefit from automatic layout management without coupling the layout system to specific intervention types.
