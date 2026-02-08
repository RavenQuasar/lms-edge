#!/bin/bash

# LMS-Edge 快速部署脚本
# 用于快速部署 LMS-Edge 系统到 Jetson Nano

set -e

echo "========================================="
echo "  LMS-Edge 快速部署脚本"
echo "========================================="

PROJECT_DIR="/opt/lms-edge"
USER="jetson"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统
check_system() {
    log_info "检查系统环境..."
    
    # 检查 Python 版本
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    log_info "Python 版本: $python_version"
    
    # 检查可用空间
    available_space=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$available_space" -lt 5 ]; then
        log_error "磁盘空间不足，至少需要 5GB 可用空间"
        exit 1
    fi
    
    log_info "系统检查通过"
}

# 创建项目目录
setup_directories() {
    log_info "创建项目目录..."
    
    mkdir -p $PROJECT_DIR
    mkdir -p $PROJECT_DIR/backend/{data,logs,uploads,static}
    
    # 设置权限
    if id "$USER" &>/dev/null; then
        chown -R $USER:$USER $PROJECT_DIR
    fi
    
    log_info "目录创建完成: $PROJECT_DIR"
}

# 安装 Python 依赖
install_python() {
    log_info "安装 Python 依赖..."
    
    apt-get update
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        git \
        curl
    
    log_info "Python 依赖安装完成"
}

# 安装项目依赖
install_project_deps() {
    log_info "安装项目依赖..."
    
    cd $PROJECT_DIR/backend
    
    # 创建虚拟环境
    python3 -m venv venv
    
    # 激活虚拟环境并安装依赖
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log_info "项目依赖安装完成"
}

# 创建默认用户
create_users() {
    log_info "创建默认用户..."
    
    cd $PROJECT_DIR/backend
    source venv/bin/activate
    
    python init_users.py
    
    log_info "默认用户创建完成"
}

# 构建前端
build_frontend() {
    log_info "构建前端..."
    
    cd $PROJECT_DIR/frontend
    
    if [ -f "package.json" ]; then
        # 安装 Node.js 依赖
        if ! command -v node &> /dev/null; then
            log_info "安装 Node.js..."
            curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
            apt-get install -y nodejs
        fi
        
        npm install
        npm run build
    else
        log_warn "前端 package.json 不存在，跳过构建"
    fi
    
    log_info "前端构建完成"
}

# 创建 systemd 服务
create_service() {
    log_info "创建 systemd 服务..."
    
    cat > /etc/systemd/system/lms-edge.service <<EOF
[Unit]
Description=LMS-Edge Backend Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR/backend
Environment="PATH=$PROJECT_DIR/backend/venv/bin"
ExecStart=$PROJECT_DIR/backend/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=lms-edge

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable lms-edge.service
    
    log_info "Systemd 服务创建完成"
}

# 启动服务
start_service() {
    log_info "启动 LMS-Edge 服务..."
    
    systemctl start lms-edge.service
    
    sleep 3
    
    # 检查服务状态
    if systemctl is-active --quiet lms-edge.service; then
        log_info "LMS-Edge 服务启动成功"
    else
        log_error "LMS-Edge 服务启动失败"
        log_info "查看日志: journalctl -u lms-edge -n 50"
        exit 1
    fi
}

# 显示摘要
show_summary() {
    log_info "========================================="
    log_info "  部署完成！"
    log_info "========================================="
    echo ""
    echo "访问信息:"
    echo "  - 本地访问: http://localhost:8000"
    echo "  - API 文档: http://localhost:8000/docs"
    echo ""
    echo "默认用户:"
    echo "  - 管理员: admin / admin123"
    echo "  - 老师: teacher / teacher123"
    echo "  - 学生: student / student123"
    echo ""
    echo "服务管理:"
    echo "  - 启动服务: systemctl start lms-edge"
    echo "  - 停止服务: systemctl stop lms-edge"
    echo "  - 重启服务: systemctl restart lms-edge"
    echo "  - 查看状态: systemctl status lms-edge"
    echo "  - 查看日志: journalctl -u lms-edge -f"
    echo ""
    log_warn "请及时修改默认密码！"
}

# 主函数
main() {
    check_system
    setup_directories
    install_python
    install_project_deps
    create_users
    build_frontend
    create_service
    start_service
    show_summary
    
    log_info "部署成功完成！"
}

# 执行主函数
main
