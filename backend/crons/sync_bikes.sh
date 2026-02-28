#!/bin/bash
# ============================================================
# sync_bikes.sh — Cron wrapper for sync_bike_telemetry
#
# Activates the project virtual environment, runs the Django
# management command, and appends timestamped output to the
# bike sync log file.
#
# Suggested crontab entry (every 2 minutes):
#   */2 * * * * /home/backend/crons/sync_bikes.sh
# ============================================================

DEPLOY_PATH="/home/backend"
DJANGO_PATH="$DEPLOY_PATH/backend"          # WorkingDirectory used by gunicorn/manage.py
VENV_PYTHON="$DEPLOY_PATH/venv/bin/python"
LOG_FILE="$DEPLOY_PATH/logs/bike_sync.log"
MANAGE="$DJANGO_PATH/manage.py"

# ── Safety checks ────────────────────────────────────────────
if [ ! -f "$VENV_PYTHON" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: venv not found at $VENV_PYTHON" >> "$LOG_FILE"
    exit 1
fi

if [ ! -f "$MANAGE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: manage.py not found at $MANAGE" >> "$LOG_FILE"
    exit 1
fi

# ── Load environment variables ───────────────────────────────
if [ -f "$DEPLOY_PATH/.env" ]; then
    set -a
    source "$DEPLOY_PATH/.env"
    set +a
fi

# ── Run the sync command ─────────────────────────────────────
echo "[$(date '+%Y-%m-%d %H:%M:%S')] --- bike sync start ---" >> "$LOG_FILE"

"$VENV_PYTHON" "$MANAGE" sync_bike_telemetry >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] sync_bike_telemetry finished OK (exit 0)" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] sync_bike_telemetry FAILED (exit $EXIT_CODE)" >> "$LOG_FILE"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] --- bike sync end ---" >> "$LOG_FILE"

exit $EXIT_CODE

