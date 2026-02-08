# LMS-Edge - 班级局域网教学管理系统

## 项目概述

LMS-Edge 是专为 Jetson Nano 设计的班级局域网教学管理系统，提供实时教学互动、作业管理、考勤统计等功能。

## 技术栈

### 后端
- FastAPI - 高性能异步 Web 框架
- SQLAlchemy + SQLite - ORM 和数据库
- WebSocket - 实时通信
- Pydantic - 数据验证

### 前端（待开发）
- Vue.js / React
- Tailwind CSS
- Socket.io-client

## 目录结构

```
lms-edge/
├── backend/
│   ├── app/
│   │   ├── api/              # API 路由
│   │   ├── core/             # 核心配置
│   │   ├── models/           # 数据库模型
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── websocket/        # WebSocket 管理
│   │   └── services/         # 业务逻辑服务
│   ├── static/               # 静态文件
│   ├── uploads/              # 上传文件
│   ├── data/                 # 数据库文件
│   ├── logs/                 # 日志文件
│   ├── main.py               # 应用入口
│   ├── init_users.py         # 初始化默认用户
│   ├── requirements.txt      # Python 依赖
│   └── .env                  # 环境配置
├── frontend/                 # 前端代码
│   ├── src/
│   │   ├── components/       # Vue/React 组件
│   │   ├── pages/            # 页面组件
│   │   ├── services/         # API 服务
│   │   ├── stores/           # 状态管理
│   │   └── utils/            # 工具函数
│   └── public/               # 静态资源
├── deploy/                   # 部署脚本
└── data/                     # 持久化数据
```

## 快速开始

### 后端设置

1. 进入后端目录：
```bash
cd lms-edge/backend
```

2. 创建虚拟环境（可选）：
```bash
python3 -m venv venv
source venv/bin/activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 初始化数据库和默认用户：
```bash
python init_users.py
```

5. 启动服务器：
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

或使用启动脚本：
```bash
chmod +x start.sh
./start.sh
```

### 默认用户

系统会自动创建以下默认用户：

| 角色   | 用户名  | 密码     |
|--------|---------|----------|
| 管理员 | admin   | admin123 |
| 老师   | teacher | teacher123|
| 学生   | student | student123|

**请及时修改默认密码！**

## API 文档

启动服务器后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 核心功能

### 1. 用户认证与权限
- JWT Token 认证
- 三种角色权限（管理员/老师/学生）
- 用户管理 API

### 2. 实时通信（WebSocket）
- 在线状态监控
- 共享白板
- 实时签到
- 课堂互动消息

### 3. 作业管理
- 题目创建（单选/多选/判断/简答）
- 学生提交作业
- 自动阅卷（客观题）
- 手动评分（主观题）
- 随堂测验

### 4. 考勤管理
- 实时签到系统
- 在线时长统计
- 活跃度追踪
- 迟到记录

### 5. 统计分析
- 个人学习数据
- 班级整体统计
- 成绩趋势分析
- 数据导出（CSV/PDF）

### 6. 系统监控
- CPU/内存使用率
- 磁盘空间
- 温度监控（Jetson Nano）
- 日志查看

## Jetson Nano 优化

### 1. AP 模式配置
在 Jetson Nano 上启用无线热点，为学生设备提供局域网访问。

### 2. 性能优化
- 静态资源本地缓存
- 数据库持久化到外部存储
- WebSocket 连接池优化

### 3. 系统监控
- 实时监控硬件状态
- 温度过高预警
- 自动日志记录

## 部署说明

详细的 Jetson Nano 部署脚本请参考 `deploy/` 目录。

## 开发进度

- [x] 项目初始化和目录结构
- [x] 后端 FastAPI 框架
- [x] 数据库模型设计
- [x] 用户认证系统
- [x] WebSocket 实时通信
- [x] 作业管理 API
- [x] 考勤管理 API
- [x] 统计分析 API
- [ ] 前端 Vue.js/React 框架
- [ ] 前端页面开发
- [ ] Jetson Nano 部署脚本

## 许可证

本项目仅供学习和教学使用。

## 联系方式

如有问题或建议，请提交 Issue。
