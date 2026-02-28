#!/bin/bash
# ============================================================
# sync_bikes.sh — Cron wrapper for sync_bike_telemetry
#
# Activates the project virtual environment, runs the Django
# management command, and appends timestamped output to the
# bike sync log file.
#
# Suggested crontab entry (every minute — script loops 6× with 10s sleep):
#   * * * * * /home/backend/backend/crons/sync_bikes.sh
# ============================================================

DEPLOY_PATH="/home/backend"
DJANGO_PATH="$DEPLOY_PATH/backend"          # WorkingDirectory used by gunicorn/manage.py
VENV_PYTHON="$DEPLOY_PATH/venv/bin/python"
LOG_FILE="$DEPLOY_PATH/logs/bike_sync.log"
MANAGE="$DJANGO_PATH/manage.py"
SYNC_INTERVAL=10   # seconds between each sync run
RUNS_PER_MINUTE=6  # 60s / 10s = 6 runs

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

# ── Run the sync command 6 times (every 10 seconds) ──────────
for i in $(seq 1 $RUNS_PER_MINUTE); do
    "$VENV_PYTHON" "$MANAGE" sync_bike_telemetry >> "$LOG_FILE" 2>&1
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] sync OK (run $i/$RUNS_PER_MINUTE)" >> "$LOG_FILE"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] sync FAILED exit=$EXIT_CODE (run $i/$RUNS_PER_MINUTE)" >> "$LOG_FILE"
    fi

    # Don't sleep after the last run
    if [ $i -lt $RUNS_PER_MINUTE ]; then
        sleep $SYNC_INTERVAL
    fi
done

