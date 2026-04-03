import os
import subprocess
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Creates a PostgreSQL database backup and removes old ones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-days', type=int, default=7,
            help='Number of days to keep backups (default: 7)'
        )

    def handle(self, *args, **options):
        keep_days   = options['keep_days']
        backup_dir  = '/app/backups'
        timestamp   = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename    = f"chandamama_db_{timestamp}.sql"
        filepath    = os.path.join(backup_dir, filename)

        # ── Ensure backup directory exists ────────────────────────
        os.makedirs(backup_dir, exist_ok=True)

        # ── Get DB credentials from settings ──────────────────────
        db = settings.DATABASES['default']
        db_name = db.get('NAME', 'myeod_db')
        db_user = db.get('USER', 'postgres')
        db_pass = db.get('PASSWORD', '')
        db_host = db.get('HOST', 'db')
        db_port = db.get('PORT', '5432')

        # ── Run pg_dump ───────────────────────────────────────────
        env = os.environ.copy()
        env['PGPASSWORD'] = db_pass

        cmd = [
            'pg_dump',
            '-h', db_host,
            '-p', str(db_port),
            '-U', db_user,
            '-F', 'p',       # plain SQL format
            '-f', filepath,
            db_name,
        ]

        try:
            result = subprocess.run(
                cmd, env=env,
                capture_output=True, text=True, timeout=120
            )

            if result.returncode != 0:
                self.stdout.write(self.style.ERROR(
                    f'❌ Backup failed: {result.stderr}'
                ))
                return

            size_kb = round(os.path.getsize(filepath) / 1024, 1)
            self.stdout.write(self.style.SUCCESS(
                f'✅ Backup created: {filename} ({size_kb} KB)'
            ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                '❌ pg_dump not found. Install postgresql-client in Dockerfile.'
            ))
            return
        except subprocess.TimeoutExpired:
            self.stdout.write(self.style.ERROR('❌ Backup timed out after 120 seconds'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Backup error: {e}'))
            return

        # ── Delete old backups ────────────────────────────────────
        cutoff = datetime.now() - timedelta(days=keep_days)
        deleted = 0

        for fname in os.listdir(backup_dir):
            if not fname.startswith('chandamama_db_') or not fname.endswith('.sql'):
                continue
            fpath = os.path.join(backup_dir, fname)
            ftime = datetime.fromtimestamp(os.path.getmtime(fpath))
            if ftime < cutoff:
                os.remove(fpath)
                deleted += 1

        if deleted:
            self.stdout.write(self.style.WARNING(
                f'🗑️  Deleted {deleted} old backup(s) older than {keep_days} days'
            ))

        # ── List current backups ──────────────────────────────────
        backups = sorted([
            f for f in os.listdir(backup_dir)
            if f.startswith('chandamama_db_') and f.endswith('.sql')
        ])
        self.stdout.write(f'\n📁 Current backups ({len(backups)}/{keep_days} max):')
        for b in backups:
            bpath = os.path.join(backup_dir, b)
            size  = round(os.path.getsize(bpath) / 1024, 1)
            self.stdout.write(f'   • {b} ({size} KB)')
