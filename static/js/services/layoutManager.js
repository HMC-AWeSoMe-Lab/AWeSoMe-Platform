/**
 * Generic layout management service for dynamic UI elements.
 * Tracks elements and automatically repositions them when the layout changes.
 */
export class LayoutManager {
    /**
     * Initialize the layout manager with empty tracking arrays.
     */
    constructor() {
        this.trackedElements = [];
        this.resizeHandler = null;
        this.mutationObserver = null;
    }

    /**
     * Registers an element for dynamic repositioning when layout changes occur.
     * Sets up observers for the first tracked element.
     * 
     * @param {HTMLElement} element - The DOM element to track
     * @param {Function} repositionFunction - Function to call when repositioning is needed
     * @param {Object} [metadata={}] - Additional data needed for repositioning
     * @returns {string} Unique tracking ID for the element
     */
    trackElement(element, repositionFunction, metadata = {}) {
        const trackedElement = {
            element,
            repositionFunction,
            metadata,
            id: this.generateId()
        };
        
        this.trackedElements.push(trackedElement);
        console.log(`[LayoutManager] Now tracking ${this.trackedElements.length} elements`);
        
        // Set up observers if this is the first element
        if (this.trackedElements.length === 1) {
            this.setupObservers();
        }
        
        return trackedElement.id;
    }

    /**
     * Removes an element from tracking and cleans up observers if needed.
     * Automatically cleans up observers when no elements remain tracked.
     * 
     * @param {string|HTMLElement} elementOrId - Element or its tracking ID to remove
     * @returns {void}
     */
    untrackElement(elementOrId) {
        const index = typeof elementOrId === 'string' 
            ? this.trackedElements.findIndex(item => item.id === elementOrId)
            : this.trackedElements.findIndex(item => item.element === elementOrId);
            
        if (index !== -1) {
            this.trackedElements.splice(index, 1);
            console.log(`[LayoutManager] Element untracked. ${this.trackedElements.length} remaining.`);
        }
        
        // Clean up observers if no elements remain
        if (this.trackedElements.length === 0) {
            this.cleanupObservers();
        }
    }

    /**
     * Repositions all tracked elements and cleans up stale references.
     * Automatically removes elements that are no longer in the DOM.
     * 
     * @returns {void}
     */
    repositionAll() {
        console.log(`[LayoutManager] Repositioning ${this.trackedElements.length} tracked elements`);
        
        // Clean up stale references
        this.trackedElements = this.trackedElements.filter(item => {
            if (!item.element || !document.body.contains(item.element)) {
                console.log(`[LayoutManager] Removing stale element reference`);
                return false;
            }
            return true;
        });
        
        // Reposition remaining elements, but check if their parent elements are visible first
        this.trackedElements.forEach((item, index) => {
            try {
                // Check if the parent element (if specified) is visible before repositioning
                if (item.metadata && item.metadata.parentId) {
                    const parent = document.getElementById(item.metadata.parentId);
                    if (!parent || parent.style.display === 'none' || !parent.offsetParent) {
                        console.log(`[LayoutManager] Skipping repositioning - parent ${item.metadata.parentId} is not visible`);
                        return;
                    }
                }
                
                console.log(`[LayoutManager] Repositioning element ${index + 1}`);
                item.repositionFunction(item.element, item.metadata);
            } catch (error) {
                console.error(`[LayoutManager] Error repositioning element ${index + 1}:`, error);
            }
        });
    }

    /**
     * Clear all tracked elements
     */
    clearAll() {
        console.log(`[LayoutManager] Clearing all ${this.trackedElements.length} tracked elements`);
        this.trackedElements = [];
        this.cleanupObservers();
    }

    // Private methods
    generateId() {
        return `layout_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    setupObservers() {
        this.setupResizeHandler();
        this.setupMutationObserver();
    }

    setupResizeHandler() {
        if (!this.resizeHandler) {
            this.resizeHandler = this.debounce(() => {
                console.log('[LayoutManager] Window resized, repositioning elements');
                this.repositionAll();
            }, 250);
            
            window.addEventListener('resize', this.resizeHandler);
            console.log('[LayoutManager] Resize handler set up');
        }
    }

    setupMutationObserver() {
        if (!this.mutationObserver) {
            // Watch for changes in the main content area
            const contentContainer = document.getElementById('reddit-convo') || 
                                   document.querySelector('.container') || 
                                   document.body;
                                   
            if (contentContainer) {
                this.mutationObserver = new MutationObserver(this.debounce(() => {
                    console.log('[LayoutManager] DOM mutations detected, repositioning elements');
                    this.repositionAll();
                }, 100));
                
                this.mutationObserver.observe(contentContainer, {
                    childList: true,
                    subtree: true,
                    attributes: true,
                    attributeFilter: ['style', 'class']
                });
                
                console.log('[LayoutManager] Mutation observer set up');
            }
        }
    }

    cleanupObservers() {
        if (this.resizeHandler) {
            window.removeEventListener('resize', this.resizeHandler);
            this.resizeHandler = null;
            console.log('[LayoutManager] Resize handler cleaned up');
        }

        if (this.mutationObserver) {
            this.mutationObserver.disconnect();
            this.mutationObserver = null;
            console.log('[LayoutManager] Mutation observer cleaned up');
        }
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        }.bind(this);
    }
}

// Create a singleton instance for global use
export const layoutManager = new LayoutManager();

// Convenience functions for common use cases
export function trackElementForRepositioning(element, repositionCallback, metadata = {}) {
    return layoutManager.trackElement(element, repositionCallback, metadata);
}

export function untrackElement(elementOrId) {
    layoutManager.untrackElement(elementOrId);
}

export function repositionAllElements() {
    layoutManager.repositionAll();
}

export function clearAllTrackedElements() {
    layoutManager.clearAll();
}
