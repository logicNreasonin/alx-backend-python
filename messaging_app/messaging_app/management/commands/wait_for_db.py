# ~/Documents/Github/alx-backend-python/messaging_app/messaging_app/management/commands/wait_for_db.py
import time
import sys
from django.db import connections
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """Django command to pause execution until database is available"""

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        db_conn = None
        retries = 30  # Try for 30 seconds (30 * 1 second)
        while retries > 0:
            try:
                db_conn = connections['default']
                db_conn.cursor() # Try to get a cursor from the db
                self.stdout.write(self.style.SUCCESS('Database available!'))
                break # Exit loop if connection successful
            except OperationalError:
                self.stdout.write('Database unavailable, waiting 1 second...')
                time.sleep(1)
                retries -= 1
        
        if retries == 0:
            self.stderr.write(self.style.ERROR('Database unavailable after multiple retries. Exiting.'))
            sys.exit(1) # Exit with error code if db not available