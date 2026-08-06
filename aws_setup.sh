#!/bin/bash
# ==============================================================================
# MarketPulse AWS EC2 Automated Production Setup Script (Ubuntu 22.04 / 24.04)
# ==============================================================================
set -e

echo "========================================================"
echo " 🚀 Starting MarketPulse AWS EC2 Automated Setup"
echo "========================================================"

# 1. Update and install system dependencies
echo "📦 Updating system packages and installing dependencies..."
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv git nginx curl ufw

# 2. Setup project environment
PROJECT_DIR=$(pwd)
echo "📂 Working directory: $PROJECT_DIR"

echo "🐍 Setting up Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Create Systemd Service for 24/7 Background Execution
echo "⚙️ Creating Systemd background service (marketpulse.service)..."
SERVICE_FILE="/etc/systemd/system/marketpulse.service"
CURRENT_USER=$(whoami)

sudo bash -c "cat <<EOF > $SERVICE_FILE
[Unit]
Description=MarketPulse Financial Prediction Platform
After=network.target

[Service]
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/server.py
Restart=always
RestartSec=5
Environment=PORT=8501
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable marketpulse
sudo systemctl restart marketpulse

# 4. Configure Nginx Reverse Proxy (Port 80 -> Port 8501)
echo "🌐 Configuring Nginx Reverse Proxy for HTTP port 80..."
NGINX_CONF="/etc/nginx/sites-available/marketpulse"

sudo bash -c "cat <<EOF > $NGINX_CONF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }
}
EOF"

sudo ln -sf /etc/nginx/sites-available/marketpulse /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# 5. Summary
PUBLIC_IP=$(curl -s ifconfig.me || echo "YOUR-EC2-PUBLIC-IP")
echo "========================================================"
echo " ✅ MarketPulse Successfully Deployed on AWS EC2!"
echo "========================================================"
echo " 🌐 Access your live application at:"
echo "    http://$PUBLIC_IP"
echo "    http://$PUBLIC_IP:8501"
echo "========================================================"
echo " 📜 Useful service management commands:"
echo "    sudo systemctl status marketpulse   # Check status"
echo "    sudo systemctl restart marketpulse  # Restart app"
echo "    sudo journalctl -u marketpulse -f   # View live logs"
echo "========================================================"
