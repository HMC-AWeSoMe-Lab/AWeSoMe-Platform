# backend/interventions/popup.py
from backend.interventions.base import BaseIntervention

class PopupIntervention(BaseIntervention):
    """
    Intervention class for displaying popups

    Creates popup interventions that can be triggered by various events
    such as page load, button clicks, or text input.
    """

    def __init__(self, trigger_event, text_func, button_id=None):
        """
        Initialize a popup intervention.

        :param trigger_event: When to trigger the popup (e.g., "onClick", "onLoad", "onText")
        :type trigger_event: str
        :param text_func: Function that generates popup content based on input text
        :type text_func: callable
        :param button_id: Specific button ID to trigger popup (for onClick events), defaults to None
        :type button_id: str or None, optional
        """
        super().__init__()
        self.name = "popup"
        self.trigger_event = trigger_event
        self.button_id = button_id
        self.text_func = text_func

    def get_trigger_event(self):
        """
        Get the trigger event for this intervention.

        :return: The trigger event string
        :rtype: str
        """
        return self.trigger_event 
    
    def get_payload(self, convo=None, text=None, button_id=None, **kwargs):
        """
        Generate the popup intervention payload.

        :param convo: Conversation context (unused for popups), defaults to None
        :type convo: convokit.Conversation or None, optional
        :param text: Text input to analyze for popup content, defaults to None
        :type text: str or None, optional
        :param button_id: ID of button that was clicked, defaults to None
        :type button_id: str or None, optional
        :param kwargs: Additional keyword arguments
        :return: Popup intervention data or None if not triggered
        :rtype: dict or None
        :raises ValueError: If onClick trigger requires button_id but none provided
        """
        # Validate that onClick interventions have the required button_id
        if self.trigger_event == "onClick":
            if self.button_id is None:
                error_msg = f"PopupIntervention with onClick trigger must specify a button_id parameter"
                print(f"❌ INTERVENTION ERROR: {error_msg}")
                raise ValueError(error_msg)
            
            if self.button_id != button_id:
                return None

        popup_text = self.text_func(text or "")
        header_text = "ConvoWizard Suggestion"

        return {
            "type": "popup",
            "html": f"""<div class="popup" id="popup"
                        data-intervention-type="popup"
                        data-event-id="POPUP">
                        <div class="popup-inner" id="popup-inner"
                             data-event-id="POPUP_INNER">
                            <h2>{header_text}</h2>
                            <p>{popup_text}</p>
                            <button class="popup-close" id="popup-close-button">OK</button>
                        </div>
                        </div>""",
            "triggerEvent": self.trigger_event,
        }
