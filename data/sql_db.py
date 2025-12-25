"""
Azure SQL Database access layer.
Provides functions to query Users, Water Invoices, Electricity Invoices, and Zones.
"""
import pyodbc
from typing import Optional, Dict
from config.settings import settings


def get_connection():
    """
    Create and return a connection to Azure SQL Database.
    
    Returns:
        pyodbc.Connection: Database connection object
        
    Raises:
        Exception: If connection fails
    """
    try:
        # Validate credentials are configured
        if not settings.AZURE_SQL_SERVER or not settings.AZURE_SQL_DATABASE:
            raise Exception("SQL Server and Database must be set in .env file")

        if not settings.AZURE_SQL_USERNAME:
            # Use Windows Authentications
            connection_string = (
                f"Driver={{{settings.AZURE_SQL_DRIVER}}};"
                f"Server={settings.AZURE_SQL_SERVER};"
                f"Database={settings.AZURE_SQL_DATABASE};"
                f"Trusted_Connection=yes;"
                f"Encrypt=no;"
            )
        else:
            # Use SQL Authentication
            connection_string = (
                f"Driver={{{settings.AZURE_SQL_DRIVER}}};"
                f"Server=tcp:{settings.AZURE_SQL_SERVER},1433;"
                f"Database={settings.AZURE_SQL_DATABASE};"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
                f"Connection Timeout=30;"
            )

        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        raise Exception(f"Failed to connect to Azure SQL Database: {str(e)}")


def get_user_by_water_contract(water_contract: str) -> Optional[Dict]:
    """
    Retrieve user and water invoice information by water contract number.
    Supports both full format (3701455886 / 1014871) and partial (3701455886).
    
    Args:
        water_contract: Water Contract Number (full or partial)
        
    Returns:
        dict: Combined user and water invoice information or None if not found
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # SQL query with JOIN to get user + water invoice data
        # Supports partial matching by checking if the contract starts with the input
        query = """
            SELECT 
                u.user_id,
                u.name,
                u.address,
                u.phone,
                u.zone_id,
                w.water_contract_number,
                w.is_paid,
                w.outstanding_balance,
                w.last_payment_date,
                w.cut_status,
                w.cut_reason
            FROM dbo.water_invoices w
            INNER JOIN dbo.users u ON w.user_id = u.user_id
            WHERE w.water_contract_number = ? 
               OR w.water_contract_number LIKE ? + '%'
        """
        
        cursor.execute(query, (water_contract, water_contract))
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            conn.close()
            return None
        
        # Convert row to dictionary
        result = {
            'user_id': row.user_id,
            'name': row.name,
            'address': row.address,
            'phone': row.phone,
            'zone_id': row.zone_id,
            'water_contract_number': row.water_contract_number,
            'is_paid': bool(row.is_paid),
            'outstanding_balance': float(row.outstanding_balance) if row.outstanding_balance else 0.0,
            'last_payment_date': str(row.last_payment_date) if row.last_payment_date else None,
            'cut_status': row.cut_status,
            'cut_reason': row.cut_reason,
            'service_type': 'ماء'
        }
        
        cursor.close()
        conn.close()
        return result
        
    except Exception as e:
        print(f"Error querying water contract: {str(e)}")
        return None


def get_user_by_electricity_contract(electricity_contract: str) -> Optional[Dict]:
    """
    Retrieve user and electricity invoice information by electricity contract number.
    Supports both full format (4801566997 / 2025982) and partial (4801566997).
    
    Args:
        electricity_contract: Electricity Contract Number (full or partial)
        
    Returns:
        dict: Combined user and electricity invoice information or None if not found
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # SQL query with JOIN to get user + electricity invoice data
        # Supports partial matching by checking if the contract starts with the input
        query = """
            SELECT 
                u.user_id,
                u.name,
                u.address,
                u.phone,
                u.zone_id,
                e.electricity_contract_number,
                e.is_paid,
                e.outstanding_balance,
                e.last_payment_date,
                e.cut_status,
                e.cut_reason
            FROM dbo.electricity_invoices e
            INNER JOIN dbo.users u ON e.user_id = u.user_id
            WHERE e.electricity_contract_number = ? 
               OR e.electricity_contract_number LIKE ? + '%'
        """
        
        cursor.execute(query, (electricity_contract, electricity_contract))
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            conn.close()
            return None
        
        # Convert row to dictionary
        result = {
            'user_id': row.user_id,
            'name': row.name,
            'address': row.address,
            'phone': row.phone,
            'zone_id': row.zone_id,
            'electricity_contract_number': row.electricity_contract_number,
            'is_paid': bool(row.is_paid),
            'outstanding_balance': float(row.outstanding_balance) if row.outstanding_balance else 0.0,
            'last_payment_date': str(row.last_payment_date) if row.last_payment_date else None,
            'cut_status': row.cut_status,
            'cut_reason': row.cut_reason,
            'service_type': 'كهرباء'
        }
        
        cursor.close()
        conn.close()
        return result
        
    except Exception as e:
        print(f"Error querying electricity contract: {str(e)}")
        return None


def get_zone_by_id(zone_id: int) -> Optional[Dict]:
    """
    Retrieve zone/maintenance information by zone ID.
    
    Args:
        zone_id: Zone identification number
        
    Returns:
        dict: Zone information or None if not found
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # SQL query to get zone information
        query = """
            SELECT 
                zone_id,
                zone_name,
                maintenance_status,
                outage_reason,
                estimated_restoration,
                affected_services,
                status_updated
            FROM dbo.zones
            WHERE zone_id = ?
        """
        
        cursor.execute(query, (zone_id,))
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            conn.close()
            return None
        
        # Convert row to dictionary
        result = {
            'zone_id': row.zone_id,
            'zone_name': row.zone_name,
            'maintenance_status': row.maintenance_status,
            'outage_reason': row.outage_reason,
            'estimated_restoration': str(row.estimated_restoration) if row.estimated_restoration else None,
            'affected_services': row.affected_services,
            'status_updated': str(row.status_updated) if row.status_updated else None
        }
        
        cursor.close()
        conn.close()
        return result
        
    except Exception as e:
        print(f"Error querying zone: {str(e)}")
        return None


def test_connection() -> bool:
    """
    Test the database connection.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        print("✓ Azure SQL Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Azure SQL Database connection failed: {str(e)}")
        return False
