"""
Management command to verify migration consistency.

Prevents the "applied migrations missing from repo" issue by checking:
1. Migrations recorded in DB exist as files on disk
2. Migration files on disk are recorded in DB (informational)

Usage:
    python manage.py check_migration_consistency

Exit codes:
    0 - All migrations consistent
    1 - Missing migration files detected (CRITICAL)
    2 - Unapplied migrations detected (informational warning)
"""

import sys
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps


class Command(BaseCommand):
    help = "Check for migration consistency between database and filesystem"

    # Apps to check (exclude third-party)
    MONITORED_APPS = ["bookings", "barbers", "contact", "reviews"]

    def add_arguments(self, parser):
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Exit non-zero even for unapplied migrations (not just missing files)",
        )

    def handle(self, *args, **options):
        strict = options.get("strict", False)

        self.stdout.write(self.style.HTTP_INFO("=" * 70))
        self.stdout.write(self.style.HTTP_INFO("Migration Consistency Check"))
        self.stdout.write(self.style.HTTP_INFO("=" * 70))

        # Get applied migrations from database
        applied_migrations = self._get_applied_migrations()

        # Check each app
        missing_files = []
        unapplied_files = []

        for app_label in self.MONITORED_APPS:
            self.stdout.write(f"\nChecking app: {app_label}")

            # Get migrations directory
            try:
                app_config = apps.get_app_config(app_label)
                migrations_dir = Path(app_config.path) / "migrations"
            except LookupError:
                self.stdout.write(self.style.WARNING(f"  App {app_label} not found, skipping"))
                continue

            if not migrations_dir.exists():
                self.stdout.write(self.style.WARNING(f"  No migrations directory found"))
                continue

            # Get applied migrations for this app from DB
            app_applied = [name for app, name in applied_migrations if app == app_label]

            # Get migration files from disk
            migration_files = [
                f.stem for f in migrations_dir.glob("*.py")
                if f.name != "__init__.py" and not f.name.startswith(".")
            ]

            # Check 1: Applied migrations missing from disk (CRITICAL)
            for migration_name in app_applied:
                migration_file = migrations_dir / f"{migration_name}.py"
                if not migration_file.exists():
                    missing_files.append((app_label, migration_name))
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ MISSING FILE: {migration_name}.py (applied in DB)")
                    )

            # Check 2: Files on disk not applied in DB (informational)
            for migration_name in migration_files:
                if migration_name not in app_applied:
                    unapplied_files.append((app_label, migration_name))
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ UNAPPLIED: {migration_name}.py (exists on disk)")
                    )

            # Report OK if all good
            if not any(app == app_label for app, _ in missing_files + unapplied_files):
                self.stdout.write(self.style.SUCCESS(f"  ✓ All migrations consistent"))

        # Summary
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 70)

        if missing_files:
            self.stdout.write(self.style.ERROR(f"\n🔴 CRITICAL: {len(missing_files)} applied migrations missing from filesystem:"))
            for app, name in missing_files:
                self.stdout.write(f"   - {app}.{name}")
            self.stdout.write("\nACTION REQUIRED:")
            self.stdout.write("  1. Restore missing migration files from git history")
            self.stdout.write("  2. OR run: python manage.py migrate --fake <app> <migration>")
            return_code = 1
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ No missing migration files"))
            return_code = 0

        if unapplied_files:
            self.stdout.write(self.style.WARNING(f"\n⚠ INFO: {len(unapplied_files)} migration files not yet applied:"))
            for app, name in unapplied_files:
                self.stdout.write(f"   - {app}.{name}")
            self.stdout.write("\nRECOMMENDED:")
            self.stdout.write("  Run: python manage.py migrate")
            if strict:
                return_code = 2
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ All migration files are applied"))

        self.stdout.write("")
        sys.exit(return_code)

    def _get_applied_migrations(self):
        """
        Query django_migrations table for applied migrations.
        Returns list of (app, name) tuples.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT app, name FROM django_migrations ORDER BY app, name"
            )
            return cursor.fetchall()
