#!/bin/bash
# Jetson Nano WiFi 热点配置脚本
# 运行此脚本将WiFi配置为热点模式

echo "========================================="
echo "  Jetson Nano WiFi 热点配置"
echo "========================================="

# 检查是否为root
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

SSID="LMS-Classroom"
PASSWORD="lmsedge123"
HOTSPOT_IP="10.42.0.1"

echo ""
echo "配置信息:"
echo "  SSID: $SSID"
echo "  密码: $PASSWORD"
echo "  IP:   $HOTSPOT_IP"
echo ""

# 创建NetworkManager热点连接
echo "创建WiFi热点连接..."
nmcli connection add \
    type wifi \
    con-name "$SSID" \
    ifname wlan0 \
    autoconnect no \
    ssid "$SSID"

# 配置WiFi接口为共享模式
echo "配置WiFi接口..."
nmcli connection modify "$SSID" \
    ipv4.method shared \
    ipv4.addresses "$HOTSPOT_IP/24" \
    wifi.mode ap \
    wifi-sec.key-mgmt wpa-psk \
    wifi-sec.psk "$PASSWORD"

# 停止现有WiFi连接
echo "停止现有WiFi连接..."
nmcli connection down pandass 2>/dev/null || true

# 启动热点
echo ""
echo "启动WiFi热点..."
nmcli connection up "$SSID"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ WiFi热点已启动!"
    echo ""
    echo "========================================="
    echo "  连接信息:"
    echo "========================================="
    echo "  WiFi名称: $SSID"
    echo "  密码: $PASSWORD"
    echo "  访问地址: http://$HOTSPOT_IP:8080"
    echo ""
    echo "从其他设备连接此WiFi后，访问:"
    echo "  http://$HOTSPOT_IP:8080"
    echo "========================================="
else
    echo "❌ 热点启动失败"
fi
