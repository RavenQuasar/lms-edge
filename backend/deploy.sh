#!/bin/bash
# LMS-Edge Deployment Script

set -e

echo "=== LMS-Edge Deployment ==="

# Stop existing services
echo "Stopping existing services..."
sudo systemctl stop lms-edge-nginx 2>/dev/null || true
sudo systemctl stop lms-edge-api 2>/dev/null || true

# Install nginx if not installed
if ! command -v nginx &> /dev/null; then
    echo "Installing nginx..."
    sudo apt-get update
    sudo apt-get install -y nginx
fi

# Copy nginx config
echo "Configuring nginx..."
sudo cp /home/raven/lms-edge/backend/nginx/lms-edge.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/lms-edge.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx config
sudo nginx -t

# Copy systemd service
echo "Configuring systemd service..."
sudo cp /home/raven/lms-edge/backend/systemd/lms-edge-api.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Start services
echo "Starting services..."
sudo systemctl start lms-edge-api
sudo systemctl start lms-edge-nginx

# Enable on boot
sudo systemctl enable lms-edge-api
sudo systemctl enable lms-edge-nginx

# Show status
echo ""
echo "=== Services Status ==="
sudo systemctl status lms-edge-api --no-pager || true
sudo systemctl status lms-edge-nginx --no-pager || true

echo ""
echo "=== Deployment Complete ==="
echo "Access: http://jetson-nano-ip:8080"
echo "API: http://jetson-nano-ip:8080/api/"
