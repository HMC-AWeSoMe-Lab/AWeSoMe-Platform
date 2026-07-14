import { appState } from '../services/appState.js';
import { pushToPayloadQueue } from '../services/payloadQueue.js';
import { eventHandlers } from '../events/eventHandlers.js';

export function resetPopupShownFlag() {}

export function renderPopup(data) {
  // Blocking popups are handled entirely by showBlockingPopup() in
  // commentActions.js — renderPopup must not touch them or their buttons
  // will have no event listeners.
  if (data.blocking) return;

  if (document.getElementById("popup")) return;

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