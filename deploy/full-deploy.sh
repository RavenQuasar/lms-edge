#!/bin/bash
# LMS-Edge 完整部署脚本
# 在 Jetson Nano 上运行此脚本

echo "========================================="
echo "  LMS-Edge 完整部署"
echo "========================================="

# 检查root权限
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 1. 安装系统依赖
echo "[1/6] 安装系统依赖..."
apt-get update
apt-get install -y nginx python3-pip python3-venv git

# 2. 创建项目目录
echo "[2/6] 创建项目目录..."
mkdir -p /opt/lms-edge/backend/{data,logs,uploads,static}
mkdir -p /opt/lms-edge/frontend

# 3. 创建Python虚拟环境
echo "[3/6] 创建Python虚拟环境..."
cd /opt/lms-edge/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# 4. 安装Python依赖
echo "[4/6] 安装Python依赖..."
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic pydantic-settings \
    python-jose passlib bcrypt python-multipart python-dotenv websockets \
    redis psutil jinja2

# 5. 复制项目文件
echo "[5/6] 复制项目文件..."
cp -r /home/raven/lms-edge/lms-edge/backend/* /opt/lms-edge/backend/
cp -r /home/raven/lms-edge/lms-edge/frontend/* /opt/lms-edge/frontend/

# 6. 配置Nginx
echo "[6/6] 配置Nginx..."

cat > /etc/nginx/sites-available/lms-edge << 'EOF'
server {
    listen 80;
    server_name _;
    root /opt/lms-edge/frontend/dist;
    index index.html;

    # 静态文件缓存
    location /static/ {
        alias /opt/lms-edge/backend/static/;
        expires 30d;
    }

    location /uploads/ {
        alias /opt/lms-edge/backend/uploads/;
    }

    # API代理到FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket代理
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 前端路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

ln -sf /etc/nginx/sites-available/lms-edge /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 重启Nginx
systemctl restart nginx

echo ""
echo "========================================="
echo "  部署完成!"
echo "========================================="
echo ""
echo "访问地址: http://<jetson-ip>"
echo ""
echo "后续步骤:"
echo "  1. 构建前端: cd /opt/lms-edge/frontend && npm install && npm run build"
echo "  2. 启动后端: cd /opt/lms-edge/backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000"
echo ""
