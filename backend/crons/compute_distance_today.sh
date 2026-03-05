#!/bin/bash
# ============================================================
# compute_distance_today.sh — Cron wrapper for compute_distance_today
#
# Runs the Django management command once per minute to keep
# VehicleAsset.distance_today fresh.
#
# Suggested crontab entry:
#   * * * * * /home/backend/backend/crons/compute_distance_today.sh
# ============================================================

set -e

DEPLOY_PATH="/home/backend"
DJANGO_PATH="$DEPLOY_PATH/backend"
VENV_PYTHON="$DEPLOY_PATH/venv/bin/python"
MANAGE="$DJANGO_PATH/manage.py"
LOG_FILE="$DEPLOY_PATH/logs/compute_distance_today.log"
LOCK_FILE="/tmp/compute_distance_today.lock"

mkdir -p "$(dirname "$LOG_FILE")"

# ── Safety checks ────────────────────────────────────────────
if [ ! -f "$VENV_PYTHON" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: venv python not found at $VENV_PYTHON" >> "$LOG_FILE"
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

# ── Prevent overlapping runs ─────────────────────────────────
if command -v flock >/dev/null 2>&1; then
  flock -n "$LOCK_FILE" "$VENV_PYTHON" "$MANAGE" compute_distance_today >> "$LOG_FILE" 2>&1
else
  "$VENV_PYTHON" "$MANAGE" compute_distance_today >> "$LOG_FILE" 2>&1
fi

