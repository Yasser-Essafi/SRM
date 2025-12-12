"""
Mock database using Pandas DataFrames.
Simulates Azure SQL tables for Users, Water Invoices, and Electricity Invoices.
"""
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime
import uuid


# Users Table - Contains customer information
users_table = pd.DataFrame({
    'user_id': [1, 2, 3, 4, 5],
    'name': ['عبد النبي المرزوقي', 'أحمد السعيدي', 'محمد الإدريسي', 'خديجة العلوي', 'يوسف السباعي'],
    'address': ['حي المسيرة، مراكش', 'حي الداوديات، مراكش', 'شارع محمد الخامس، مراكش', 'حي جيليز، مراكش', 'حي الصناعي، آسفي'],
    'phone': ['0612345678', '0698765432', '0611223344', '0655667788', '0699887766'],
    'zone_id': [1, 2, 3, 4, 5]
})


# Water Invoices Table - Contains water service information
water_invoices_table = pd.DataFrame({
    'water_contract_number': ['3701455886 / 1014871', '3701455887 / 1014872', '3701455888 / 1014873', '3701455890 / 1014875'],
    'user_id': [1, 2, 3, 5],
    'is_paid': [True, True, True, False],
    'outstanding_balance': [0.0, 0.0, 0.0, 450.0],
    'last_payment_date': ['2026-01-15', '2026-01-08', '2026-01-28', '2026-01-15'],
    'cut_status': ['OK', 'OK', 'OK', 'CUT_OFF'],
    'cut_reason': [None, None, None, 'Non-payment']
})


# Electricity Invoices Table - Contains electricity service information
electricity_invoices_table = pd.DataFrame({
    'electricity_contract_number': ['4801566997 / 2025982', '4801566998 / 2025983', '4801566999 / 2025984', '4801567001 / 2025986'],
    'user_id': [1, 3, 4, 5],
    'is_paid': [True, True, True, False],
    'outstanding_balance': [0.0, 0.0, 0.0, 440.0],
    'last_payment_date': ['2026-01-15', '2026-01-28', '2026-01-10', '2026-01-15'],
    'cut_status': ['OK', 'OK', 'OK', 'CUT_OFF'],
    'cut_reason': [None, None, None, 'Non-payment']
})


# Zones Table - Contains maintenance and outage information
zones_table = pd.DataFrame({
    'zone_id': [1, 2, 3, 4, 5],
    'zone_name': ['مراكش - حي المسيرة', 'مراكش - حي الداوديات', 'مراكش - حي جيليز', 'مراكش - المدينة القديمة', 'آسفي - الحي الصناعي'],
    'maintenance_status': ['جاري الصيانة', 'لا توجد صيانة', 'لا توجد صيانة', 'جاري الصيانة', 'لا توجد صيانة'],
    'outage_reason': ['إصلاح أنابيب المياه الرئيسية', None, None, 'صيانة محولات الكهرباء', None],
    'estimated_restoration': ['2024-12-04 18:00', None, None, '2024-12-05 14:00', None],
    'affected_services': ['ماء', None, None, 'كهرباء', None],
    'status_updated': ['2024-12-03 08:00', '2024-12-01 10:00', '2024-12-01 10:00', '2024-12-03 06:00', '2024-12-01 10:00']
})


def get_user_by_water_contract(water_contract: str) -> Optional[dict]:
    """
    Retrieve user and water invoice information by water contract number.
    Supports both full format (3701455886 / 1014871) and partial (3701455886).
    
    Args:
        water_contract: Water Contract Number (full or partial)
        
    Returns:
        dict: Combined user and water invoice information or None if not found
    """
    # First try exact match
    invoice = water_invoices_table[water_invoices_table['water_contract_number'] == water_contract]
    
    # If not found and contract doesn't contain '/', try partial match
    if invoice.empty and '/' not in water_contract:
        invoice = water_invoices_table[water_invoices_table['water_contract_number'].str.split(' / ').str[0] == water_contract.strip()]
    
    if invoice.empty:
        return None
    
    invoice_dict = invoice.iloc[0].to_dict()
    user_id = invoice_dict['user_id']
    
    # Get user information
    user = users_table[users_table['user_id'] == user_id]
    if user.empty:
        return None
    
    user_dict = user.iloc[0].to_dict()
    
    # Combine user and invoice data
    result = {**user_dict, **invoice_dict}
    result['service_type'] = 'ماء'
    return result


def get_user_by_electricity_contract(electricity_contract: str) -> Optional[dict]:
    """
    Retrieve user and electricity invoice information by electricity contract number.
    Supports both full format (4801566997 / 2025982) and partial (4801566997).
    
    Args:
        electricity_contract: Electricity Contract Number (full or partial)
        
    Returns:
        dict: Combined user and electricity invoice information or None if not found
    """
    # First try exact match
    invoice = electricity_invoices_table[electricity_invoices_table['electricity_contract_number'] == electricity_contract]
    
    # If not found and contract doesn't contain '/', try partial match
    if invoice.empty and '/' not in electricity_contract:
        invoice = electricity_invoices_table[electricity_invoices_table['electricity_contract_number'].str.split(' / ').str[0] == electricity_contract.strip()]
    
    if invoice.empty:
        return None
    
    invoice_dict = invoice.iloc[0].to_dict()
    user_id = invoice_dict['user_id']
    
    # Get user information
    user = users_table[users_table['user_id'] == user_id]
    if user.empty:
        return None
    
    user_dict = user.iloc[0].to_dict()
    
    # Combine user and invoice data
    result = {**user_dict, **invoice_dict}
    result['service_type'] = 'كهرباء'
    return result


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


def get_all_water_invoices() -> pd.DataFrame:
    """Get all water invoices from the database."""
    return water_invoices_table.copy()


def get_all_electricity_invoices() -> pd.DataFrame:
    """Get all electricity invoices from the database."""
    return electricity_invoices_table.copy()


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
