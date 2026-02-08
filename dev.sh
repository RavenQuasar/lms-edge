#!/bin/bash

# LMS-Edge 开发环境启动脚本

cd "$(dirname "$0")/.."

BACKEND_DIR="./backend"
FRONTEND_DIR="./frontend"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================="
echo "  LMS-Edge 开发环境启动"
echo "========================================="
echo ""

# 检查后端依赖
echo -e "${GREEN}[1/4]${NC} 检查后端依赖..."
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "创建后端虚拟环境..."
    cd "$BACKEND_DIR"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo "后端虚拟环境已存在"
fi

# 检查前端依赖
echo -e "${GREEN}[2/4]${NC} 检查前端依赖..."
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "安装前端依赖..."
    cd "$FRONTEND_DIR"
    npm install
    cd ..
else
    echo "前端依赖已安装"
fi

# 初始化数据库
echo -e "${GREEN}[3/4]${NC} 初始化数据库..."
cd "$BACKEND_DIR"
source venv/bin/activate
python init_users.py
cd ..

# 启动服务
echo -e "${GREEN}[4/4]${NC} 启动服务..."
echo ""
echo "后端服务: http://localhost:8000"
echo "前端服务: http://localhost:3000"
echo "API 文档: http://localhost:8000/docs"
echo ""

# 启动后端
cd "$BACKEND_DIR"
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动前端
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo -e "${GREEN}服务已启动！${NC}"
echo "后端 PID: $BACKEND_PID"
echo "前端 PID: $FRONTEND_PID"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待中断信号
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

wait
