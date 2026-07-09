# backend/interventions/popup.py
from backend.interventions.base import BaseIntervention
from backend.interventions.interventionHelpers import infer_trigger_reason

class PopupIntervention(BaseIntervention):
    """
    Intervention class for displaying popups

    Creates popup interventions that can be triggered by various events
    such as page load, button clicks, or text input.
    """

    def __init__(self, trigger_event, text_func, button_id=None, blocking=False):
        """
        Initialize a popup intervention.

        :param trigger_event: When to trigger the popup (e.g., "onClick", "onLoad", "onText")
        :type trigger_event: str
        :param text_func: Function that generates popup content based on input text
        :type text_func: callable
        :param button_id: Specific button ID to trigger popup (for onClick events), defaults to None
        :type button_id: str or None, optional
        :param blocking: If True, shows "Post Anyway" / "Edit Post" buttons instead of OK,
                         and prevents the comment from posting until the user chooses.
        :type blocking: bool, optional
        """
        super().__init__()
        self.name = "popup"
        self.trigger_event = trigger_event
        self.button_id = button_id
        self.text_func = text_func
        self.blocking = blocking

    def get_trigger_event(self):
        """
        Get the trigger event for this intervention.

        :return: The trigger event string
        :rtype: str
        """
        return self.trigger_event

    def get_payload(self, convo=None, text=None, button_id=None, **kwargs):
        if self.trigger_event == "onClick":
            if self.button_id is None:
                error_msg = "PopupIntervention with onClick trigger must specify a button_id parameter"
                print(f"❌ INTERVENTION ERROR: {error_msg}")
                raise ValueError(error_msg)

            if self.button_id != button_id:
                return None

        popup_text = self.text_func(text or "")

        # No trigger word found — don't show a popup at all
        if popup_text is None:
            return None

        header_text = "ConvoWizard Suggestion"

        if self.blocking:
            buttons_html = """
                <button type="button" class="popup-post-anyway" id="popup-post-anyway-button">Post Anyway</button>
                <button type="button" class="popup-edit" id="popup-edit-button">Edit Post</button>
            """
        else:
            buttons_html = '<button class="popup-close" id="popup-close-button">OK</button>'

        return {
            "type": "popup",
            "blocking": self.blocking,
            "reason": infer_trigger_reason(text),
            "html": f"""<div class="popup" id="popup"
                        data-intervention-type="popup"
                        data-event-id="POPUP">
                        <div class="popup-inner" id="popup-inner"
                             data-event-id="POPUP_INNER">
                            <h2>{header_text}</h2>
                            <p>{popup_text}</p>
                            {buttons_html}
                        </div>
                        </div>""",
            "triggerEvent": self.trigger_event,
        }