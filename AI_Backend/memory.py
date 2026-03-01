# memory.py - Conversation memory management for web UI

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory


# In-memory store for LangChain message history
# Used for maintaining stateful agent conversations
store = {}


def get_session_history(session_id: str):
    """
    Get or create chat history for a session
    
    Used by LangChain's RunnableWithMessageHistory for agent state management
    """
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


def clear_session_history(session_id: str):
    """Clear history for a specific session"""
    if session_id in store:
        del store[session_id]


def clear_all_history():
    """Clear all in-memory history (use with caution)"""
    global store
    store = {}