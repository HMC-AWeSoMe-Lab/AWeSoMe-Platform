// 📦 Import renderers
import { renderPopup } from "./popup.js";
import { renderFeedbackBox } from "./feedbackBox.js";
import { renderHighlighting } from "./highlighting.js";

/**
 * Dispatch table mapping intervention types to their rendering functions.
 * Used by the main intervention system to route backend intervention data to appropriate handlers.
 */
export const interventionHandlers = {
  popup: renderPopup,
  feedbackBox: renderFeedbackBox,
  highlighting: renderHighlighting
};
