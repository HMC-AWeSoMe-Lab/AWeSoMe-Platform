import random





def getToxicityScoreText(score):
    """
    Returns a string representation of the toxicity score.
    Args:
        score (float): The toxicity score.
    Returns:
        str: A string representation of the toxicity score.
    """
    if score > 0.55:
        return "<h3>ConvoWizard: Reply Summary</h3><p>ConvoWizard thinks this comment might increase the tension in this discussion. Remember that you will be most likely to have a productive discussion with a civil, respectful, and open approach.</p>"
    else:
        return "<h3>ConvoWizard: Reply Summary</h3><p>ConvoWizard thinks this comment might decrease tension in this discussion.</p>"