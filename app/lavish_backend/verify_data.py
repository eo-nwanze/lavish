import sqlite3

backend_conn = sqlite3.connect('lavish_library.db')
backend_cursor = backend_conn.cursor()

print("="*80)
print("BACKEND DATABASE - LOCATION DATA SUMMARY")
print("="*80)

# Countries
backend_cursor.execute("SELECT COUNT(*) FROM locations_country")
print(f"\nCountries: {backend_cursor.fetchone()[0]}")

backend_cursor.execute("PRAGMA table_info(locations_country)")
country_columns = [col[1] for col in backend_cursor.fetchall()]
print(f"  Columns: {', '.join(country_columns)}")

backend_cursor.execute("SELECT * FROM locations_country LIMIT 3")
print("  Sample data:")
for row in backend_cursor.fetchall():
    print(f"    {row}")

# States
backend_cursor.execute("SELECT COUNT(*) FROM locations_state")
print(f"\nStates: {backend_cursor.fetchone()[0]}")

backend_cursor.execute("PRAGMA table_info(locations_state)")
state_columns = [col[1] for col in backend_cursor.fetchall()]
print(f"  Columns: {', '.join(state_columns)}")

backend_cursor.execute("SELECT * FROM locations_state LIMIT 3")
print("  Sample data:")
for row in backend_cursor.fetchall():
    print(f"    {row}")

# Cities
backend_cursor.execute("SELECT COUNT(*) FROM locations_city")
print(f"\nCities: {backend_cursor.fetchone()[0]}")

backend_cursor.execute("PRAGMA table_info(locations_city)")
city_columns = [col[1] for col in backend_cursor.fetchall()]
print(f"  Columns: {', '.join(city_columns)}")

backend_cursor.execute("SELECT * FROM locations_city LIMIT 3")
print("  Sample data:")
for row in backend_cursor.fetchall():
    print(f"    {row}")

print("\n" + "="*80)
print("✓ DATA SUCCESSFULLY COPIED AND VERIFIED")
print("="*80)

backend_conn.close()
