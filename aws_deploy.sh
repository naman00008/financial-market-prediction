#!/bin/bash
# ==============================================================================
# MarketPulse — AWS EC2 Automated Production Deployment Script (Ubuntu 22.04/24.04)
# ==============================================================================

set -e

echo "=========================================================="
echo " Starting MarketPulse AWS EC2 Deployment Setup"
echo "=========================================================="

# 1. Update OS Packages
echo "[1/7] Updating system package index..."
sudo apt-get update -y

# 2. Install System Dependencies (Python 3, pip, git, Nginx, Certbot)
echo "[2/7] Installing Python3, build tools, Nginx, and Certbot..."
sudo apt-get install -y python3 python3-pip python3-venv git nginx curl

# 3. Create Project Directory & Virtual Environment
echo "[3/7] Setting up project directory and Python virtual environment..."
cd /home/ubuntu
if [ ! -d "financial-market-prediction" ]; then
    git clone https://github.com/naman00008/financial-market-prediction.git
else
    cd financial-market-prediction
    git pull origin main
    cd /home/ubuntu
fi

cd /home/ubuntu/financial-market-prediction

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# 4. Install Python Requirements
echo "[4/7] Installing Python dependencies from requirements.txt..."
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# 5. Configure Systemd Daemon Service
echo "[5/7] Configuring Systemd service (marketpulse.service)..."
sudo cp marketpulse.service /etc/systemd/system/marketpulse.service
sudo systemctl daemon-reload
sudo systemctl enable marketpulse.service
sudo systemctl restart marketpulse.service

# 6. Configure Nginx Reverse Proxy
echo "[6/7] Configuring Nginx reverse proxy with WebSocket support..."
sudo cp nginx_marketpulse.conf /etc/nginx/sites-available/marketpulse
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/marketpulse /etc/nginx/sites-enabled/marketpulse
sudo nginx -t
sudo systemctl restart nginx

# 7. Final Verification
echo "[7/7] Waiting for Python backend to initialize..."
sleep 3
sudo systemctl status marketpulse.service --no-pager
sudo systemctl status nginx --no-pager

echo "=========================================================="
echo " MarketPulse Deployment Complete on AWS EC2!"
echo " Public Access: http://$(curl -s http://checkip.amazonaws.com || echo '34.205.48.35')"
echo "=========================================================="
