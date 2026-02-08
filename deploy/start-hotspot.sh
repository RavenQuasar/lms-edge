#!/bin/bash
# LMS-Edge WiFi热点模式启动脚本
# 同时启动WiFi热点和LMS-Edge服务

set -e

SSID="LMS-Classroom"
PASSWORD="lmsedge123"
HOTSPOT_IP="10.42.0.1"
SERVER_PORT=8080

echo "========================================="
echo "  LMS-Edge WiFi热点模式启动"
echo "========================================="

# 检查root权限
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 检查Python服务是否存在
if [ ! -f "/home/raven/lms-edge/lms-edge/backend/simple_server.py" ]; then
    echo "错误: 找不到服务器脚本"
    exit 1
fi

# 停止现有热点连接
echo "停止现有WiFi连接..."
nmcli connection down "$SSID" 2>/dev/null || true
nmcli connection down pandass 2>/dev/null || true

sleep 1

# 创建或配置热点连接
echo "配置WiFi热点..."
nmcli connection delete "$SSID" 2>/dev/null || true

nmcli connection add \
    type wifi \
    con-name "$SSID" \
    ifname wlan0 \
    autoconnect no \
    ssid "$SSID" 2>/dev/null || true

nmcli connection modify "$SSID" \
    ipv4.method shared \
    ipv4.addresses "$HOTSPOT_IP/24" \
    wifi.mode ap \
    wifi-sec.key-mgmt wpa-psk \
    wifi-sec.psk "$PASSWORD"

# 启动热点
echo "启动WiFi热点..."
nmcli connection up "$SSID"

sleep 2

# 检查IP是否配置成功
ACTUAL_IP=$(ip addr show wlan0 | grep "inet " | awk '{print $2}' | cut -d'/' -f1)

if [ -z "$ACTUAL_IP" ]; then
    echo "❌ WiFi热点IP配置失败"
    exit 1
fi

# 启动LMS-Edge服务
echo ""
echo "启动LMS-Edge服务..."
cd /home/raven/lms-edge/lms-edge/backend

# 杀掉旧进程
pkill -f simple_server.py 2>/dev/null || true
sleep 1

# 启动新进程
nohup python3 simple_server.py > /tmp/lms-edge.log 2>&1 &
SERVER_PID=$!

sleep 2

echo ""
echo "========================================="
echo "  ✅ 启动完成!"
echo "========================================="
echo ""
echo "  WiFi热点信息:"
echo "    SSID: $SSID"
echo "    密码: $PASSWORD"
echo ""
echo "  LMS-Edge访问地址:"
echo "    http://$HOTSPOT_IP:$SERVER_PORT"
echo "    http://$ACTUAL_IP:$SERVER_PORT"
echo ""
echo "  API端点:"
echo "    http://$HOTSPOT_IP:$SERVER_PORT/api/health"
echo "    http://$HOTSPOT_IP:$SERVER_PORT/api/info"
echo ""
echo "  默认用户:"
echo "    admin / admin123"
echo "    teacher / teacher123"
echo "    student / student123"
echo ""
echo "========================================="
echo ""
echo "从手机或电脑连接WiFi '$SSID' 后，"
echo "在浏览器访问: http://$HOTSPOT_IP:$SERVER_PORT"
echo ""
