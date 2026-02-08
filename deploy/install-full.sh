#!/bin/bash
# LMS-Edge 完整部署脚本
# 在 Jetson Nano 上以 root 权限运行

set -e

echo "========================================="
echo "  LMS-Edge 完整部署脚本"
echo "========================================="
echo ""

PROJECT_DIR="/opt/lms-edge"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# 1. 安装系统依赖
echo "[1/7] 安装系统依赖..."
apt-get update
apt-get install -y nginx python3-pip python3-venv git nodejs npm

# 2. 创建项目目录
echo "[2/7] 创建项目目录..."
mkdir -p "$BACKEND_DIR"/{data,logs,uploads,static}
mkdir -p "$FRONTEND_DIR"
chown -R raven:raven "$PROJECT_DIR" 2>/dev/null || true

# 3. 复制项目文件
echo "[3/7] 复制项目文件..."
cp -rf /home/raven/lms-edge/lms-edge/backend/* "$BACKEND_DIR/" 2>/dev/null || true
cp -rf /home/raven/lms-edge/lms-edge/frontend/* "$FRONTEND_DIR/" 2>/dev/null || true

# 4. 创建 Python 虚拟环境
echo "[4/7] 创建 Python 虚拟环境..."
cd "$BACKEND_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic pydantic-settings \
    python-jose passlib bcrypt python-multipart python-dotenv websockets \
    redis psutil jinja2 python-multipart

# 5. 构建前端
echo "[5/7] 构建前端..."
cd "$FRONTEND_DIR"
npm install
npm run build

# 6. 配置 nginx
echo "[6/7] 配置 nginx..."
cat > /etc/nginx/sites-available/lms-edge << 'EOF'
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
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

ln -sf /etc/nginx/sites-available/lms-edge /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# 7. 启动后端服务
echo "[7/7] 启动后端服务..."
cd "$BACKEND_DIR"

# 杀掉旧进程
pkill -f "uvicorn" 2>/dev/null || true
sleep 1

# 启动新进程
source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > "$BACKEND_DIR/logs/lms.log" 2>&1 &
sleep 2

echo ""
echo "========================================="
echo "  部署完成!"
echo "========================================="
echo ""
echo "访问地址: http://$(hostname -I | awk '{print $1}')"
echo ""
echo "管理命令:"
echo "  查看日志: tail -f $BACKEND_DIR/logs/lms.log"
echo "  重启服务: cd $BACKEND_DIR && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000"
echo ""
echo "测试账号:"
echo "  管理员: admin / admin123"
echo "  老师:   teacher / teacher123"
echo "  学生:   student / student123"
echo ""
