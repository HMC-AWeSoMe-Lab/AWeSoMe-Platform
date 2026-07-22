# Adapter and Interface

The interface is an abstract class with the required functions: `load()`, `get_speaker()`, `get_conversation()`, `get_conversation_ids()`, and `get_utterance()`. These functions will be inherited by adapter files, which need to be written by the researchers, because the website is unable to run without a conversation, information about the speakers from the conversation, and the text (utterance). The three classes, `conversation`, `speaker`, and `utterance`, set the basic structure and information needed to make the platform run properly. All classes have their required information, such as `id`, and optional information, which can be added as a metadata dictionary.

![diagram](../static/images/AwesomePlatformDiagram.svg)

To see an example of a written-out class, look at `dummy_adapter`, `demo_adapter`, or `convokit_adapter` in `backend/adapter`. Both `dummy_adapter` and `demo_adapter` are loaded through a python dictionary while the `convokit_adapter` uses convokit. This feature allows for any type of conversation to be supported.

Finally, once the adapter is written, researchers can load it through the `config.py` file. For example of how to do this check out the ones written and commented out for `dummy_adapter`, `convokit_adapter`, and `demo_adapter`.
