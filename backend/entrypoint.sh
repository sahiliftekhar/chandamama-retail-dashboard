#!/bin/sh

# ── Wait for database ─────────────────────────────────────────────
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.5
done
echo "Database started"

# ── Run migrations ────────────────────────────────────────────────
echo "Running migrations..."
python manage.py migrate --noinput

# ── Ensure superuser ──────────────────────────────────────────────
echo "Ensuring superuser exists..."
python manage.py ensure_superuser

# ── Collect static files ──────────────────────────────────────────
echo "Collecting static files..."
python manage.py collectstatic --noinput

# ── Create log directory ──────────────────────────────────────────
mkdir -p /app/logs
touch /app/logs/error.log
touch /app/logs/requests.log
touch /app/logs/security.log
touch /app/logs/gunicorn_access.log
touch /app/logs/gunicorn_error.log
echo "Log directory ready"

# ── Setup cron ────────────────────────────────────────────────────
echo "Setting up scheduled alerts..."
apt-get install -y cron > /dev/null 2>&1

cat > /etc/cron.d/chandamama << CRONEOF
# EOD Sales Report — 9:00 PM IST (15:30 UTC)
30 15 * * * root cd /app && python manage.py send_eod_report >> /app/logs/eod.log 2>&1

# Stock Alerts — 10:00 AM IST (04:30 UTC)
30 4 * * * root cd /app && python manage.py send_stock_alerts >> /app/logs/stock_alerts.log 2>&1

# Daily DB Backup — 11:00 PM IST (17:30 UTC)
30 17 * * * root cd /app && python manage.py backup_db >> /app/logs/backup.log 2>&1

# Health check ping — every 5 minutes
*/5 * * * * root curl -sf http://localhost:8000/api/health/ >> /app/logs/health.log 2>&1
CRONEOF

chmod 0644 /etc/cron.d/chandamama
service cron start
echo "Cron scheduler started"

# ── Start Gunicorn ────────────────────────────────────────────────
echo "Starting server..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --reload \
    --timeout 120 \
    --access-logfile /app/logs/gunicorn_access.log \
    --error-logfile /app/logs/gunicorn_error.log \
    --log-level info \
    --capture-output