// static/js/interventions/popup.js
import { appState } from '../services/appState.js';
import { pushToPayloadQueue } from '../services/payloadQueue.js';
import { eventHandlers } from '../events/eventHandlers.js';

/**
 * Renders a popup intervention in the DOM with text selection tracking.
 * Creates the popup element from backend HTML and adds event listeners.
 * 
 * @param {Object} data - The popup data from the backend
 * @param {string} data.html - The HTML content for the popup
 * @returns {void}
 */
export function renderPopup(data) {
  // Don't render a second popup if a blocking popup is already shown
  if (document.getElementById("popup")) return;

  const wrapper = document.createElement("div");
  wrapper.innerHTML = data.html;  // inject full HTML from backend
  const popupElement = wrapper.firstElementChild;
  
  // Add text selection logging to the popup-inner element
  const popupInner = popupElement.querySelector('.popup-inner');
  if (popupInner) {
    eventHandlers.addTextSelectionLogging(popupInner, "POPUP");
  }
  
  document.body.appendChild(popupElement);
}

// intervention specific event listeners

document.addEventListener("click", async (e) => {
  if (e.target.matches(".popup-close")) {
    document.getElementById("popup")?.remove();
    // Note: Button click logging is handled by the general click handler in eventSetup.js
  }
});