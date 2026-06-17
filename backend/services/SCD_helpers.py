import re
import random
import string
import markdown


def fix_summary_chars(input_text):
    """Given by Yilun (borrowed from Convokit repo / cornell)
    use this right before you output the transcript
    :param input_text: transcript to clean
    :type input_text: str
    :return: cleaned transcript
    :rtype: str
    """

    # Define the regex pattern to match '&gt;' and the first '\n' behind it
    pattern = r'&gt;(.*?)\n'

    # Define a function to handle the replacement

    # TODO fix the quotation mark in the original json formatted transcripts.
    # quote until the end of the comment?
    def replace_quote(match):
        return '"' + match.group(1) + '"'

    # Use re.sub() to perform the replacement
    def fix_transcript_quote(transcript):
        return re.sub(pattern, replace_quote, transcript)

    # Print the result
    output_text = fix_transcript_quote(input_text)
    return output_text

def transcript(convo):
    """Returns transcript of a given Conversation

    :param id: conversation to transcribe
    :type id: Conversation
    :return: transcript of conversation
    :rtype: str
    """
    transcript_output = ""

    speakerDict = {}

    # loop through utterances and add their speakers and text to transcript
    for utt in convo.get_chronological_utterance_list():
        if utt.speaker_id not in speakerDict:
            speakerDict[utt.speaker_id] = len(speakerDict) + 1
        transcript_output += ("Speaker" + str(speakerDict[utt.speaker_id]) + ": " + utt.text + "\n")

    
    convo.add_meta('text', transcript_output)
    return fix_summary_chars(transcript_output)

from config import active_adapter

def transcript_id(convo_id):
    return transcript(active_adapter.get_conversation(convo_id))


def get_SCD(convo):
    return markdown.markdown(convo.meta["conversation_summary"][-1])