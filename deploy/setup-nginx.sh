#!/bin/bash
# 快速配置 nginx

echo "配置 nginx..."

# 创建 nginx 配置
cat > /tmp/lms-edge.conf << 'EOF'
server {
    listen 8080;
    server_name _;
    root /home/raven/lms-edge/lms-edge/backend/static;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

echo "配置已创建: /tmp/lms-edge.conf"
echo ""
echo "请手动执行:"
echo "  sudo cp /tmp/lms-edge.conf /etc/nginx/sites-available/lms-edge"
echo "  sudo ln -sf /etc/nginx/sites-available/lms-edge /etc/nginx/sites-enabled/"
echo "  sudo nginx -t"
echo "  sudo systemctl restart nginx"
