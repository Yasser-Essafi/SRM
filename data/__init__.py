"""Data package for SRM application."""
from .mock_db import users_table, zones_table, get_user_by_contract, get_zone_by_id

__all__ = ['users_table', 'zones_table', 'get_user_by_contract', 'get_zone_by_id']
