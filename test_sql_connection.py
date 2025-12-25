"""
Test script for Azure SQL Database connection.
Verifies that all database functions work correctly.
"""
from data.sql_db import (
    test_connection,
    get_user_by_water_contract,
    get_user_by_electricity_contract,
    get_zone_by_id
)


def test_all_functions():
    """Test all SQL database functions."""
    
    print("\n" + "="*60)
    print("AZURE SQL DATABASE CONNECTION TEST")
    print("="*60 + "\n")
    
    # Test 1: Connection
    print("1. Testing database connection...")
    if not test_connection():
        print("❌ Connection failed. Check credentials and network.")
        return
    print()
    
    # Test 2: Water contract lookup (full format)
    print("2. Testing water contract lookup (full format)...")
    water_user = get_user_by_water_contract("3701455886 / 1014871")
    if water_user:
        print(f"✓ Found user: {water_user['name']}")
        print(f"  Contract: {water_user['water_contract_number']}")
        print(f"  Paid: {water_user['is_paid']}")
        print(f"  Balance: {water_user['outstanding_balance']} MAD")
    else:
        print("✗ Water contract not found")
    print()
    
    # Test 3: Water contract lookup (partial format)
    print("3. Testing water contract lookup (partial format)...")
    water_user_partial = get_user_by_water_contract("3701455886")
    if water_user_partial:
        print(f"✓ Found user: {water_user_partial['name']}")
        print(f"  Contract: {water_user_partial['water_contract_number']}")
    else:
        print("✗ Partial water contract not found")
    print()
    
    # Test 4: Electricity contract lookup (full format)
    print("4. Testing electricity contract lookup (full format)...")
    elec_user = get_user_by_electricity_contract("4801566997 / 2025982")
    if elec_user:
        print(f"✓ Found user: {elec_user['name']}")
        print(f"  Contract: {elec_user['electricity_contract_number']}")
        print(f"  Paid: {elec_user['is_paid']}")
        print(f"  Balance: {elec_user['outstanding_balance']} MAD")
    else:
        print("✗ Electricity contract not found")
    print()
    
    # Test 5: Electricity contract lookup (partial format)
    print("5. Testing electricity contract lookup (partial format)...")
    elec_user_partial = get_user_by_electricity_contract("4801566997")
    if elec_user_partial:
        print(f"✓ Found user: {elec_user_partial['name']}")
        print(f"  Contract: {elec_user_partial['electricity_contract_number']}")
    else:
        print("✗ Partial electricity contract not found")
    print()
    
    # Test 6: Zone lookup
    print("6. Testing zone lookup...")
    zone = get_zone_by_id(1)
    if zone:
        print(f"✓ Found zone: {zone['zone_name']}")
        print(f"  Status: {zone['maintenance_status']}")
        print(f"  Affected services: {zone['affected_services']}")
        if zone['outage_reason']:
            print(f"  Reason: {zone['outage_reason']}")
    else:
        print("✗ Zone not found")
    print()
    
    # Test 7: Non-existent contract
    print("7. Testing non-existent contract...")
    no_user = get_user_by_water_contract("9999999999")
    if no_user is None:
        print("✓ Correctly returned None for non-existent contract")
    else:
        print("✗ Should return None for non-existent contract")
    print()
    
    print("="*60)
    print("TEST COMPLETED")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_all_functions()
