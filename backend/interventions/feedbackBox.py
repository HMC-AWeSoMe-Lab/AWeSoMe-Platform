# backend/interventions/feedbackBox.py
from backend.interventions.base import BaseIntervention
from backend.interventions.interventionHelpers import infer_trigger_reason

class feedbackBoxIntervention(BaseIntervention):
    """
    Intervention class for displaying positioned feedback boxes.

    Creates feedback box interventions that position themselves relative
    to other elements on the page to provide contextual feedback.
    """

    def __init__(self, trigger_event, text_func, button_id=None, parent_id=None, relation="right", width="220px"):
        """
        Initialize a feedback box intervention.

        :param trigger_event: When to trigger the feedback box (e.g., "onClick", "onText")
        :type trigger_event: str
        :param text_func: Function that generates feedback content based on input text
        :type text_func: callable
        :param button_id: Specific button ID to trigger feedback box, defaults to None
        :type button_id: str or None, optional
        :param parent_id: ID of parent element to position relative to, defaults to None
        :type parent_id: str or None, optional
        :param relation: Position relative to parent ("right", "left", "above", "below"), defaults to "right"
        :type relation: str, optional
        :param width: CSS width of the feedback box, defaults to "220px"
        :type width: str, optional
        """
        super().__init__()
        self.name = "feedbackBox"
        self.trigger_event = trigger_event
        self.button_id = button_id
        self.text_func = text_func
        self.parent_id = parent_id
        self.relation = relation
        self.width = width

    def get_payload(self, convo=None, text=None, button_id=None, **kwargs):
        """
        Generate the feedback box intervention payload.

        :param convo: Conversation context (unused for feedback boxes), defaults to None
        :type convo: convokit.Conversation or None, optional
        :param text: Text input to analyze for feedback content, defaults to None
        :type text: str or None, optional
        :param button_id: ID of button that was clicked, defaults to None
        :type button_id: str or None, optional
        :param kwargs: Additional keyword arguments
        :return: Feedback box intervention data or None if not triggered
        :rtype: dict or None
        :raises ValueError: If onClick trigger requires button_id but none provided
        """
        # Validate that onClick interventions have the required button_id
        if self.trigger_event == "onClick":
            if self.button_id is None:
                error_msg = f"feedbackBoxIntervention with onClick trigger must specify a button_id parameter"
                print(f"❌ INTERVENTION ERROR: {error_msg}")
                raise ValueError(error_msg)
            
            if self.button_id != button_id:
                return None
            
        feedback_text = self.text_func(text or "")
        
        # Create unique ID based on relation to avoid conflicts
        unique_id = f"feedback-box-{self.relation}"
        unique_button_id = f"feedback-button-{self.relation}"

        return {
            "type": "feedbackBox",
            "reason": infer_trigger_reason(text, default="Feedback box conditions were met (e.g. relevant button clicked)"),
            "html": f"""
                <div class="feedback-box" id="{unique_id}" 
                     data-intervention-type="feedbackBox"
                     data-event-id="FEEDBACK_BOX"
                     style="display: none; width: {self.width};">
                    <div id="feedback-text" data-event-id="FEEDBACK_BOX_INNER">{feedback_text}</div>
                    <button id="{unique_button_id}">See more</button>
                </div>""",
            "triggerEvent": self.trigger_event,
            "buttonId": self.button_id,
            "parentId": self.parent_id,
            "relation": self.relation
        }