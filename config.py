# config.py  —  Dummy Adapter version (for testing without a real corpus)
# -------------------------------------------------------
# THIS IS THE ONLY FILE YOU NEED TO CHANGE
# when switching to a different corpus or adapter.
# -------------------------------------------------------
# To switch to the real ConvoKit corpus, replace the three
# lines below with:
#
from backend.adapters.convokit_adapter import ConvoKitAdapter
active_adapter = ConvoKitAdapter("download:reddit-corpus-small")
active_adapter.load()
# -------------------------------------------------------

#from backend.convo_interface.dummy_adapter import DummyAdapter
#from backend.convo_interface.test_data import DUMMY_CONVERSATION
#active_adapter = DummyAdapter(DUMMY_CONVERSATION)
#active_adapter.load()


#from backend.adapters.tree_adapter import TreeAdapter
#active_adapter = TreeAdapter("download:reddit-corpus-small")
#active_adapter.load()