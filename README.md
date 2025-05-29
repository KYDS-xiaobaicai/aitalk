# AI Talk - 智能对话系统

基于 FastAPI + Vue 3 的全栈 AI 对话系统，支持多用户、多对话管理，集成通义千问 API。

## 🏗️ 技术架构

### 后端技术栈
- **FastAPI 0.104.1** - 现代化 Python Web 框架
- **MySQL** - 关系型数据库
- **SQLAlchemy** - ORM 框架
- **JWT** - 用户认证
- **通义千问 API** - AI 对话服务
- **Pydantic** - 数据验证
- **Pytest** - 测试框架

### 前端技术栈
- **Vue 3** - 渐进式 JavaScript 框架
- **Element Plus** - Vue 3 组件库
- **Vue Router** - 路由管理
- **Axios** - HTTP 客户端
- **Vite** - 前端构建工具

## 🚀 快速开始

### 环境要求
- Python 3.10+（我用的3.12.9）
- Node.js 18+（我用的18.20.3）
- MySQL 8.0

### 1. 克隆项目
```bash
git clone <repository-url>
cd aitalk
```

### 2. 后端设置

#### 安装 Python 依赖
```bash
pip install -r requirements.txt
```

#### 配置环境变量
创建 `.env` 文件：
```env
# 数据库配置
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/aitalk_db

# JWT配置
SECRET_KEY=your-secret-key-here-change-in-production

# 通义千问API配置
DASHSCOPE_API_KEY=your-dashscope-api-key
```

#### 初始化数据库
```bash
# 创建数据库（确保 MySQL 服务运行）
mysql -u root -p -e "CREATE DATABASE aitalk_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 启动应用（会自动创建表）
uvicorn app.main:app --reload
```

### 3. 前端设置

#### 安装 Node.js 依赖
```bash
cd frontend
npm install
```

#### 启动前端开发服务器
```bash
npm run dev
```

## 📱 访问地址

- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **交互式文档**: http://localhost:8000/redoc

## 🎯 功能特性

### 🔐 用户认证与授权
- 用户注册和登录
- JWT 令牌认证
- 完整的访问控制列表 (ACL)
- 密码加密存储

### 💬 对话管理
- 创建新对话
- 查看对话列表
- 修改对话标题
- 删除对话
- 支持多对话并行

### 🤖 AI 智能交互
- 集成通义千问 API
- 支持流式和非流式输出
- 实时消息发送和接收
- 消息历史记录
- 智能上下文理解

### 🎨 用户界面
- 现代化响应式设计
- 直观的聊天界面
- 实时消息状态
- 优雅的加载动画
- 移动端适配

## 📁 项目结构

```
aitalk/
├── backend/                # 后端应用
│   ├── app/               # 应用核心
│   │   ├── api/           # API 路由
│   │   │   ├── auth.py            # 认证相关
│   │   │   ├── conversations.py   # 对话管理
│   │   │   └── messages.py        # 消息处理
│   │   ├── models/        # 数据模型
│   │   │   ├── user.py            # 用户模型
│   │   │   ├── conversation.py    # 对话模型
│   │   │   └── message.py         # 消息模型
│   │   ├── schemas/       # Pydantic 模式
│   │   │   ├── user.py            # 用户模式
│   │   │   ├── conversation.py    # 对话模式
│   │   │   └── message.py         # 消息模式
│   │   ├── services/      # 业务逻辑
│   │   │   ├── auth.py            # 认证服务
│   │   │   ├── conversation.py    # 对话服务
│   │   │   └── ai.py              # AI 服务
│   │   ├── utils/         # 工具函数
│   │   │   ├── dependencies.py    # 依赖项
│   │   │   └── security.py        # 安全工具
│   │   ├── config.py      # 配置管理
│   │   ├── database.py    # 数据库连接
│   │   └── main.py        # 应用入口
│   ├── tests/             # 测试文件
│   │   ├── test_api.py            # API 测试
│   │   ├── test_services.py       # 服务测试
│   │   └── test_security.py       # 安全测试
│   ├── requirements.txt   # Python 依赖
│   └── run_tests.py       # 测试启动脚本
├── frontend/              # 前端应用
│   ├── src/               # 源代码
│   │   ├── api/           # API 调用
│   │   ├── views/         # 页面组件
│   │   │   ├── Login.vue           # 登录/注册页面
│   │   │   └── Chat.vue            # 聊天页面
│   │   ├── router/        # 路由配置
│   │   ├── App.vue        # 根组件
│   │   └── main.js        # 入口文件
│   ├── public/            # 静态资源
│   ├── index.html         # HTML 模板
│   ├── vite.config.js     # Vite 配置
│   └── package.json       # 依赖配置
└── README.md              # 项目说明
```

## 🔧 API 接口

### 认证接口
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 对话接口
- `GET /api/conversations` - 获取对话列表
- `POST /api/conversations` - 创建新对话
- `GET /api/conversations/{id}` - 获取对话详情
- `PUT /api/conversations/{id}` - 更新对话标题
- `DELETE /api/conversations/{id}` - 删除对话

### 消息接口
- `GET /api/conversations/{id}/messages` - 获取消息列表
- `POST /api/conversations/{id}/messages` - 发送消息
- `POST /api/conversations/{id}/messages/stream` - 流式发送消息

## 🧪 测试

### 运行所有测试
```bash
python run_tests.py
```

### 运行特定测试
```bash
# API 测试
pytest tests/test_api.py -v

# 服务测试
pytest tests/test_services.py -v

# 安全测试
pytest tests/test_security.py -v
```

### 测试覆盖率
```bash
pytest --cov=app --cov-report=html
```

## 🔒 安全特性

- **密码安全**: bcrypt 加密存储
- **JWT 安全**: 令牌过期和刷新机制
- **输入验证**: Pydantic 数据验证
- **SQL 注入防护**: SQLAlchemy ORM 保护
- **XSS 防护**: 输入过滤和输出编码
- **CORS 配置**: 跨域请求控制

## 🚀 部署

### 后端部署（宝塔面板）

#### 安装 Python 环境
在宝塔面板中：
1. 进入【软件商店】，安装 Python 项目管理器
2. 创建新的 Python 项目，选择 Python 3.12.9 版本
3. 上传项目后端代码到指定目录

#### 配置环境变量
创建 `.env` 文件：
```env
# 数据库配置
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/aitalk_db

# JWT配置
SECRET_KEY=your-secret-key-here-change-in-production

# 通义千问API配置
DASHSCOPE_API_KEY=your-dashscope-api-key
```

#### 安装依赖并启动
```bash
# 安装依赖
pip install -r requirements.txt

# 创建数据库
mysql -u root -p -e "CREATE DATABASE aitalk_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 配置反向代理
在宝塔面板中配置网站，添加反向代理规则：
- 代理名称：api
- 目标URL：http://127.0.0.1:8000
- 发送域名：$host

### 前端部署（服务器）

#### 安装 Node.js
```bash
# 安装 NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
source ~/.bashrc

# 安装 Node.js
nvm install 18
```

#### 安装 PM2
```bash
npm install -g pm2
```

#### 构建与部署
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 修改 vite.config.js 中的 API 代理地址为实际后端地址
# 构建生产版本
npm run build

# 使用 PM2 启动
pm2 serve dist 3000 --name aitalk-frontend --spa
```

#### PM2 管理命令
```bash
# 查看应用状态
pm2 status

# 查看日志
pm2 logs aitalk-frontend

# 重启应用
pm2 restart aitalk-frontend

# 设置开机自启
pm2 startup
pm2 save
```

### 访问地址
- 前端界面: http://您的域名:3000
- 后端 API: http://您的域名/api
- API 文档: http://您的域名/api/docs

## 📝 开发说明

### 代码规范
- 后端遵循 PEP 8 规范
- 前端使用 ESLint + Prettier
- 提交信息遵循 Conventional Commits

### 开发流程
1. 创建功能分支
2. 编写代码和测试
3. 运行测试确保通过
4. 提交代码并创建 PR