import abc

class BaseIntervention(abc.ABC):
    """
    Abstract base class for all intervention implementations.
    
    This class provides a framework for creating interventions that can be triggered
    by various events and can receive text content and conversation data.
    """
    
    def __init__(self):
        pass

    def update(self, convo=None, text=None, **kwargs):
        """
        Process an intervention update and return the payload.
        
        This method passes all provided parameters to the concrete implementation's 
        get_payload method.
        
        :param convo: Conversation object containing context data
        :type convo: object or None
        :param text: Text content from user input
        :type text: str or None
        :param kwargs: Additional parameters specific to the intervention type
        :type kwargs: dict
        :returns: The intervention payload or None if not applicable
        :rtype: dict or None
        """
        return self.get_payload(convo=convo, text=text, **kwargs)

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
