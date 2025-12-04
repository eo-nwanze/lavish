#!/usr/bin/env python
"""
Compare databases and migrate differences
"""
import sqlite3
import os
import sys

def compare_databases():
    """Compare current database with updated database"""
    
    # Path to both databases
    current_db = 'lavish_library.db'
    updated_db = '../../lavish_library (1).db'
    
    print('🔍 Comparing databases...')
    print(f'Current database: {os.path.abspath(current_db)}')
    print(f'Updated database: {os.path.abspath(updated_db)}')
    
    if not os.path.exists(updated_db):
        print(f'❌ Updated database not found: {updated_db}')
        return
    
    # Connect to both databases
    current_conn = sqlite3.connect(current_db)
    updated_conn = sqlite3.connect(updated_db)
    
    # Get table names from both databases
    current_tables = current_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    updated_tables = updated_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    
    current_table_names = {table[0] for table in current_tables}
    updated_table_names = {table[0] for table in updated_tables}
    
    print(f'\n📊 Current database tables: {len(current_table_names)}')
    print(f'📊 Updated database tables: {len(updated_table_names)}')
    
    # Find tables only in updated database
    new_tables = updated_table_names - current_table_names
    if new_tables:
        print(f'\n🆕 New tables in updated database: {new_tables}')
    else:
        print('\n✅ No new tables found')
    
    # Find tables only in current database
    removed_tables = current_table_names - updated_table_names
    if removed_tables:
        print(f'\n🗑️ Tables removed in updated database: {removed_tables}')
    else:
        print('\n✅ No tables removed')
    
    # Compare common tables
    common_tables = current_table_names & updated_table_names
    print(f'\n📋 Comparing {len(common_tables)} common tables...')
    
    differences = []
    for table_name in common_tables:
        # Get row counts
        current_count = current_conn.execute(f'SELECT COUNT(*) FROM {table_name}').fetchone()[0]
        updated_count = updated_conn.execute(f'SELECT COUNT(*) FROM {table_name}').fetchone()[0]
        
        if current_count != updated_count:
            differences.append({
                'table': table_name,
                'current_count': current_count,
                'updated_count': updated_count,
                'diff': updated_count - current_count
            })
    
    if differences:
        print('\n📊 Table row count differences:')
        for diff in differences:
            print(f'  {diff["table"]}: {diff["current_count"]} -> {diff["updated_count"]} ({diff["diff"]:+d})')
    else:
        print('\n✅ No row count differences found')
    
    current_conn.close()
    updated_conn.close()
    
    return new_tables, differences

def migrate_differences(new_tables, differences):
    """Migrate differences from updated database to current database"""
    
    if not new_tables and not differences:
        print('\n✅ No differences to migrate!')
        return
    
    print('\n🔄 Starting migration...')
    
    current_db = 'lavish_library.db'
    updated_db = '../lavish_library (1).db'
    
    # Connect to both databases
    current_conn = sqlite3.connect(current_db)
    updated_conn = sqlite3.connect(updated_db)
    
    try:
        # Migrate new tables
        if new_tables:
            print(f'\n📋 Migrating {len(new_tables)} new tables...')
            
            for table_name in new_tables:
                print(f'  📋 Migrating table: {table_name}')
                
                # Get table schema from updated database
                schema = updated_conn.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'").fetchone()
                if schema and schema[0]:
                    # Create table in current database
                    current_conn.execute(schema[0])
                    
                    # Get data from updated database
                    data = updated_conn.execute(f"SELECT * FROM {table_name}").fetchall()
                    
                    if data:
                        # Get column names
                        columns = [description[0] for description in updated_conn.execute(f"PRAGMA table_info({table_name})").fetchall()]
                        
                        # Insert data into current database
                        placeholders = ','.join(['?' for _ in columns])
                        current_conn.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", data)
                        
                        print(f'    ✅ Migrated {len(data)} rows')
                    else:
                        print(f'    ✅ Table created (no data)')
        
        # Migrate data differences
        if differences:
            print(f'\n📊 Migrating data for {len(differences)} tables with differences...')
            
            for diff in differences:
                table_name = diff['table']
                if diff['diff'] > 0:  # Updated database has more rows
                    print(f'  📊 Migrating data for table: {table_name} (+{diff["diff"]} rows)')
                    
                    # Get column names
                    columns = [description[0] for description in updated_conn.execute(f"PRAGMA table_info({table_name})").fetchall()]
                    
                    # Get existing IDs in current database
                    if 'id' in columns:
                        existing_ids = {row[0] for row in current_conn.execute(f"SELECT id FROM {table_name}").fetchall()}
                        
                        # Get new rows from updated database
                        new_data = []
                        for row in updated_conn.execute(f"SELECT * FROM {table_name}"):
                            if row[0] not in existing_ids:
                                new_data.append(row)
                        
                        if new_data:
                            placeholders = ','.join(['?' for _ in columns])
                            current_conn.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", new_data)
                            print(f'    ✅ Migrated {len(new_data)} new rows')
                        else:
                            print(f'    ✅ No new rows to migrate')
                    else:
                        print(f'    ⚠️  Table has no id column - skipping data migration')
        
        # Commit changes
        current_conn.commit()
        print('\n🎉 Migration completed successfully!')
        
    except Exception as e:
        print(f'\n❌ Migration error: {e}')
        current_conn.rollback()
    
    finally:
        current_conn.close()
        updated_conn.close()

if __name__ == '__main__':
    new_tables, differences = compare_databases()
    
    if new_tables or differences:
        print('\n❓ Do you want to migrate these differences? (y/n)')
        # In automated script, we'll proceed with migration
        migrate_differences(new_tables, differences)
    else:
        print('\n✅ Databases are already in sync!')