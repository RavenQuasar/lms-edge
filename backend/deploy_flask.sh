#!/bin/bash
set -e

echo "=== LMS-Edge v3.0 Deployment (Flask + Nginx) ==="

# Install Flask if not installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing Flask..."
    pip3 install flask flask-cors --user
fi

# Stop existing services
echo "Stopping existing services..."
sudo systemctl stop lms-edge 2>/dev/null || true
sudo systemctl stop lms-edge-api 2>/dev/null || true
sudo systemctl stop lms-edge-nginx 2>/dev/null || true
pkill -f full_server.py 2>/dev/null || true
pkill -f app_api.py 2>/dev/null || true

# Copy nginx config
echo "Configuring nginx..."
sudo cp /tmp/lms-edge.conf /etc/nginx/sites-available/
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/lms-edge.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Copy systemd services
echo "Configuring systemd..."
sudo cp /tmp/lms-edge-api.service /etc/systemd/system/
sudo cp /tmp/lms-edge-nginx.service /etc/systemd/system/
sudo systemctl daemon-reload

# Start services
echo "Starting services..."
sudo systemctl start lms-edge-api
sudo systemctl start lms-edge-nginx

# Enable on boot
sudo systemctl enable lms-edge-api
sudo systemctl enable lms-edge-nginx

echo ""
echo "=== Deployment Complete ==="
echo "Access: http://192.168.55.1:8080"
echo ""
sudo systemctl status lms-edge-api --no-pager || true
