import os
import pyodbc
import pandas as pd 
from data.mock_db import users_table, water_invoices_table, electricity_invoices_table, zones_table 
from config.settings import settings

def get_connection():
    """Establish a connection to the Azure SQL Database."""
    try:
        conn_str = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server={settings.AZURE_SQL_SERVER};"
            f"Database={settings.AZURE_SQL_DATABASE};"
            f"Uid={settings.AZURE_SQL_USERNAME};"
            f"Pwd={settings.AZURE_SQL_PASSWORD};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
        )
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return None
def main():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    IF OBJECT_ID('users', 'U') IS NOT NULL DROP TABLE users;
    CREATE TABLE users (
        user_id INT PRIMARY KEY,
        name NVARCHAR(100),
        address NVARCHAR(200),
        phone NVARCHAR(20),
        zone_id INT
    );
    """)
    cursor.execute("""
    IF OBJECT_ID('water_invoices', 'U') IS NOT NULL DROP TABLE water_invoices;
    CREATE TABLE water_invoices (
        water_contract_number NVARCHAR(50) PRIMARY KEY,
        user_id INT,
        is_paid BIT,
        outstanding_balance DECIMAL(10,2),
        last_payment_datetime NVARCHAR(30),
        last_payment_date NVARCHAR(20),
        cut_status NVARCHAR(20),
        cut_reason NVARCHAR(100)
    );
    """)
    cursor.execute("""
    IF OBJECT_ID('electricity_invoices', 'U') IS NOT NULL DROP TABLE electricity_invoices;
    CREATE TABLE electricity_invoices (
        electricity_contract_number NVARCHAR(50) PRIMARY KEY,
        user_id INT,
        is_paid BIT,
        outstanding_balance DECIMAL(10,2),
        last_payment_datetime NVARCHAR(30),
        last_payment_date NVARCHAR(20),
        cut_status NVARCHAR(20),
        cut_reason NVARCHAR(100)
    );
    """)
    
    cursor.execute("""
    IF OBJECT_ID('zones', 'U') IS NOT NULL DROP TABLE zones;
    CREATE TABLE zones (
        zone_id INT PRIMARY KEY,
        zone_name NVARCHAR(100),
        maintenance_status NVARCHAR(50),
        outage_reason NVARCHAR(200),
        estimated_restoration NVARCHAR(30),
        affected_services NVARCHAR(50),
        status_updated NVARCHAR(30)
    );
    """)
    conn.commit()

    # Insert users
    for _, row in users_table.iterrows():
        cursor.execute("""
            INSERT INTO users (user_id, name, address, phone, zone_id)
            VALUES (?, ?, ?, ?, ?)
        """, row['user_id'], row['name'], row['address'], row['phone'], row['zone_id'])

    # Insert water invoices
    for _, row in water_invoices_table.iterrows():
        cursor.execute("""
            INSERT INTO water_invoices
            (water_contract_number, user_id, is_paid, outstanding_balance, last_payment_datetime, last_payment_date, cut_status, cut_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, row['water_contract_number'], row['user_id'], row['is_paid'], row['outstanding_balance'],
             row['last_payment_datetime'], row['last_payment_date'], row['cut_status'], row['cut_reason'])

    # Insert electricity invoices
    for _, row in electricity_invoices_table.iterrows():
        cursor.execute("""
            INSERT INTO electricity_invoices
            (electricity_contract_number, user_id, is_paid, outstanding_balance, last_payment_datetime, last_payment_date, cut_status, cut_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, row['electricity_contract_number'], row['user_id'], row['is_paid'], row['outstanding_balance'],
             row['last_payment_datetime'], row['last_payment_date'], row['cut_status'], row['cut_reason'])

    # Insert zones
    for _, row in zones_table.iterrows():
        cursor.execute("""
            INSERT INTO zones
            (zone_id, zone_name, maintenance_status, outage_reason, estimated_restoration, affected_services, status_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, row['zone_id'], row['zone_name'], row['maintenance_status'], row['outage_reason'],
             row['estimated_restoration'], row['affected_services'], row['status_updated'])
    conn.commit()
    cursor.close()
    conn.close()
    print("All tables created and data inserted successfully!")

if __name__ == "__main__":
    main()