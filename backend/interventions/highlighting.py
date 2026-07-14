from backend.interventions.base import BaseIntervention
from backend.interventions.interventionHelpers import default_highlight_logic, infer_trigger_reason
import json

class HighlightingIntervention(BaseIntervention):
    """
    Intervention class for highlighting text in user input.

    Analyzes user text input and highlights potentially problematic
    or interesting portions based on configurable logic.
    """

    def __init__(self, trigger_event="onText", highlight_func=None, variant="default"):
        """
        Initialize the highlighting intervention.

        :param trigger_event: When to trigger highlighting ("onText", "onClick", etc.), defaults to "onText"
        :type trigger_event: str, optional
        :param button_id: Specific button ID for onClick triggers, defaults to None
        :type button_id: str or None, optional
        :param highlight_func: Function that takes text and returns highlight ranges, defaults to None
        :type highlight_func: callable or None, optional
        """
        super().__init__()
        self.name = "highlighting"
        self.trigger_event = trigger_event
        self.highlight_func = highlight_func or default_highlight_logic
        # variant is sent to the frontend so each HighlightingIntervention
        # can be styled and labelled independently (e.g. "default" = red,
        # "salad" = green).  See VARIANTS in highlighting.js for the mapping.
        self.variant = variant



    def get_payload(self, convo=None, text=None, trigger_event=None, **kwargs):
        """
        Generate highlighting payload with ranges to highlight.

        :param convo: Conversation context (unused for highlighting), defaults to None
        :type convo: convokit.Conversation or None, optional
        :param text: Text input to analyze for highlighting, defaults to None
        :type text: str or None, optional
        :param trigger_event: Event that triggered this intervention, defaults to None
        :type trigger_event: str or None, optional
        :param kwargs: Additional keyword arguments
        :return: Highlighting intervention data or None if not triggered
        :rtype: dict or None
        """
        # Check if this intervention should trigger
        if self.trigger_event != trigger_event:
            return None
            
        # For onClick events, check button ID
        if self.trigger_event == "onClick":
            return None
            
        # Get highlight ranges using the provided function
        highlight_ranges = self.highlight_func(text or "")

        # Nothing to highlight — don't fire the intervention at all.
        # Returning None means no DB row is written and the frontend receives
        # no highlighting payload, which is correct: the intervention only
        # "fires" when there is actually something to highlight.
        if not highlight_ranges:
            return None

        reason = infer_trigger_reason(
            text,
            default=f"{len(highlight_ranges)} portion(s) of the user's comment matched the highlighting criteria"
        )

        return {
            "type": "highlighting",
            "triggerEvent": self.trigger_event,
            "variant": self.variant,
            "reason": reason,
            "enabled": True,
            "highlight_indices": highlight_ranges
        }