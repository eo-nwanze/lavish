#!/usr/bin/env python
"""
Verify migrated data
"""
import sqlite3
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lavish_backend.settings')
django.setup()

def verify_migration():
    """Verify the migrated data"""
    
    print('🔍 Verifying migrated data after migration...')
    
    # Check fulfillment orders
    print('\n📊 Fulfillment Orders:')
    try:
        from shipping.models import ShopifyFulfillmentOrder
        fulfillment_count = ShopifyFulfillmentOrder.objects.count()
        print(f'  ShopifyFulfillmentOrder: {fulfillment_count} records')
    except Exception as e:
        print(f'  Error: {e}')
    
    # Check increased data
    print('\n📊 Increased data counts:')
    try:
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.admin.models import LogEntry
        from django.contrib.sessions.models import Session
        from email_manager.models import EmailHistory
        
        print(f'  Permissions: {Permission.objects.count()}')
        print(f'  Content Types: {ContentType.objects.count()}')
        print(f'  Admin Logs: {LogEntry.objects.count()}')
        print(f'  Sessions: {Session.objects.count()}')
        print(f'  Email History: {EmailHistory.objects.count()}')
    except Exception as e:
        print(f'  Error checking Django models: {e}')
    
    # Check if new tables exist in database
    print('\n📊 Database table check:')
    try:
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
        
        conn.close()
    except Exception as e:
        print(f'  Error checking database: {e}')
    
    print('\n🎉 Verification complete!')

if __name__ == '__main__':
    verify_migration()