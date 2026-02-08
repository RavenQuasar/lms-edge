#!/bin/bash

# LMS-Edge Jetson Nano 部署脚本
# 此脚本用于在 Jetson Nano 上配置 AP 模式并部署 LMS-Edge 系统

set -e

echo "========================================="
echo "  LMS-Edge Jetson Nano 部署脚本"
echo "========================================="

# 配置变量
WIFI_INTERFACE="wlan0"
SSID="LMS-Classroom"
PASSWORD="lms123456"
IP_ADDRESS="192.168.1.1"
DHCP_START="192.168.1.100"
DHCP_END="192.168.1.200"
PROJECT_DIR="/opt/lms-edge"
USER="jetson"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# 检查是否为 root
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        log_error "请使用 root 权限运行此脚本"
        exit 1
    fi
}

# 更新系统
update_system() {
    log_info "更新系统..."
    apt-get update && apt-get upgrade -y
}

# 安装依赖
install_dependencies() {
    log_info "安装系统依赖..."
    apt-get install -y \
        hostapd \
        dnsmasq \
        python3 \
        python3-pip \
        python3-venv \
        nginx \
        git \
        curl \
        vim \
        htop
    
    systemctl stop hostapd
    systemctl stop dnsmasq
}

# 配置网络接口
configure_network() {
    log_info "配置网络接口..."
    
    # 配置静态 IP
    cat > /etc/network/interfaces.d/"$WIFI_INTERFACE" <<EOF
interface $WIFI_INTERFACE
    static ip_address=$IP_ADDRESS/24
    nohook wpa_supplicant
EOF
    
    # 重启网络
    systemctl restart networking
    
    log_info "已配置 IP 地址: $IP_ADDRESS"
}

# 配置 DHCP 服务器
configure_dhcp() {
    log_info "配置 DHCP 服务器..."
    
    # 备份原配置
    cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup
    
    # 配置 dnsmasq
    cat > /etc/dnsmasq.conf <<EOF
interface=$WIFI_INTERFACE
dhcp-range=$DHCP_START,$DHCP_END,255.255.255.0,24h
dhcp-option=3,$IP_ADDRESS
dhcp-option=6,$IP_ADDRESS
server=8.8.8.8
server=8.8.4.4
EOF
    
    log_info "DHCP 配置完成"
}

# 配置 AP 模式
configure_ap() {
    log_info "配置 AP 模式..."
    
    # 检查 hostapd 配置
    cat > /etc/hostapd/hostapd.conf <<EOF
interface=$WIFI_INTERFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF
    
    # 配置 hostapd 路径
    sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd
    
    # 创建 hostapd 服务（如果不存在）
    cat > /etc/systemd/system/hostapd.service <<EOF
[Unit]
Description=Hostapd IEEE 802.11 AP
After=network.target

[Service]
ExecStartPre=/sbin/iw dev $WIFI_INTERFACE interface add $WIFI_INTERFACE type __ap
ExecStart=/usr/sbin/hostapd /etc/hostapd/hostapd.conf
ExecStopPost=/sbin/iw dev $WIFI_INTERFACE del
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    
    log_info "AP 配置完成"
    log_info "SSID: $SSID"
    log_info "密码: $PASSWORD"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    # 启用 IP 转发
    sed -i 's|#net.ipv4.ip_forward=1|net.ipv4.ip_forward=1|' /etc/sysctl.conf
    sysctl -p
    
    # 配置 NAT
    iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
    iptables -A FORWARD -i eth0 -o $WIFI_INTERFACE -m state --state RELATED,ESTABLISHED -j ACCEPT
    iptables -A FORWARD -i $WIFI_INTERFACE -o eth0 -j ACCEPT
    
    # 保存规则
    iptables-save > /etc/iptables.ipv4.nat
    
    # 创建启动脚本
    cat > /etc/rc.local <<EOF
#!/bin/sh -e
iptables-restore < /etc/iptables.ipv4.nat
exit 0
EOF
    chmod +x /etc/rc.local
    
    log_info "防火墙配置完成"
}

# 创建项目目录
create_project_dir() {
    log_info "创建项目目录..."
    mkdir -p $PROJECT_DIR
    mkdir -p $PROJECT_DIR/data
    mkdir -p $PROJECT_DIR/logs
    mkdir -p $PROJECT_DIR/uploads
    
    # 设置权限
    chown -R $USER:$USER $PROJECT_DIR
}

# 安装 Python 依赖
install_python_deps() {
    log_info "安装 Python 依赖..."
    
    cd $PROJECT_DIR
    
    # 创建虚拟环境
    su - $USER -c "cd $PROJECT_DIR && python3 -m venv venv"
    
    # 安装依赖
    su - $USER -c "cd $PROJECT_DIR && source venv/bin/activate && pip install --upgrade pip"
    
    log_info "Python 依赖安装完成"
}

# 创建 systemd 服务
create_service() {
    log_info "创建 systemd 服务..."
    
    cat > /etc/systemd/system/lms-edge.service <<EOF
[Unit]
Description=LMS-Edge Backend Service
After=network.target hostapd.service dnsmasq.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable lms-edge.service
    
    log_info "Systemd 服务创建完成"
}

# 配置 Nginx
configure_nginx() {
    log_info "配置 Nginx..."
    
    cat > /etc/nginx/sites-available/lms-edge <<EOF
server {
    listen 80;
    server_name _;

    # 静态文件
    location / {
        root $PROJECT_DIR/backend/static;
        try_files \$uri \$uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    # WebSocket 代理
    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    # 上传文件
    location /uploads/ {
        alias $PROJECT_DIR/backend/uploads/;
    }
EOF
    
    ln -sf /etc/nginx/sites-available/lms-edge /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    systemctl restart nginx
    
    log_info "Nginx 配置完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 启动 AP 服务
    systemctl unmask hostapd
    systemctl enable hostapd
    systemctl start hostapd
    
    # 启动 DHCP
    systemctl enable dnsmasq
    systemctl start dnsmasq
    
    log_info "所有服务已启动"
}

# 显示摘要
show_summary() {
    log_info "========================================="
    log_info "  部署完成！"
    log_info "========================================="
    echo ""
    echo "访问信息:"
    echo "  - 本地访问: http://localhost"
    echo "  - 局域网访问: http://$IP_ADDRESS"
    echo "  - WiFi SSID: $SSID"
    echo "  - WiFi 密码: $PASSWORD"
    echo ""
    echo "默认用户:"
    echo "  - 管理员: admin / admin123"
    echo "  - 老师: teacher / teacher123"
    echo "  - 学生: student / student123"
    echo ""
    echo "服务管理:"
    echo "  - 启动服务: systemctl start lms-edge"
    echo "  - 停止服务: systemctl stop lms-edge"
    echo "  - 查看日志: journalctl -u lms-edge -f"
    echo ""
    log_warn "请及时修改默认密码！"
}

# 主函数
main() {
    check_root
    update_system
    install_dependencies
    configure_network
    configure_dhcp
    configure_ap
    configure_firewall
    create_project_dir
    install_python_deps
    create_service
    configure_nginx
    start_services
    show_summary
    
    log_info "部署成功完成！"
    log_warn "请重启系统以使所有配置生效"
}

# 执行主函数
main
