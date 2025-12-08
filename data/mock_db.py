"""
Mock database using Pandas DataFrames.
Simulates Azure SQL tables for Users and Zones.
"""
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime
import uuid


# Users Table - Contains customer information
users_table = pd.DataFrame({
    'cil': ['1071324-101', '1300994-101', '3095678-303', '4017890-404', '5029012-505'],
    'name': ['Abdenbi EL MARZOUKI', 'Ahmed Sabil', 'محمد الإدريسي', 'خديجة العلوي', 'يوسف السباعي'],
    'address': ['967, Lot. Sala Al Jadida Zone (1), Sala Al Jadida', '2 Rue BATTIT I Ghizlaine Imm 2 apt 03', 'شارع محمد الخامس، فاس', 'حي النخيل، مراكش', 'شارع الزرقطوني، طنجة'],
    'phone': ['0612345678', '0698765432', '0611223344', '0655667788', '0699887766'],
    'service_type': ['ماء وكهرباء', 'ماء', 'ماء', 'كهرباء', 'ماء وكهرباء'],
    'zone_id': [1, 2, 1, 3, 2],
    'payment_status': ['مدفوع', 'مدفوع', 'مدفوع', 'مدفوع', 'غير مدفوع'],
    'last_payment_date': ['2026-01-15', '2026-01-08', '2026-01-28', '2026-01-10', '2026-01-15'],
    'outstanding_balance': [0.0, 0.0, 0.0, 0.0, 890.0],
    'service_status': ['نشط', 'نشط', 'نشط', 'نشط', 'مقطوع']
})


# Zones Table - Contains maintenance and outage information
zones_table = pd.DataFrame({
    'zone_id': [1, 2, 3, 4],
    'zone_name': ['الدار البيضاء - وسط المدينة', 'الرباط - حي المحمدي', 'مراكش - القليعة', 'طنجة - المدينة القديمة'],
    'maintenance_status': ['جاري الصيانة', 'لا توجد صيانة', 'لا توجد صيانة', 'جاري الصيانة'],
    'outage_reason': ['إصلاح أنابيب المياه الرئيسية', None, None, 'صيانة محولات الكهرباء'],
    'estimated_restoration': ['2024-12-04 18:00', None, None, '2024-12-05 14:00'],
    'affected_services': ['ماء', None, None, 'كهرباء'],
    'status_updated': ['2024-12-03 08:00', '2024-12-01 10:00', '2024-12-01 10:00', '2024-12-03 06:00']
})


def get_user_by_cil(cil: str) -> Optional[dict]:
    """
    Retrieve user information by CIL (Customer Identification Number).
    
    Args:
        cil: Customer Identification Number
        
    Returns:
        dict: User information or None if not found
    """
    user = users_table[users_table['cil'] == cil]
    
    if user.empty:
        return None
    
    return user.iloc[0].to_dict()


def get_zone_by_id(zone_id: int) -> Optional[dict]:
    """
    Retrieve zone/maintenance information by zone ID.
    
    Args:
        zone_id: Zone identification number
        
    Returns:
        dict: Zone information or None if not found
    """
    zone = zones_table[zones_table['zone_id'] == zone_id]
    
    if zone.empty:
        return None
    
    return zone.iloc[0].to_dict()


def get_all_users() -> pd.DataFrame:
    """Get all users from the database."""
    return users_table.copy()


def get_all_zones() -> pd.DataFrame:
    """Get all zones from the database."""
    return zones_table.copy()


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
