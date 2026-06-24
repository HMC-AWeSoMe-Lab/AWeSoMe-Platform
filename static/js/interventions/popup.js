// static/js/interventions/popup.js
import { appState } from '../services/appState.js';
import { pushToPayloadQueue } from '../services/payloadQueue.js';
import { eventHandlers } from '../events/eventHandlers.js';

// Tracks whether the non-blocking popup has already fired for the current reply session
let popupShownThisReply = false;

export function resetPopupShownFlag() {
  popupShownThisReply = false;
}

export function renderPopup(data) {
  // Don't render if a popup is already visible
  if (document.getElementById("popup")) return;

  // For non-blocking popups (the reply-btn one), only show once per reply session
  if (!data.blocking) {
    if (popupShownThisReply) return;
    popupShownThisReply = true;
  }

  const wrapper = document.createElement("div");
  wrapper.innerHTML = data.html;
  const popupElement = wrapper.firstElementChild;

  const popupInner = popupElement.querySelector('.popup-inner');
  if (popupInner) {
    eventHandlers.addTextSelectionLogging(popupInner, "POPUP");
  }

  document.body.appendChild(popupElement);
}

document.addEventListener("click", async (e) => {
  if (e.target.matches(".popup-close")) {
    document.getElementById("popup")?.remove();
  }
});