#!/bin/bash

# ============================================
# AX Merchant Portal - Backend Deployment Script
# Server: 144.126.208.115
# Domain: www.orders.axpress.net
# ============================================

set -e  # Exit on error

echo "=========================================="
echo "AX Merchant Portal - Backend Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVER_IP="144.126.208.115"
DOMAIN="www.orders.axpress.net"
DEPLOY_USER="root"
DEPLOY_PATH="/home/backend"
PROJECT_NAME="ax_merchant_api"

echo -e "${YELLOW}Step 1: Installing system dependencies...${NC}"
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server certbot python3-certbot-nginx

echo -e "${GREEN}✓ System dependencies installed${NC}"

echo -e "${YELLOW}Step 2: Creating deployment directory...${NC}"
sudo mkdir -p $DEPLOY_PATH
sudo mkdir -p $DEPLOY_PATH/logs
sudo mkdir -p $DEPLOY_PATH/staticfiles
sudo mkdir -p $DEPLOY_PATH/media

echo -e "${GREEN}✓ Directories created${NC}"

echo -e "${YELLOW}Step 3: Setting up Python virtual environment...${NC}"
cd $DEPLOY_PATH
python3 -m venv venv
source venv/bin/activate

echo -e "${GREEN}✓ Virtual environment created${NC}"

echo -e "${YELLOW}Step 4: Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install gunicorn

echo -e "${GREEN}✓ Python dependencies installed${NC}"

echo -e "${YELLOW}Step 5: Configuring PostgreSQL...${NC}"
echo "PostgreSQL is already configured with:"
echo "  Database: axpress"
echo "  User: postgres"
echo "  Port: 5432"

echo -e "${GREEN}✓ PostgreSQL configured${NC}"

echo -e "${YELLOW}Step 6: Configuring Redis...${NC}"
sudo systemctl enable redis-server
sudo systemctl start redis-server

echo -e "${GREEN}✓ Redis configured${NC}"

echo -e "${YELLOW}Step 7: Setting up Nginx...${NC}"
sudo rm -f /etc/nginx/sites-enabled/default
echo "Nginx configuration will be set up after copying project files"

echo -e "${GREEN}✓ Nginx prepared${NC}"

echo -e "${YELLOW}Step 8: Setting up SSL with Certbot...${NC}"
echo "SSL will be configured after Nginx is set up"

echo ""
echo -e "${GREEN}=========================================="
echo "Server preparation complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Copy your backend code to: $DEPLOY_PATH"
echo "2. Copy .env file with production settings"
echo "3. Run: pip install -r requirements.txt"
echo "4. Run: python manage.py collectstatic --noinput"
echo "5. Run: python manage.py migrate"
echo "6. Copy nginx config: sudo cp deploy/nginx.conf /etc/nginx/sites-available/axpress-api"
echo "7. Enable nginx site: sudo ln -s /etc/nginx/sites-available/axpress-api /etc/nginx/sites-enabled/"
echo "8. Test nginx: sudo nginx -t"
echo "9. Get SSL cert: sudo certbot --nginx -d $DOMAIN"
echo "10. Copy systemd service: sudo cp deploy/axpress-api.service /etc/systemd/system/"
echo "11. Start service: sudo systemctl start axpress-api"
echo "12. Enable service: sudo systemctl enable axpress-api"

