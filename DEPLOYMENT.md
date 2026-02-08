# LMS-Edge 部署指南

本文档说明如何在 Jetson Nano 上部署 LMS-Edge 班级局域网教学管理系统。

## 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [完整部署（含 AP 模式）](#完整部署含-ap-模式)
- [服务管理](#服务管理)
- [故障排除](#故障排除)

## 系统要求

### 硬件要求
- Jetson Nano (4GB/2GB)
- 支持的 WiFi 模块（用于 AP 模式）
- 至少 16GB 的 SD 卡或 SSD
- 稳定的电源供应

### 软件要求
- Ubuntu 18.04/20.04 LTS (JetPack 4.x/5.x)
- Python 3.6+
- Node.js 14+ (开发环境)

## 快速开始

### 1. 准备系统

更新系统并安装基础依赖：

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y git python3 python3-pip python3-venv nginx
```

### 2. 克隆项目

```bash
cd /opt
sudo git clone <repository-url> lms-edge
cd lms-edge
sudo chown -R $USER:$USER .
```

### 3. 运行快速部署脚本

```bash
chmod +x deploy/quick-deploy.sh
sudo ./deploy/quick-deploy.sh
```

### 4. 访问系统

部署完成后，可以通过以下地址访问系统：

- 本地访问: `http://localhost:8000`
- API 文档: `http://localhost:8000/docs`
- 局域网访问: `http://<jetson-ip>:8000`

## 完整部署（含 AP 模式）

此配置将 Jetson Nano 配置为无线热点，学生设备可以直接连接。

### 1. 准备部署脚本

```bash
cd /opt/lms-edge
chmod +x deploy/deploy.sh
```

### 2. 修改配置（可选）

编辑 `deploy/deploy.sh` 中的配置变量：

```bash
WIFI_INTERFACE="wlan0"      # WiFi 接口名称
SSID="LMS-Classroom"        # WiFi 名称
PASSWORD="lms123456"        # WiFi 密码
IP_ADDRESS="192.168.1.1"    # Jetson Nano 的 IP 地址
USER="jetson"               # 运行服务的用户
```

### 3. 运行完整部署脚本

```bash
sudo ./deploy/deploy.sh
```

### 4. 重启系统

```bash
sudo reboot
```

### 5. 连接 WiFi

学生设备可以搜索并连接到 WiFi 热点：

- SSID: `LMS-Classroom`（可自定义）
- 密码: `lms123456`（可自定义）

连接后访问: `http://192.168.1.1`

## 服务管理

### 启动/停止/重启服务

```bash
# 启动服务
sudo systemctl start lms-edge

# 停止服务
sudo systemctl stop lms-edge

# 重启服务
sudo systemctl restart lms-edge

# 查看服务状态
sudo systemctl status lms-edge
```

### 查看日志

```bash
# 实时查看日志
sudo journalctl -u lms-edge -f

# 查看最近 100 行日志
sudo journalctl -u lms-edge -n 100

# 查看今天的服务日志
sudo journalctl -u lms-edge --since today
```

### 更新系统

```bash
# 停止服务
sudo systemctl stop lms-edge

# 拉取最新代码
cd /opt/lms-edge
git pull

# 更新依赖
source backend/venv/bin/activate
cd backend
pip install -r requirements.txt

# 构建前端（如果有更新）
cd ../frontend
npm install
npm run build

# 启动服务
sudo systemctl start lms-edge
```

## 网络配置

### 静态 IP 配置

如果需要修改 Jetson Nano 的 IP 地址，编辑：

```bash
sudo nano /etc/network/interfaces.d/wlan0
```

修改 `static ip_address` 为所需地址，然后重启网络服务：

```bash
sudo systemctl restart networking
```

### DHCP 范围配置

修改 DHCP 分配的 IP 范围：

```bash
sudo nano /etc/dnsmasq.conf
```

修改 `dhcp-range` 参数，然后重启服务：

```bash
sudo systemctl restart dnsmasq
```

## 开发环境

### 启动开发环境

在项目根目录运行：

```bash
chmod +x dev.sh
./dev.sh
```

这将：
1. 自动检查和安装依赖
2. 初始化数据库
3. 启动后端服务（端口 8000）
4. 启动前端开发服务器（端口 3000）

### 手动启动后端

```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 手动启动前端

```bash
cd frontend
npm run dev
```

## 故障排除

### AP 模式无法启动

1. 检查 WiFi 接口：
```bash
iwconfig
```

2. 检查 hostapd 服务状态：
```bash
sudo systemctl status hostapd
```

3. 查看详细日志：
```bash
sudo journalctl -xe -u hostapd
```

### 服务无法启动

1. 检查服务状态：
```bash
sudo systemctl status lms-edge
```

2. 查看错误日志：
```bash
sudo journalctl -u lms-edge -n 50
```

3. 手动测试：
```bash
cd /opt/lms-edge/backend
source venv/bin/activate
python main.py
```

### 无法访问系统

1. 检查防火墙：
```bash
sudo ufw status
sudo ufw allow 8000/tcp
```

2. 检查端口监听：
```bash
sudo netstat -tulpn | grep 8000
```

3. 测试本地连接：
```bash
curl http://localhost:8000
```

### 数据库问题

如果数据库出现问题，可以重建数据库：

```bash
cd /opt/lms-edge/backend
rm data/lms.db
source venv/bin/activate
python init_users.py
```

### 性能优化

Jetson Nano 的资源有限，可以进行以下优化：

1. 启用最大性能模式：
```bash
sudo nvpmodel -m 0
sudo jetson_clocks
```

2. 增加 swap 空间：
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

3. 监控系统资源：
```bash
htop
sudo tegrastats
```

## 安全建议

1. **修改默认密码**: 登录后立即修改所有默认用户密码
2. **使用 HTTPS**: 在生产环境中配置 SSL 证书
3. **定期备份**: 定期备份数据库和上传文件
4. **限制访问**: 使用防火墙限制不必要的端口访问
5. **更新系统**: 定期更新系统和依赖包

## 支持

如有问题或建议，请：
- 提交 Issue 到项目仓库
- 查看 API 文档: `http://<your-ip>:8000/docs`
- 查看系统日志进行故障排除
