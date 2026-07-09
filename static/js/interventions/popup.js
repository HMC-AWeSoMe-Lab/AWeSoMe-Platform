// static/js/interventions/popup.js
import { appState } from '../services/appState.js';
import { pushToPayloadQueue } from '../services/payloadQueue.js';
import { eventHandlers } from '../events/eventHandlers.js';

// Kept as a no-op for backward compatibility: earlier versions used a
// global "shown once per reply" flag for non-blocking popups, which this
// function reset after submit/cancel. That suppression caused "See more"
// to only work once per reply (clicking it again silently did nothing),
// so the flag was removed from renderPopup below. This export is kept so
// existing call sites (e.g. in commentActions.js) don't need to change.
export function resetPopupShownFlag() {}

export function renderPopup(data) {
  // Don't stack a new popup while one is already open — but every distinct
  // onClick (e.g. clicking "See more" again) should still be able to show
  // a fresh popup, since the underlying content may have changed while the
  // user kept typing. There is intentionally no "only once per reply"
  // suppression here: onClick popups only ever fire in direct response to
  // an explicit button click, so there's no risk of them spamming on their
  // own, and limiting them to a single showing broke repeated clicks.
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