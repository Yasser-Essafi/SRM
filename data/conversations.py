"""
Conversation history management.
In-memory storage for conversation sessions.
"""
from typing import Optional, List, Dict
from datetime import datetime
import uuid


# Conversations Store - In-memory storage for conversation history
conversations_store = {}


def create_conversation() -> str:
    """
    Create a new conversation and return its unique ID.
    
    Returns:
        str: Unique conversation ID
    """
    conversation_id = str(uuid.uuid4())
    conversations_store[conversation_id] = {
        'conversation_id': conversation_id,
        'created_at': datetime.now().isoformat(),
        'messages': []
    }
    return conversation_id


def get_conversation(conversation_id: str) -> Optional[Dict]:
    """
    Retrieve a conversation by ID.
    
    Args:
        conversation_id: Unique conversation identifier
        
    Returns:
        dict: Conversation data with messages or None if not found
    """
    return conversations_store.get(conversation_id)


def add_message_to_conversation(conversation_id: str, role: str, content: str) -> bool:
    """
    Add a message to an existing conversation.
    
    Args:
        conversation_id: Unique conversation identifier
        role: Message role ('user' or 'assistant')
        content: Message content
        
    Returns:
        bool: True if successful, False if conversation not found
    """
    conversation = conversations_store.get(conversation_id)
    
    if not conversation:
        return False
    
    message = {
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat()
    }
    
    conversation['messages'].append(message)
    return True


def get_conversation_history(conversation_id: str) -> List[Dict]:
    """
    Get the message history for a conversation.
    
    Args:
        conversation_id: Unique conversation identifier
        
    Returns:
        list: List of messages or empty list if conversation not found
    """
    conversation = conversations_store.get(conversation_id)
    
    if not conversation:
        return []
    
    return conversation['messages']
