"""
Script to copy location data from root database to backend database
"""
import sqlite3
import os

# Database paths
root_db = '../../lavish_library.db'
backend_db = 'lavish_library.db'

print("="*80)
print("COPYING LOCATION DATA FROM ROOT DB TO BACKEND DB")
print("="*80)

# Connect to both databases
root_conn = sqlite3.connect(root_db)
backend_conn = sqlite3.connect(backend_db)

root_cursor = root_conn.cursor()
backend_cursor = backend_conn.cursor()

try:
    # 1. Copy Countries
    print("\n1. Copying countries...")
    root_cursor.execute("SELECT * FROM locations_country")
    countries = root_cursor.fetchall()
    
    if countries:
        # Get column names
        root_cursor.execute("PRAGMA table_info(locations_country)")
        columns = [col[1] for col in root_cursor.fetchall()]
        placeholders = ','.join(['?' for _ in columns])
        columns_str = ','.join(columns)
        
        # Clear existing data
        backend_cursor.execute("DELETE FROM locations_country")
        
        # Insert data
        for country in countries:
            backend_cursor.execute(f"INSERT INTO locations_country ({columns_str}) VALUES ({placeholders})", country)
        
        print(f"   ✓ Copied {len(countries)} countries")
    else:
        print("   ⚠ No countries found in source database")
    
    # 2. Copy States
    print("\n2. Copying states...")
    root_cursor.execute("SELECT * FROM locations_state")
    states = root_cursor.fetchall()
    
    if states:
        root_cursor.execute("PRAGMA table_info(locations_state)")
        columns = [col[1] for col in root_cursor.fetchall()]
        placeholders = ','.join(['?' for _ in columns])
        columns_str = ','.join(columns)
        
        backend_cursor.execute("DELETE FROM locations_state")
        
        for state in states:
            backend_cursor.execute(f"INSERT INTO locations_state ({columns_str}) VALUES ({placeholders})", state)
        
        print(f"   ✓ Copied {len(states)} states")
    else:
        print("   ⚠ No states found in source database")
    
    # 3. Copy Cities
    print("\n3. Copying cities...")
    root_cursor.execute("SELECT * FROM locations_city")
    cities = root_cursor.fetchall()
    
    if cities:
        root_cursor.execute("PRAGMA table_info(locations_city)")
        columns = [col[1] for col in root_cursor.fetchall()]
        placeholders = ','.join(['?' for _ in columns])
        columns_str = ','.join(columns)
        
        backend_cursor.execute("DELETE FROM locations_city")
        
        for city in cities:
            backend_cursor.execute(f"INSERT INTO locations_city ({columns_str}) VALUES ({placeholders})", city)
        
        print(f"   ✓ Copied {len(cities)} cities")
    else:
        print("   ⚠ No cities found in source database")
    
    # 4. Copy Locations (if exists)
    print("\n4. Copying locations...")
    try:
        root_cursor.execute("SELECT * FROM locations_location")
        locations = root_cursor.fetchall()
        
        if locations:
            root_cursor.execute("PRAGMA table_info(locations_location)")
            columns = [col[1] for col in root_cursor.fetchall()]
            placeholders = ','.join(['?' for _ in columns])
            columns_str = ','.join(columns)
            
            backend_cursor.execute("DELETE FROM locations_location")
            
            for location in locations:
                backend_cursor.execute(f"INSERT INTO locations_location ({columns_str}) VALUES ({placeholders})", location)
            
            print(f"   ✓ Copied {len(locations)} locations")
        else:
            print("   ⚠ No locations found in source database")
    except sqlite3.OperationalError as e:
        print(f"   ⚠ locations_location table not found or error: {e}")
    
    # Commit all changes
    backend_conn.commit()
    
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    
    # Verify the copy
    backend_cursor.execute("SELECT COUNT(*) FROM locations_country")
    country_count = backend_cursor.fetchone()[0]
    print(f"Countries in backend DB: {country_count}")
    
    backend_cursor.execute("SELECT COUNT(*) FROM locations_state")
    state_count = backend_cursor.fetchone()[0]
    print(f"States in backend DB: {state_count}")
    
    backend_cursor.execute("SELECT COUNT(*) FROM locations_city")
    city_count = backend_cursor.fetchone()[0]
    print(f"Cities in backend DB: {city_count}")
    
    try:
        backend_cursor.execute("SELECT COUNT(*) FROM locations_location")
        location_count = backend_cursor.fetchone()[0]
        print(f"Locations in backend DB: {location_count}")
    except:
        pass
    
    print("\n" + "="*80)
    print("✓ LOCATION DATA COPY COMPLETED SUCCESSFULLY")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    backend_conn.rollback()
    raise

finally:
    # Close connections
    root_conn.close()
    backend_conn.close()
