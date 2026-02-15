#!/bin/bash

# ============================================
# AX Merchant Portal - Automated Deployment Script
# Deploy from local machine to Digital Ocean droplet
# Server: 144.126.208.115
# Domain: www.orders.axpress.net
# ============================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER_IP="144.126.208.115"
SERVER_USER="root"
DOMAIN="www.orders.axpress.net"
DEPLOY_PATH="/home/backend"
LOCAL_BACKEND_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}=========================================="
echo "AX Merchant Portal - Backend Deployment"
echo "==========================================${NC}"
echo ""
echo "Server: $SERVER_IP"
echo "Domain: $DOMAIN"
echo "Deploy Path: $DEPLOY_PATH"
echo "Local Path: $LOCAL_BACKEND_PATH"
echo ""

# Test SSH connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
if ssh -o ConnectTimeout=5 $SERVER_USER@$SERVER_IP "echo 'SSH connection successful'" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ SSH connection successful${NC}"
else
    echo -e "${RED}✗ SSH connection failed${NC}"
    echo "Please ensure you can SSH to $SERVER_USER@$SERVER_IP"
    exit 1
fi

# Step 1: Prepare server
echo -e "${YELLOW}Step 1: Preparing server...${NC}"
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
# Update system
apt-get update

# Install dependencies
apt-get install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server certbot python3-certbot-nginx git

# Create directories
mkdir -p /home/backend
mkdir -p /home/backend/logs
mkdir -p /home/backend/staticfiles
mkdir -p /home/backend/media
mkdir -p /var/www/certbot

# Enable and start services
systemctl enable redis-server
systemctl start redis-server
systemctl enable postgresql
systemctl start postgresql

echo "Server prepared successfully"
ENDSSH

echo -e "${GREEN}✓ Server prepared${NC}"

# Step 2: Clone/Pull backend files from Git
echo -e "${YELLOW}Step 2: Cloning backend from Git repository...${NC}"
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /home

# Remove old backend directory if exists
if [ -d "backend" ]; then
    echo "Removing old backend directory..."
    rm -rf backend
fi

# Clone the repository
echo "Cloning from https://github.com/LibertytechX/aexpress.git..."
git clone https://github.com/LibertytechX/aexpress.git backend

cd backend

# If there's a backend subdirectory, move its contents up
if [ -d "backend" ]; then
    echo "Moving backend contents to root..."
    mv backend/* .
    mv backend/.* . 2>/dev/null || true
    rmdir backend
fi

echo "Repository cloned successfully"
ENDSSH

echo -e "${GREEN}✓ Files cloned from Git${NC}"

# Step 3: Setup production .env file
echo -e "${YELLOW}Step 3: Setting up environment file...${NC}"
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /home/backend

# Copy the production env template to .env
if [ -f "deploy/.env.production" ]; then
    cp deploy/.env.production .env
    echo "Environment file created from template"
else
    echo "Warning: deploy/.env.production not found in repository"
fi
ENDSSH

echo -e "${GREEN}✓ Environment file setup${NC}"

# Step 4: Install Python dependencies
echo -e "${YELLOW}Step 4: Installing Python dependencies...${NC}"
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /home/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

echo "Python dependencies installed"
ENDSSH

echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Step 5: Run Django migrations and collect static files
echo -e "${YELLOW}Step 5: Running Django migrations and collecting static files...${NC}"
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /home/backend
source venv/bin/activate

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

echo "Django setup complete"
ENDSSH

echo -e "${GREEN}✓ Django setup complete${NC}"

# Step 6: Configure Nginx
echo -e "${YELLOW}Step 6: Configuring Nginx...${NC}"
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
# Copy Nginx config
cp /home/backend/deploy/nginx.conf /etc/nginx/sites-available/axpress-api

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Enable site
ln -sf /etc/nginx/sites-available/axpress-api /etc/nginx/sites-enabled/

# Test Nginx config
nginx -t

echo "Nginx configured"
ENDSSH

echo -e "${GREEN}✓ Nginx configured${NC}"

# Step 7: Setup SSL with Certbot
echo -e "${YELLOW}Step 7: Setting up SSL certificate...${NC}"
echo "This will obtain an SSL certificate from Let's Encrypt"
ssh $SERVER_USER@$SERVER_IP << ENDSSH
# Get SSL certificate
certbot --nginx -d www.orders.axpress.net --non-interactive --agree-tos --email admin@axpress.net --redirect

echo "SSL certificate obtained"
ENDSSH

echo -e "${GREEN}✓ SSL certificate configured${NC}"

# Step 8: Setup systemd service
echo -e "${YELLOW}Step 8: Setting up systemd service...${NC}"
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
# Copy service file
cp /home/backend/deploy/axpress-api.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable and start service
systemctl enable axpress-api
systemctl start axpress-api

# Restart Nginx
systemctl restart nginx

echo "Service started"
ENDSSH

echo -e "${GREEN}✓ Service started${NC}"

# Step 9: Check status
echo -e "${YELLOW}Step 9: Checking deployment status...${NC}"
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
echo ""
echo "=== Service Status ==="
systemctl status axpress-api --no-pager | head -20

echo ""
echo "=== Nginx Status ==="
systemctl status nginx --no-pager | head -10

echo ""
echo "=== Recent Logs ==="
tail -20 /home/backend/logs/gunicorn_error.log
ENDSSH

echo ""
echo -e "${GREEN}=========================================="
echo "Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo "Your API is now available at:"
echo "  https://www.orders.axpress.net"
echo ""
echo "Useful commands:"
echo "  Check status: ssh $SERVER_USER@$SERVER_IP 'systemctl status axpress-api'"
echo "  View logs: ssh $SERVER_USER@$SERVER_IP 'tail -f /home/backend/logs/gunicorn_error.log'"
echo "  Restart: ssh $SERVER_USER@$SERVER_IP 'systemctl restart axpress-api'"
echo ""

