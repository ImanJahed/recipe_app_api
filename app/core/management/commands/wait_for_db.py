"""
Django command to wait for the database to be available
"""

import time

from django.core.management.base import BaseCommand
from django.db.utils import OperationalError
from psycopg2 import OperationalError as Pyscopg2OpError


class Command(BaseCommand):
    """Django command to wait to database."""

    def handle(self, *args, **options):
        self.stdout.write("Waiting for database...")
        db_up = False

        while db_up is False:
            try:
                self.check(databases=["default"])
                db_up = True

            except (Pyscopg2OpError, OperationalError):
                self.stdout.write(
                    self.style.ERROR("Database unavailable, \
                        waiting 1 second... ")
                )
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database available!"))
