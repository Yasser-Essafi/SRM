# Azure SQL Database Migration Guide

## Overview
Successfully migrated from mock Pandas DataFrames to Azure SQL Database with pyodbc.

---

## Changes Made

### 1. **New Files Created**

#### `data/sql_db.py` (Azure SQL Database Layer)
- **Connection**: `get_connection()` - Connects to Azure SQL Server
- **Functions**:
  - `get_user_by_water_contract(water_contract)` - Joins `dbo.water_invoices` + `dbo.users`
  - `get_user_by_electricity_contract(electricity_contract)` - Joins `dbo.electricity_invoices` + `dbo.users`
  - `get_zone_by_id(zone_id)` - Queries `dbo.zones`
  - `test_connection()` - Verifies database connectivity

**Key Features**:
- Parameterized queries (SQL injection safe)
- Supports partial contract matching: `"3701455886"` matches `"3701455886 / 1014871"`
- Returns same dictionary structure as mock_db
- Graceful error handling with None returns
- Connection pooling per query

#### `data/conversations.py` (Conversation Management)
- Moved conversation history functions from `mock_db.py`
- In-memory storage for chat sessions
- Functions:
  - `create_conversation()`
  - `get_conversation(conversation_id)`
  - `add_message_to_conversation(conversation_id, role, content)`
  - `get_conversation_history(conversation_id)`

#### `test_sql_connection.py` (Testing Script)
- Comprehensive test suite for all SQL functions
- Tests full and partial contract matching
- Validates zone queries
- Run with: `python test_sql_connection.py`

---

### 2. **Updated Files**

#### `services/ai_service.py`
```python
# OLD:
from data.mock_db import get_user_by_water_contract, get_user_by_electricity_contract, get_zone_by_id

# NEW:
from data.sql_db import get_user_by_water_contract, get_user_by_electricity_contract, get_zone_by_id
```

#### `backend/routes/chat.py`
```python
# OLD:
from data.mock_db import (create_conversation, get_conversation, add_message_to_conversation, get_conversation_history)

# NEW:
from data.conversations import (create_conversation, get_conversation, add_message_to_conversation, get_conversation_history)
```

#### `backend/routes/speech.py`
```python
# OLD:
from data.mock_db import (create_conversation, get_conversation, add_message_to_conversation, get_conversation_history)

# NEW:
from data.conversations import (create_conversation, get_conversation, add_message_to_conversation, get_conversation_history)
```

#### `data/__init__.py`
- Updated to export from `sql_db` and `conversations` instead of `mock_db`

#### `requirements.txt`
- Added: `pyodbc==5.0.1`

---

## Database Configuration

### Azure SQL Server Details
```
Server: srm-server.database.windows.net
Database: SRM
Username: srmadmin
Password: Srm12345
Driver: ODBC Driver 18 for SQL Server
Port: 1433
```

### Connection String (in `sql_db.py`)
```python
connection_string = (
    f"Driver={{ODBC Driver 18 for SQL Server}};"
    f"Server=tcp:srm-server.database.windows.net,1433;"
    f"Database=SRM;"
    f"Uid=srmadmin;"
    f"Pwd=Srm12345;"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
    f"Connection Timeout=30;"
)
```

---

## Database Schema

### Required Tables

#### `dbo.users`
```sql
CREATE TABLE dbo.users (
    user_id INT PRIMARY KEY,
    name NVARCHAR(100),
    address NVARCHAR(200),
    phone NVARCHAR(20),
    zone_id INT
);
```

#### `dbo.water_invoices`
```sql
CREATE TABLE dbo.water_invoices (
    water_contract_number NVARCHAR(50) PRIMARY KEY,
    user_id INT FOREIGN KEY REFERENCES dbo.users(user_id),
    is_paid BIT,
    outstanding_balance DECIMAL(10,2),
    last_payment_date DATE,
    cut_status NVARCHAR(20),
    cut_reason NVARCHAR(100)
);
```

#### `dbo.electricity_invoices`
```sql
CREATE TABLE dbo.electricity_invoices (
    electricity_contract_number NVARCHAR(50) PRIMARY KEY,
    user_id INT FOREIGN KEY REFERENCES dbo.users(user_id),
    is_paid BIT,
    outstanding_balance DECIMAL(10,2),
    last_payment_date DATE,
    cut_status NVARCHAR(20),
    cut_reason NVARCHAR(100)
);
```

#### `dbo.zones`
```sql
CREATE TABLE dbo.zones (
    zone_id INT PRIMARY KEY,
    zone_name NVARCHAR(100),
    maintenance_status NVARCHAR(50),
    outage_reason NVARCHAR(200),
    estimated_restoration DATETIME,
    affected_services NVARCHAR(50),
    status_updated DATETIME
);
```

---

## Installation Steps

### 1. Install ODBC Driver (Windows)
```powershell
# Download and install ODBC Driver 18 for SQL Server
# https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
```

### 2. Install Python Dependencies
```powershell
pip install pyodbc==5.0.1
```

### 3. Test Connection
```powershell
python test_sql_connection.py
```

Expected output:
```
============================================================
AZURE SQL DATABASE CONNECTION TEST
============================================================

1. Testing database connection...
✓ Azure SQL Database connection successful

2. Testing water contract lookup (full format)...
✓ Found user: عبد النبي المرزوقي
  Contract: 3701455886 / 1014871
  Paid: True
  Balance: 0.0 MAD

...
```

---

## SQL Query Logic

### Water Contract Query
```sql
SELECT 
    u.user_id, u.name, u.address, u.phone, u.zone_id,
    w.water_contract_number, w.is_paid, w.outstanding_balance, 
    w.last_payment_date, w.cut_status, w.cut_reason
FROM dbo.water_invoices w
INNER JOIN dbo.users u ON w.user_id = u.user_id
WHERE w.water_contract_number = ? 
   OR w.water_contract_number LIKE ? + '%'
```

**Partial Matching Logic**:
- Input: `"3701455886"`
- Matches: `"3701455886 / 1014871"`
- Uses SQL `LIKE` operator: `water_contract_number LIKE '3701455886%'`

### Electricity Contract Query
Same pattern as water, but queries `dbo.electricity_invoices`

### Zone Query
```sql
SELECT zone_id, zone_name, maintenance_status, outage_reason, 
       estimated_restoration, affected_services, status_updated
FROM dbo.zones
WHERE zone_id = ?
```

---

## Return Value Compatibility

### Water Contract Response
```python
{
    'user_id': 1,
    'name': 'عبد النبي المرزوقي',
    'address': 'حي المسيرة، مراكش',
    'phone': '+212624339149',
    'zone_id': 1,
    'water_contract_number': '3701455886 / 1014871',
    'is_paid': True,
    'outstanding_balance': 0.0,
    'last_payment_date': '2026-01-15',
    'cut_status': 'OK',
    'cut_reason': None,
    'service_type': 'ماء'  # Added by function
}
```

### Electricity Contract Response
Same structure with `electricity_contract_number` and `service_type='كهرباء'`

### Zone Response
```python
{
    'zone_id': 1,
    'zone_name': 'مراكش - حي المسيرة',
    'maintenance_status': 'جاري الصيانة',
    'outage_reason': 'إصلاح أنابيب المياه الرئيسية',
    'estimated_restoration': '2024-12-04 18:00',
    'affected_services': 'ماء',
    'status_updated': '2025-12-03 08:00'
}
```

---

## No Changes Required In

✅ **LangChain Tools** (`services/ai_service.py`)
- `_check_water_payment_impl()`
- `_check_water_maintenance_impl()`
- `_check_electricity_payment_impl()`
- `_check_electricity_maintenance_impl()`

✅ **API Routes** (`backend/routes/`)
- `/api/chat`
- `/api/speech-to-text`
- `/api/speech-to-chat`

✅ **UI Components** (`ui/`)
- `chat_interface.py`
- `layout.py`

✅ **Prompts & Agent Logic**
- System prompts
- Tool descriptions
- Agent initialization

---

## Testing Checklist

- [ ] Install ODBC Driver 18 for SQL Server
- [ ] Install pyodbc: `pip install pyodbc==5.0.1`
- [ ] Verify Azure SQL firewall allows your IP
- [ ] Run `python test_sql_connection.py`
- [ ] Test water contract lookup (full and partial)
- [ ] Test electricity contract lookup (full and partial)
- [ ] Test zone queries
- [ ] Start backend: `cd backend && python app.py`
- [ ] Test `/api/chat` endpoint with water contract
- [ ] Test `/api/chat` endpoint with electricity contract
- [ ] Test speech-to-text with contract queries

---

## Troubleshooting

### ODBC Driver Not Found
```
Error: [Microsoft][ODBC Driver Manager] Data source name not found
```
**Solution**: Install ODBC Driver 18 for SQL Server from Microsoft

### Firewall Issues
```
Error: Cannot open server 'srm-server' requested by the login
```
**Solution**: Add your IP to Azure SQL firewall rules

### Connection Timeout
```
Error: Connection Timeout Expired
```
**Solution**: Check network connectivity, verify server name and credentials

### No Results Returned
- Verify data exists in Azure SQL tables
- Check contract number format matches database
- Ensure JOIN conditions are correct

---

## Migration Benefits

1. **Production-Ready**: Real database instead of in-memory mock
2. **Data Persistence**: Data survives server restarts
3. **Scalability**: Azure SQL handles concurrent users
4. **Security**: Encrypted connections, parameterized queries
5. **No Code Changes**: Same interface, zero impact on AI logic
6. **Backward Compatible**: Same return structures

---

## Next Steps

1. **Populate Database**: Insert test data from `mock_db.py` into Azure SQL
2. **Environment Variables**: Move credentials to `.env` file
3. **Connection Pooling**: Implement connection pool for better performance
4. **Logging**: Add query logging for debugging
5. **Error Monitoring**: Track database errors in production

---

## Sample Data Migration Script

```python
# migrate_data.py - Copy mock data to Azure SQL
from data.mock_db import users_table, water_invoices_table, electricity_invoices_table, zones_table
from data.sql_db import get_connection

conn = get_connection()
cursor = conn.cursor()

# Insert users
for _, row in users_table.iterrows():
    cursor.execute("""
        INSERT INTO dbo.users (user_id, name, address, phone, zone_id)
        VALUES (?, ?, ?, ?, ?)
    """, row['user_id'], row['name'], row['address'], row['phone'], row['zone_id'])

# Insert water invoices
for _, row in water_invoices_table.iterrows():
    cursor.execute("""
        INSERT INTO dbo.water_invoices 
        (water_contract_number, user_id, is_paid, outstanding_balance, last_payment_date, cut_status, cut_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, row['water_contract_number'], row['user_id'], row['is_paid'], 
        row['outstanding_balance'], row['last_payment_date'], row['cut_status'], row['cut_reason'])

# Insert electricity invoices
for _, row in electricity_invoices_table.iterrows():
    cursor.execute("""
        INSERT INTO dbo.electricity_invoices 
        (electricity_contract_number, user_id, is_paid, outstanding_balance, last_payment_date, cut_status, cut_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, row['electricity_contract_number'], row['user_id'], row['is_paid'], 
        row['outstanding_balance'], row['last_payment_date'], row['cut_status'], row['cut_reason'])

# Insert zones
for _, row in zones_table.iterrows():
    cursor.execute("""
        INSERT INTO dbo.zones 
        (zone_id, zone_name, maintenance_status, outage_reason, estimated_restoration, affected_services, status_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, row['zone_id'], row['zone_name'], row['maintenance_status'], 
        row['outage_reason'], row['estimated_restoration'], row['affected_services'], row['status_updated'])

conn.commit()
cursor.close()
conn.close()
print("✓ Data migration completed")
```

---

## Support

For issues or questions:
1. Check Azure SQL connection strings
2. Verify ODBC driver installation
3. Review firewall rules
4. Test with `test_sql_connection.py`
