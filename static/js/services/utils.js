/**
 * Creates a debounced version of a function that delays execution until after a specified wait time.
 * Useful for preventing excessive API calls or event handler executions.
 * 
 * @param {Function} func - The function to debounce
 * @param {number} wait - The number of milliseconds to delay
 * @returns {Function} The debounced function
 */
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Collection of utility functions for common tasks.
 */
export const utils = {
    /**
     * Performs a fetch request and returns parsed JSON data.
     * Handles errors and provides consistent error logging.
     * 
     * @param {string} url - The URL to fetch from
     * @param {Object} [options={}] - Fetch options (method, body, headers, etc.)
     * @returns {Promise<*>} Promise that resolves to the parsed JSON response
     * @throws {Error} Throws error if fetch fails or response is not ok
     */
    async fetchJSON(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: { 'Content-Type': 'application/json' },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`Error fetching ${url}:`, error);
            throw error;
        }
    },

    /**
     * Escapes HTML characters in text to prevent XSS attacks.
     * Converts special characters to HTML entities.
     * 
     * @param {string} text - The text to escape
     * @returns {string} The HTML-escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Fetches and caches the application settings from settings.json.
     * Uses caching to avoid repeated network requests for the same data.
     * 
     * @returns {Promise<Object>} Promise that resolves to the settings object
     */
    getSettings: (() => {
        let cachedSettings = null;

        return async function () {
            if (cachedSettings) return cachedSettings;
            cachedSettings = await utils.fetchJSON('/static/settings.json');
            return cachedSettings;
        };
    })()
};
