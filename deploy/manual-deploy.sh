#!/bin/bash

# LMS-Edge 手动部署脚本 - Jetson Nano
# 使用方法: 将此脚本上传到 Jetson Nano 并运行

set -e

PROJECT_DIR="$HOME/lms-edge"

echo "========================================="
echo "  LMS-Edge Jetson Nano 部署"
echo "========================================="

# 1. 安装系统依赖
echo "[1/6] 安装系统依赖..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git nginx

# 2. 创建项目目录
echo "[2/6] 创建项目目录..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 3. 创建 Python 虚拟环境
echo "[3/6] 创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# 4. 安装 Python 依赖
echo "[4/6] 安装 Python 依赖..."
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic pydantic-settings python-jose passlib bcrypt python-multipart websockets redis python-dotenv psutil reportlab matplotlib pandas

# 5. 初始化数据库
echo "[5/6] 初始化数据库..."
cd $PROJECT_DIR
mkdir -p data logs uploads static

python3 -c "
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.models.user import User, UserRole
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.models.attendance import Attendance
from app.models.board import BoardLog, BoardMessage
from app.core.database import Base
from app.core.security import get_password_hash
import asyncio

async def init():
    engine = create_async_engine('sqlite+aiosqlite:///./data/lms.db', echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    
    async with AsyncSession(engine) as session:
        result = await session.execute(select(User).where(User.username == 'admin'))
        if not result.scalar_one_or_none():
            admin = User(username='admin', full_name='Administrator', role=UserRole.ADMIN, password_hash=get_password_hash('admin123'))
            session.add(admin)
        
        result = await session.execute(select(User).where(User.username == 'teacher'))
        if not result.scalar_one_or_none():
            teacher = User(username='teacher', full_name='Teacher', role=UserRole.TEACHER, password_hash=get_password_hash('teacher123'))
            session.add(teacher)
        
        result = await session.execute(select(User).where(User.username == 'student'))
        if not result.scalar_one_or_none():
            student = User(username='student', full_name='Student', role=UserRole.STUDENT, password_hash=get_password_hash('student123'))
            session.add(student)
        
        await session.commit()
        print('默认用户创建完成')

asyncio.run(init())
"

echo "✓ 数据库初始化完成"

# 6. 启动服务
echo "[6/6] 启动服务..."
cd $PROJECT_DIR/backend

# 创建启动脚本
cat > start_server.sh << 'STARTSCRIPT'
#!/bin/bash
cd $(dirname "$0")
source venv/bin/activate
export PYTHONPATH=$(pwd)
python main.py
STARTSCRIPT

chmod +x start_server.sh

# 后台启动服务
nohup ./start_server.sh > ../logs/lms-edge.log 2>&1 &
SERVER_PID=$!

sleep 3

# 检查服务状态
if ps -p $SERVER_PID > /dev/null; then
    echo ""
    echo "========================================="
    echo "  ✓ 部署成功！"
    echo "========================================="
    echo ""
    echo "访问地址:"
    echo "  - 本地访问: http://localhost:8000"
    echo "  - API文档:  http://localhost:8000/docs"
    echo ""
    echo "默认用户:"
    echo "  - 管理员: admin / admin123"
    echo "  - 老师:   teacher / teacher123"
    echo "  - 学生:   student / student123"
    echo ""
    echo "服务 PID: $SERVER_PID"
    echo "日志位置: $PROJECT_DIR/logs/lms-edge.log"
    echo ""
    echo "停止服务: kill $SERVER_PID"
else
    echo "✗ 服务启动失败，请查看日志: $PROJECT_DIR/logs/lms-edge.log"
fi

STARTSCRIPT

chmod +x manual-deploy.sh

echo ""
echo "部署脚本已创建: $PROJECT_DIR/manual-deploy.sh"
echo "请运行: cd $PROJECT_DIR && bash manual-deploy.sh"
