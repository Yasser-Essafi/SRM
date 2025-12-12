"""Data package for SRM application."""
from .mock_db import (
    users_table, 
    water_invoices_table, 
    electricity_invoices_table, 
    zones_table, 
    get_user_by_water_contract, 
    get_user_by_electricity_contract, 
    get_zone_by_id
)

__all__ = [
    'users_table', 
    'water_invoices_table', 
    'electricity_invoices_table', 
    'zones_table', 
    'get_user_by_water_contract', 
    'get_user_by_electricity_contract', 
    'get_zone_by_id'
]
