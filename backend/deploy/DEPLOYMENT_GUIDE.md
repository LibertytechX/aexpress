# AX Merchant Portal - Backend Deployment Guide

## Server Information
- **IP Address**: 144.126.208.115
- **Domain**: www.orders.axpress.net
- **Deploy Path**: /home/backend
- **User**: root

## Prerequisites
- SSH access to the server (144.126.208.115)
- Domain DNS already pointed to server IP
- PostgreSQL database already configured (axpress)

## Quick Deployment

### Option 1: Automated Deployment (Recommended)

1. **Update production environment file**:
   ```bash
   cd backend/deploy
   nano .env.production
   ```
   Update the following:
   - `SECRET_KEY` - Generate a new random secret key
   - `FRONTEND_URL` - Your Vercel frontend URL (after deployment)

2. **Make deployment script executable**:
   ```bash
   chmod +x deploy_to_server.sh
   ```

3. **Run deployment script**:
   ```bash
   ./deploy_to_server.sh
   ```

   This script will:
   - Install system dependencies (Python, Nginx, PostgreSQL, Redis, Certbot)
   - Copy backend files to server
   - Set up Python virtual environment
   - Install Python dependencies
   - Run database migrations
   - Collect static files
   - Configure Nginx
   - Obtain SSL certificate from Let's Encrypt
   - Set up systemd service
   - Start the application

4. **Verify deployment**:
   ```bash
   curl https://www.orders.axpress.net/api/
   ```

### Option 2: Manual Deployment

If you prefer to deploy manually, follow these steps:

1. **SSH into server**:
   ```bash
   ssh root@144.126.208.115
   ```

2. **Install dependencies**:
   ```bash
   apt-get update
   apt-get install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server certbot python3-certbot-nginx
   ```

3. **Create directories**:
   ```bash
   mkdir -p /home/backend/{logs,staticfiles,media}
   ```

4. **Copy backend files** (from local machine):
   ```bash
   rsync -avz --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' backend/ root@144.126.208.115:/home/backend/
   ```

5. **Copy production .env**:
   ```bash
   scp backend/deploy/.env.production root@144.126.208.115:/home/backend/.env
   ```

6. **On server, set up Python environment**:
   ```bash
   cd /home/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install gunicorn
   ```

7. **Run migrations and collect static**:
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

8. **Configure Nginx**:
   ```bash
   cp /home/backend/deploy/nginx.conf /etc/nginx/sites-available/axpress-api
   ln -s /etc/nginx/sites-available/axpress-api /etc/nginx/sites-enabled/
   rm -f /etc/nginx/sites-enabled/default
   nginx -t
   ```

9. **Get SSL certificate**:
   ```bash
   certbot --nginx -d www.orders.axpress.net --non-interactive --agree-tos --email admin@axpress.net
   ```

10. **Set up systemd service**:
    ```bash
    cp /home/backend/deploy/axpress-api.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable axpress-api
    systemctl start axpress-api
    systemctl restart nginx
    ```

## Post-Deployment

### Check Service Status
```bash
ssh root@144.126.208.115 'systemctl status axpress-api'
```

### View Logs
```bash
ssh root@144.126.208.115 'tail -f /home/backend/logs/gunicorn_error.log'
```

### Restart Service
```bash
ssh root@144.126.208.115 'systemctl restart axpress-api'
```

### Update Code
```bash
# From local machine
rsync -avz --exclude='venv' --exclude='__pycache__' backend/ root@144.126.208.115:/home/backend/
ssh root@144.126.208.115 'systemctl restart axpress-api'
```

## Configuration Files

- **Gunicorn**: `/home/backend/deploy/gunicorn_config.py`
  - Timeout: 3 seconds (as requested)
  - Workers: CPU count * 2 + 1
  - Bind: 127.0.0.1:8000

- **Nginx**: `/etc/nginx/sites-available/axpress-api`
  - Proxy timeout: 3 seconds
  - SSL enabled
  - Static files served directly

- **Systemd**: `/etc/systemd/system/axpress-api.service`
  - Auto-restart on failure
  - Starts after PostgreSQL and Redis

## Troubleshooting

### Service won't start
```bash
journalctl -u axpress-api -n 50
```

### Nginx errors
```bash
tail -f /var/log/nginx/axpress_api_error.log
```

### Database connection issues
```bash
sudo -u postgres psql -c "\l"  # List databases
sudo -u postgres psql axpress -c "\dt"  # List tables
```

### SSL certificate renewal
```bash
certbot renew --dry-run
```

## Frontend Integration

After deploying frontend to Vercel:

1. Update `.env` on server:
   ```bash
   ssh root@144.126.208.115
   nano /home/backend/.env
   # Update FRONTEND_URL=https://your-app.vercel.app
   ```

2. Restart service:
   ```bash
   systemctl restart axpress-api
   ```

## API Endpoints

Your API will be available at:
- **Base URL**: https://www.orders.axpress.net
- **Admin**: https://www.orders.axpress.net/admin/
- **API Docs**: https://www.orders.axpress.net/api/

## Security Notes

- ✅ SSL/HTTPS enabled
- ✅ CORS configured for frontend
- ✅ Debug mode disabled in production
- ✅ Secret key secured in .env
- ✅ Database password secured in .env
- ✅ Gunicorn timeout set to 3 seconds
- ✅ Security headers enabled

