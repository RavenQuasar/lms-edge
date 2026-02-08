#!/usr/bin/env python3
"""
LMS-Edge 完整部署脚本 - 通过SSH远程执行
"""

import subprocess
import os

# 部署命令
commands = [
    # 1. 安装系统依赖
    ("sudo apt-get update", True),
    ("sudo apt-get install -y nginx python3-pip python3-venv git nodejs npm", True),
    
    # 2. 创建项目目录
    ("sudo mkdir -p /opt/lms-edge/backend/{data,logs,uploads,static}", False),
    ("sudo mkdir -p /opt/lms-edge/frontend", False),
    ("sudo chown -R raven:raven /opt/lms-edge", False),
    
    # 3. 复制项目文件
    ("cp -rf /home/raven/lms-edge/lms-edge/backend/* /opt/lms-edge/backend/", False),
    ("cp -rf /home/raven/lms-edge/lms-edge/frontend/* /opt/lms-edge/frontend/", False),
    
    # 4. 创建Python虚拟环境
    ("cd /opt/lms-edge/backend && python3 -m venv venv", False),
    
    # 5. 安装Python依赖
    ("cd /opt/lms-edge/backend && source venv/bin/activate && pip install --upgrade pip", False),
    ("cd /opt/lms-edge/backend && source venv/bin/activate && pip install fastapi uvicorn sqlalchemy aiosqlite pydantic pydantic-settings python-jose passlib bcrypt python-multipart python-dotenv websockets redis psutil jinja2", True),
    
    # 6. 构建前端
    ("cd /opt/lms-edge/frontend && npm install", True),
    ("cd /opt/lms-edge/frontend && npm run build", False),
    
    # 7. 配置Nginx
    ("""cat > /tmp/nginx.conf << 'NGINX'
server {
    listen 80;
    server_name _;
    root /opt/lms-edge/frontend/dist;
    index index.html;

    location /static/ {
        alias /opt/lms-edge/backend/static/;
        expires 30d;
    }

    location /uploads/ {
        alias /opt/lms-edge/backend/uploads/;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \\$host;
        proxy_set_header X-Real-IP \\$remote_addr;
        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \\$host;
    }

    location / {
        try_files \\$uri \\$uri/ /index.html;
    }
}
NGINX
""", False),
    
    ("sudo cp /tmp/nginx.conf /etc/nginx/sites-available/lms-edge", False),
    ("sudo ln -sf /etc/nginx/sites-available/lms-edge /etc/nginx/sites-enabled/", False),
    ("sudo rm -f /etc/nginx/sites-enabled/default", False),
    ("sudo nginx -t", False),
    ("sudo systemctl restart nginx", False),
]

print("LMS-Edge 完整部署")
print("=" * 50)
print("")
print("请在 Jetson Nano 上手动执行以下命令:")
print("")
for cmd in commands:
    if cmd[1]:  # Requires sudo
        print(f"需sudo: {cmd[0][:80]}...")
    else:
        print(cmd[0][:80])
print("")
print("=" * 50)
