# SRM Database Refactoring Documentation

## Overview
This document describes the major refactoring of the SRM chatbot system to support separate water and electricity contracts.

## Date
December 11, 2025

## Changes Summary

### 1. Database Structure Refactoring

#### Previous Structure (Single Table)
- **users_table**: Combined user info with single contract field
  - Fields: contract, name, address, phone, service_type, zone_id, payment_status, last_payment_date, outstanding_balance, service_status

#### New Structure (Three Tables)

**A) users_table**
- Purpose: Generic user information
- Fields:
  - `user_id` (int): Unique user identifier
  - `name` (str): Customer name
  - `address` (str): Customer address
  - `phone` (str): Contact number
  - `zone_id` (int): Zone identifier for maintenance info

**B) water_invoices_table**
- Purpose: Water service contracts and payment information
- Fields:
  - `water_contract_number` (str): Format "3701XXXXXX / XXXXXXX" (starts with 3701)
  - `user_id` (int): References users_table
  - `is_paid` (bool): Payment status
  - `outstanding_balance` (float): Amount due in MAD
  - `last_payment_date` (str): Date of last payment
  - `cut_status` (str): "OK" or "CUT_OFF"
  - `cut_reason` (str): Reason for service interruption

**C) electricity_invoices_table**
- Purpose: Electricity service contracts and payment information
- Fields:
  - `electricity_contract_number` (str): Format "4801XXXXXX / XXXXXXX" (starts with 4801)
  - `user_id` (int): References users_table
  - `is_paid` (bool): Payment status
  - `outstanding_balance` (float): Amount due in MAD
  - `last_payment_date` (str): Date of last payment
  - `cut_status` (str): "OK" or "CUT_OFF"
  - `cut_reason` (str): Reason for service interruption

**D) zones_table** (Unchanged structure, updated logic)
- Purpose: Maintenance and outage information by geographic zone
- Fields remain the same but now linked more granularly to service types

### 2. Database Functions Refactoring

#### Previous Functions
- `get_user_by_contract(contract)` - Single lookup function

#### New Functions

**data/mock_db.py:**
```python
def get_user_by_water_contract(water_contract: str) -> Optional[dict]:
    """
    Retrieve user and water invoice information by water contract number.
    Supports both full format (3701455886 / 1014871) and partial (3701455886).
    Returns: Combined dict with user info + water invoice data
    """

def get_user_by_electricity_contract(electricity_contract: str) -> Optional[dict]:
    """
    Retrieve user and electricity invoice information by electricity contract number.
    Supports both full format (4801566997 / 2025982) and partial (4801566997).
    Returns: Combined dict with user info + electricity invoice data
    """

def get_all_water_invoices() -> pd.DataFrame:
    """Get all water invoices from the database."""

def get_all_electricity_invoices() -> pd.DataFrame:
    """Get all electricity invoices from the database."""
```

### 3. AI Service Refactoring

#### Previous Tools
- `check_payment(contract)` - Single payment check
- `check_maintenance(contract)` - Single maintenance check

#### New Tools

**services/ai_service.py:**
```python
# Water-specific tools
@tool
def check_water_payment(water_contract: str) -> str:
    """Check water payment status and outstanding balance"""

@tool
def check_water_maintenance(water_contract: str) -> str:
    """Check for water maintenance and outages in customer's zone"""

# Electricity-specific tools
@tool
def check_electricity_payment(electricity_contract: str) -> str:
    """Check electricity payment status and outstanding balance"""

@tool
def check_electricity_maintenance(electricity_contract: str) -> str:
    """Check for electricity maintenance and outages in customer's zone"""
```

### 4. Chatbot Behavior Updates

#### New Conversation Flow

**A) Water Issue Detected:**
1. AI detects water problem from customer message
2. AI asks for WATER contract number (3701XXXXXX / XXXXXXX)
3. AI uses `check_water_payment()` and `check_water_maintenance()`
4. AI explains water service status clearly

**B) Electricity Issue Detected:**
1. AI detects electricity problem from customer message
2. AI asks for ELECTRICITY contract number (4801XXXXXX / XXXXXXX)
3. AI uses `check_electricity_payment()` and `check_electricity_maintenance()`
4. AI explains electricity service status clearly

**C) Both Issues Detected:**
1. AI handles SEQUENTIALLY:
   - First: Ask for water contract → check water → explain water
   - Then: Ask for electricity contract → check electricity → explain electricity
2. Each service is addressed completely before moving to the next

#### Updated System Prompt Features
- **Automatic Problem Detection**: Identifies water/electricity/both from customer message
- **Contract Format Awareness**: 
  - Water: 3701XXXXXX / XXXXXXX
  - Electricity: 4801XXXXXX / XXXXXXX
- **Sequential Handling**: When both services have issues, handle one at a time
- **Service-Specific Responses**: Only discuss the service the customer asked about
- **Contract-Specific Queries**: Uses appropriate tool based on contract type

### 5. OCR Service Updates

#### Previous Function
```python
def extract_contract_from_image(image_bytes: bytes) -> Optional[str]:
    """Returns single contract number"""
```

#### New Function
```python
def extract_contract_from_image(image_bytes: bytes) -> Optional[Dict[str, str]]:
    """
    Returns: {
        'water_contract': str or None,
        'electricity_contract': str or None
    }
    Detects both contract types from a single bill image
    """
```

#### New OCR Patterns
- Water pattern: `r'(3701\d{6})\s*/\s*(\d{7})'`
- Electricity pattern: `r'(4801\d{6})\s*/\s*(\d{7})'`
- Supports multilingual labels (ماء، eau, water, كهرباء، électricité, electricity)

### 6. API Endpoint Updates

#### POST /api/ocr/extract-contract

**Previous Response:**
```json
{
  "contract": "3701455886 / 1014871",
  "status": "success"
}
```

**New Response:**
```json
{
  "water_contract": "3701455886 / 1014871",
  "electricity_contract": "4801566997 / 2025982",
  "status": "success"
}
```

### 7. UI Updates

#### chat_interface.py
- Updated welcome message to explain both contract types
- Modified OCR extraction to handle both water and electricity contracts
- Displays separate lines for water and electricity contracts when extracted

#### layout.py
- Updated usage instructions to explain contract format differences
- Added comprehensive test contract numbers for both services:
  - Water contracts: 3701XXXXXX (4 examples)
  - Electricity contracts: 4801XXXXXX (4 examples)
- Shows which test accounts have payment issues vs maintenance issues

### 8. Sample Test Data

#### Water Contracts
| Contract | User | Status | Cut Status | Notes |
|----------|------|--------|------------|-------|
| 3701455886 / 1014871 | Abdenbi | Paid | OK | Zone has water maintenance |
| 3701455887 / 1014872 | Ahmed | Paid | OK | No issues |
| 3701455888 / 1014873 | محمد | Paid | OK | No issues |
| 3701455890 / 1014875 | يوسف | Unpaid | CUT_OFF | Non-payment |

#### Electricity Contracts
| Contract | User | Status | Cut Status | Notes |
|----------|------|--------|------------|-------|
| 4801566997 / 2025982 | Abdenbi | Paid | OK | No issues |
| 4801566998 / 2025983 | محمد | Paid | OK | No issues |
| 4801566999 / 2025984 | خديجة | Paid | OK | Zone has electricity maintenance |
| 4801567001 / 2025986 | يوسف | Unpaid | CUT_OFF | Non-payment |

### 9. Technical Implementation Details

#### Partial Contract Matching
Both water and electricity lookup functions support partial matching:
- Full: "3701455886 / 1014871" → Exact match
- Partial: "3701455886" → Matches first part using `str.split(' / ').str[0]`

#### Data Joining
The `get_user_by_water_contract()` and `get_user_by_electricity_contract()` functions automatically join:
- User information (name, address, phone, zone_id)
- Invoice information (contract, payment status, cut status)
- Returns unified dictionary with all relevant fields

#### Error Handling
New error codes:
- `WATER_CONTRACT_NOT_FOUND:{contract}` - Water contract not in database
- `ELECTRICITY_CONTRACT_NOT_FOUND:{contract}` - Electricity contract not in database
- `ZONE_NOT_FOUND` - Zone information missing (unchanged)

### 10. Migration Notes

#### Breaking Changes
1. **Database schema changed** - Old single contract field split into separate tables
2. **Function signatures changed** - `get_user_by_contract()` replaced with service-specific functions
3. **Tool names changed** - `check_payment()` → `check_water_payment()` / `check_electricity_payment()`
4. **OCR return type changed** - From `str` to `Dict[str, str]`

#### Backward Compatibility
- Partial contract matching maintained for easier user input
- Language support (ar, en, fr) unchanged
- Plain text formatting rules unchanged
- Technical support number unchanged (05-22-XX-XX-XX)

### 11. Testing Recommendations

1. **Test water-only scenarios:**
   - User reports water issue
   - Provide water contract number
   - Verify water-specific tools are used
   - Check response only mentions water

2. **Test electricity-only scenarios:**
   - User reports electricity issue
   - Provide electricity contract number
   - Verify electricity-specific tools are used
   - Check response only mentions electricity

3. **Test both-services scenarios:**
   - User reports both issues
   - Verify sequential handling (water first, then electricity)
   - Check both contracts are requested separately
   - Verify complete explanation for each service

4. **Test OCR extraction:**
   - Upload bill with water contract only
   - Upload bill with electricity contract only
   - Upload bill with both contracts
   - Verify correct extraction and parsing

5. **Test edge cases:**
   - Partial contract numbers (10 digits only)
   - Mixed language input
   - Payment current but service interrupted (local technical issue)
   - Wrong contract format provided

### 12. Future Enhancements

Potential improvements to consider:
1. Database persistence (replace Pandas with SQL database)
2. Support for joint water+electricity bills
3. Historical payment tracking
4. Service interruption notifications
5. Multi-location support for customers with multiple properties
6. Payment integration (direct payment through chatbot)

## Files Modified

### Core Files
- ✅ `data/mock_db.py` - Complete database restructure
- ✅ `data/__init__.py` - Updated exports
- ✅ `services/ai_service.py` - New tools and logic
- ✅ `services/ocr_service.py` - Dual contract extraction
- ✅ `backend/routes/ocr.py` - Updated API response

### UI Files
- ✅ `ui/chat_interface.py` - Welcome message and OCR handling
- ✅ `ui/layout.py` - Instructions and test data

### No Changes Required
- ✅ `config/settings.py` - No changes needed
- ✅ `backend/routes/chat.py` - Works with new structure
- ✅ `ui/main.py` - No changes needed
- ✅ `backend/app.py` - No changes needed

## Validation Checklist

- [x] Database tables created with proper schema
- [x] Lookup functions working for both services
- [x] AI tools defined for water and electricity separately
- [x] System prompt updated with new conversation flow
- [x] OCR extracts both contract types
- [x] API endpoint returns both contracts
- [x] UI displays correct information
- [x] Test data available for both services
- [x] Error handling implemented
- [x] Documentation complete

## Conclusion

This refactoring successfully separates water and electricity services into distinct contracts while maintaining the chatbot's core functionality. The system now provides more accurate, service-specific assistance to customers and can handle complex scenarios where both services are affected.

The sequential handling of multiple issues ensures clarity and prevents confusion, while the separate contract numbers allow for precise tracking and status checking for each utility service.
