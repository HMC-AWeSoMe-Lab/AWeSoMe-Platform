import abc

# Fallback reason used when an intervention's payload doesn't specify one.
# Custom interventions researchers add later aren't required to set "reason" —
# if they don't, this generic fallback is what gets logged.
DEFAULT_TRIGGER_REASON = "Intervention conditions were met"


class BaseIntervention(abc.ABC):
    """
    Abstract base class for all intervention implementations.
    
    This class provides a framework for creating interventions that can be triggered
    by various events and can receive text content and conversation data.

    Payload contract for logging:
        Concrete `get_payload` implementations should include a "reason" key
        describing *why* the intervention fired (e.g. 'trigger word "hate"
        found in comment', 'comment tone flagged as emotional'). This is
        optional — if omitted, callers fall back to DEFAULT_TRIGGER_REASON —
        but including a specific reason makes the collected data far more
        useful for research analysis.
    """
    
    def __init__(self):
        pass

    def update(self, convo=None, text=None, **kwargs):
        """
        Process an intervention update and return the payload.
        
        This method passes all provided parameters to the concrete implementation's 
        get_payload method.

        For any payload of type "highlighting" (whether from
        HighlightingIntervention.get_payload or from a subclass that
        overrides get_payload entirely, e.g. one forwarding extra
        conversation context into a custom LLM-backed highlighter),
        this also stamps the payload with "source_text": the exact
        text this update() call was given. The frontend uses that to
        detect and discard stale responses: if the user kept typing
        while this request was in flight, highlight_indices describes
        positions in text that no longer exists, and rendering them
        against the textarea's now-current value paints highlights in
        the wrong place. Doing this here, once, in the shared base
        class - rather than requiring every highlighting subclass to
        remember to add "source_text" to its own returned dict - means
        a future highlighting intervention gets this protection
        automatically, even if it overrides get_payload completely and
        never calls super().get_payload().

        :param convo: Conversation object containing context data
        :type convo: object or None
        :param text: Text content from user input
        :type text: str or None
        :param kwargs: Additional parameters specific to the intervention type
        :type kwargs: dict
        :returns: The intervention payload or None if not applicable
        :rtype: dict or None
        """
        payload = self.get_payload(convo=convo, text=text, **kwargs)
        if isinstance(payload, dict) and payload.get("type") == "highlighting":
            payload.setdefault("source_text", text or "")
        return payload

    @abc.abstractmethod
    def get_payload(self, **kwargs):
        """
        Generate the intervention payload based on provided parameters.
        
        This method must be implemented by concrete intervention classes to define
        their specific behavior and return format.
        
        :param kwargs: Parameters filtered by the update method based on hooks
        :type kwargs: dict
        :returns: The intervention payload containing type, content, and metadata
        :rtype: dict or None
        :raises NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError