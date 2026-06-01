import re
import random
import string
import markdown
from convokit import Corpus, download

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
        # mark new speakers in speakerDict by order
        if utt.speaker not in speakerDict:
            speakerDict[utt.speaker] = len(speakerDict) + 1


        transcript_output += ("Speaker" + str(speakerDict[utt.speaker]) + ": " + utt.text + "\n")
    
    convo.add_meta('text', transcript_output)
    return fix_summary_chars(transcript_output)

def transcript_id(id, corpus):
    """Returns transcript of a conversation given its ID

    :param id: ID of conversation
    :type id: str
    :param corpus: corpus the conversation is from
    :type corpus: Corpus
    :return: transcript of conversation
    :rtype: str
    """
    return transcript(corpus.get_conversation(id))


def get_SCD(convo):
    return markdown.markdown(convo.meta["summary_meta"][-1])