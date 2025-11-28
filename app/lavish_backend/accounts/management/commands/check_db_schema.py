from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Check database schema for CustomUser table'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check structure of accounts_customuser table
            cursor.execute("PRAGMA table_info(accounts_customuser)")
            columns = cursor.fetchall()
            self.stdout.write(self.style.SUCCESS('CustomUser table columns:'))
            for column in columns:
                self.stdout.write(f"{column}")
                
            # Check if the migration history matches expected state
            cursor.execute("SELECT * FROM django_migrations WHERE app='accounts' ORDER BY id DESC LIMIT 5")
            migrations = cursor.fetchall()
            self.stdout.write(self.style.SUCCESS('\nRecent account migrations:'))
            for migration in migrations:
                self.stdout.write(f"{migration}") 