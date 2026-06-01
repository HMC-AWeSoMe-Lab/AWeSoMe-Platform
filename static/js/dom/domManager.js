/**
 * DOM element management class for caching and accessing frequently used elements.
 * Provides centralized access to DOM elements throughout the application.
 */
class DOMManager {
    /**
     * Initialize the DOM manager with empty element references.
     */
    constructor() {
        this.elements = {
            textArea: null,
            commentArea: null,
            postButton: null,
            cancelButton: null
        };
    }

    /**
     * Initializes all DOM element references by querying the document.
     * Should be called after the DOM is fully loaded.
     * 
     * @returns {void}
     */
    initialize() {
        this.elements.textArea = document.getElementById('content');
        this.elements.commentArea = document.getElementsByClassName('comment__card');
        this.elements.postButton = document.getElementById('submit-comment');
        this.elements.cancelButton = document.getElementById('cancel-button');
    }

    /**
     * Retrieves a cached DOM element by name.
     * 
     * @param {string} elementName - The name of the element to retrieve
     * @returns {HTMLElement|null} The DOM element or null if not found
     */
    get(elementName) {
        return this.elements[elementName];
    }

    /**
     * Sets a DOM element reference by name.
     * 
     * @param {string} elementName - The name to store the element under
     * @param {HTMLElement} element - The DOM element to store
     * @returns {void}
     */
    set(elementName, element) {
        this.elements[elementName] = element;
    }
}

// Export singleton instance
export const domManager = new DOMManager();