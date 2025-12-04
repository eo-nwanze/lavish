#!/usr/bin/env python
"""
Verify migrated data using direct database queries
"""
import sqlite3
import os

def verify_migration():
    """Verify the migrated data"""
    
    print('🔍 Verifying migrated data after migration...')
    
    # Check if new tables exist in database
    print('\n📊 Database table check:')
    conn = sqlite3.connect('lavish_library.db')
    cursor = conn.cursor()
    
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    
    # Look for the new tables
    new_tables = ['shipping_fulfillmenttrackinginfo', 'shipping_shippingrate']
    for table_name in new_tables:
        if any(table_name in table[0] for table in tables):
            print(f'  ✅ {table_name}: Found')
            
            # Get row count
            try:
                count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                print(f'    Rows: {count}')
            except Exception as e:
                print(f'    Error getting count: {e}')
        else:
            print(f'  ❌ {table_name}: Not found')
    
    # Check some key tables
    key_tables = ['shipping_shopifyfulfillmentorder', 'email_manager_emailhistory', 'django_session']
    print('\n📊 Key tables row counts:')
    for table_name in key_tables:
        try:
            count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f'  {table_name}: {count} rows')
        except Exception as e:
            print(f'  {table_name}: Error - {e}')
    
    # Show total table count
    print(f'\n📊 Total tables: {len(tables)}')
    
    conn.close()
    
    print('\n🎉 Verification complete!')

if __name__ == '__main__':
    verify_migration()