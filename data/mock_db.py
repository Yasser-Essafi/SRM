"""
Mock database using Pandas DataFrames.
Simulates Azure SQL tables for Users and Zones.
"""
import pandas as pd
from typing import Optional


# Users Table - Contains customer information
users_table = pd.DataFrame({
    'cil': ['12345678', '87654321', '11223344', '55667788', '99887766'],
    'name': ['أحمد المرزوقي', 'فاطمة الزهراء', 'محمد الإدريسي', 'خديجة العلوي', 'يوسف السباعي'],
    'address': ['شارع الحسن الثاني، الدار البيضاء', 'حي المحمدي، الرباط', 'شارع محمد الخامس، فاس', 'حي النخيل، مراكش', 'شارع الزرقطوني، طنجة'],
    'phone': ['0612345678', '0698765432', '0611223344', '0655667788', '0699887766'],
    'service_type': ['ماء', 'كهرباء', 'ماء', 'كهرباء', 'ماء وكهرباء'],
    'zone_id': [1, 2, 1, 3, 2],
    'payment_status': ['مدفوع', 'غير مدفوع', 'مدفوع', 'مدفوع', 'غير مدفوع'],
    'last_payment_date': ['2024-11-15', '2024-09-20', '2024-11-28', '2024-11-10', '2024-08-15'],
    'outstanding_balance': [0.0, 450.0, 0.0, 0.0, 890.0],
    'service_status': ['نشط', 'مقطوع', 'نشط', 'نشط', 'مقطوع']
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
