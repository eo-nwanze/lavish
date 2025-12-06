import sqlite3

# Check root database for additional tables
root_conn = sqlite3.connect('../../lavish_library.db')
root_cursor = root_conn.cursor()

root_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
all_tables = [t[0] for t in root_cursor.fetchall()]

print("All tables in root database:")
for table in all_tables:
    if 'location' in table.lower() or 'phone' in table.lower() or 'currency' in table.lower() or 'country' in table.lower():
        root_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = root_cursor.fetchone()[0]
        print(f"  - {table}: {count} records")

root_conn.close()
