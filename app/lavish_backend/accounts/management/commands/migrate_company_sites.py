from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Migrate CompanySite data from medications to accounts app'

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            # Check if medications_companysite table exists
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'medications_companysite'
            """)
            
            result = cursor.fetchone()
            if result and result[0] > 0:
                # Table exists, migrate data
                self.stdout.write('Migrating CompanySite data from medications to accounts...')
                
                try:
                    # Copy data from medications_companysite to accounts_companysite
                    cursor.execute("""
                        INSERT INTO accounts_companysite 
                        (id, company_id, name, address, suburb, state, country, 
                         contact_number, is_active, created_at, updated_at)
                        SELECT id, company_id, name, address, suburb, state, 
                               COALESCE(country, 'Australia'), contact_number, 
                               is_active, created_at, COALESCE(updated_at, created_at)
                        FROM medications_companysite
                        WHERE NOT EXISTS (
                            SELECT 1 FROM accounts_companysite 
                            WHERE accounts_companysite.id = medications_companysite.id
                        )
                    """)
                    
                    rows_affected = cursor.rowcount
                    self.stdout.write(self.style.SUCCESS(f'Successfully migrated {rows_affected} CompanySite records'))
                    
                    # Update foreign key references in medications_medicationadministration
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM information_schema.columns 
                        WHERE table_name = 'medications_medicationadministration' 
                        AND column_name = 'site_id'
                    """)
                    
                    if cursor.fetchone()[0] > 0:
                        self.stdout.write('Foreign key references already point to the correct table')
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error during migration: {e}'))
            else:
                self.stdout.write('No medications_companysite table found or already migrated')
                
            # Verify migration
            cursor.execute("SELECT COUNT(*) FROM accounts_companysite")
            count = cursor.fetchone()[0]
            self.stdout.write(self.style.SUCCESS(f'Total CompanySite records in accounts app: {count}'))
