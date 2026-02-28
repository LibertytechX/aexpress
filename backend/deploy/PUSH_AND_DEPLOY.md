# AX Merchant Portal — Push & Deploy Guide

## Overview

This guide covers the end-to-end workflow for pushing a code change from your local machine
to GitHub and deploying it to the production server (`144.126.208.115`).

---

## Prerequisites

| Requirement | Details |
|---|---|
| SSH access | `ssh root@144.126.208.115` must work without a password prompt |
| Git remote | `git remote -v` should show `aexpress` pointing to `github.com/LibertytechX/aexpress` |
| `.env` on server | `/home/backend/.env` must include `CONCEPT_NOVA_EMAIL` and `CONCEPT_NOVA_PASSWORD` |

---

## Step 1 — Set Concept Nova Credentials on the Server (one-time)

> **Skip this step if you have already added the credentials.**

```bash
ssh root@144.126.208.115
nano /home/backend/.env
```

Add (or confirm) these lines:

```
CONCEPT_NOVA_EMAIL=inyangete@gmail.com
CONCEPT_NOVA_PASSWORD=Ab123456
CONCEPT_NOVA_BASE_URL=https://monitor.concept-nova.com
```

Save with `Ctrl+O`, exit with `Ctrl+X`.

> ⚠️  Never commit credentials to Git. The `.env` file is git-ignored.

---

## Step 2 — Commit and Push to GitHub

```bash
# From the repo root (ax-merchant-portal/frontend)
git add backend/
git add dispatcher-frontend/
git commit -m "feat: bike telemetry sync — management command, cron, and deployment"
git push aexpress main
```

---

## Step 3 — Deploy to Server

### Option A: Pull + migrate + restart (standard update)

```bash
ssh root@144.126.208.115 << 'EOF'
set -e
cd /home/backend

# 1. Pull latest code
git pull origin main

# 2. Activate venv and install any new dependencies
source venv/bin/activate
pip install -r requirements.txt --quiet

# 3. Apply database migrations (adds provider_id & sync_meta to vehicle_assets)
python manage.py migrate --noinput

# 4. Collect static files
python manage.py collectstatic --noinput

# 5. Make cron script executable
chmod +x /home/backend/crons/sync_bikes.sh

# 6. Install / refresh cron job (every 2 minutes)
CRON_ENTRY="*/2 * * * * /home/backend/crons/sync_bikes.sh"
( crontab -l 2>/dev/null | grep -v "sync_bikes.sh" ; echo "$CRON_ENTRY" ) | crontab -

# 7. Restart API
systemctl restart axpress-api
echo "✅ Deploy complete"
EOF
```

### Option B: Full automated deployment (first-time / clean install)

```bash
cd backend/deploy
chmod +x deploy_to_server.sh
./deploy_to_server.sh
```

---

## Step 4 — Verify Deployment

### Check API service

```bash
ssh root@144.126.208.115 'systemctl status axpress-api --no-pager | head -20'
```

### Check cron job is registered

```bash
ssh root@144.126.208.115 'crontab -l | grep sync_bikes'
# Expected output:
# */2 * * * * /home/backend/crons/sync_bikes.sh
```

### Run a manual sync (smoke test)

```bash
ssh root@144.126.208.115 'cd /home/backend && source venv/bin/activate && python manage.py sync_bike_telemetry'
```

Expected output:
```
Logging in to Concept Nova API…
Authenticated OK
Fetching devices…
Received N device(s) from API
Sync complete — created: X  updated: Y  skipped: Z
```

### Watch the sync log live

```bash
ssh root@144.126.208.115 'tail -f /home/backend/logs/bike_sync.log'
```

---

## Step 5 — Rollback Procedure

If something goes wrong after deployment:

```bash
ssh root@144.126.208.115 << 'EOF'
cd /home/backend

# Roll back to previous commit
git log --oneline -5          # find the last good commit hash
git reset --hard <COMMIT_HASH>

source venv/bin/activate
python manage.py migrate --noinput   # safe to run; no destructive migrations
systemctl restart axpress-api
echo "✅ Rollback complete"
EOF
```

To remove the cron job temporarily:

```bash
ssh root@144.126.208.115 'crontab -l | grep -v sync_bikes | crontab -'
```

---

## Configuration Reference

| File | Server Path | Purpose |
|---|---|---|
| `.env` | `/home/backend/.env` | All secrets and env vars |
| `sync_bikes.sh` | `/home/backend/crons/sync_bikes.sh` | Cron wrapper for telemetry sync |
| Cron log | `/home/backend/logs/bike_sync.log` | Timestamped output from each sync run |
| API log | `/home/backend/logs/gunicorn_error.log` | Gunicorn / Django errors |
| API service | `systemctl status axpress-api` | Gunicorn process managed by systemd |

