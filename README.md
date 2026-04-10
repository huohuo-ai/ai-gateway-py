# AI Gateway - Python 版本

企业级AI网关管理系统，提供MaaS（Model as a Service）能力，支持多模型管理、用户配额控制、审计日志和风险行为检测。

## 技术栈

### 后端
- **Python 3.11+**
- **FastAPI**: 高性能Web框架
- **SQLAlchemy 2.0**: ORM框架
- **Pydantic V2**: 数据验证
- **MySQL**: 主数据存储
- **Redis**: 缓存和限流
- **ClickHouse**: 审计日志存储

### 前端
- **Vue 3**: 渐进式JavaScript框架
- **Element Plus**: UI组件库
- **Vite**: 构建工具
- **ECharts**: 数据可视化图表
- **Pinia**: 状态管理

## 快速开始

### 1. 环境准备

确保已安装 Docker 和 Docker Compose。

### 2. 启动服务

```bash
# 复制环境变量文件
cp .env.example .env

# 启动所有服务
docker compose up -d

# 查看日志
docker compose logs -f backend
```

### 3. 访问服务

- **管理界面**: http://localhost:3000
- **API文档**: http://localhost:8080/docs
- **健康检查**: http://localhost:8080/health

### 4. 默认账号

- **用户名**: admin
- **密码**: admin123

## API 使用

### 登录获取 JWT Token

```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 使用 API Key 调用 LLM

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 项目结构

```
ai-gateway-python/
├── app/               # 后端应用
│   ├── api/           # API路由
│   ├── audit/         # 审计和风险检测
│   ├── core/          # 核心工具（安全、常量）
│   ├── db/            # 数据库连接
│   ├── llm/           # LLM客户端
│   ├── middleware/    # 中间件
│   ├── models/        # SQLAlchemy模型
│   ├── schemas/       # Pydantic模型
│   ├── services/      # 业务逻辑
│   ├── config.py      # 配置管理
│   └── main.py        # 应用入口
├── web/               # 前端应用 (Vue 3 + Element Plus)
│   ├── src/
│   │   ├── api/       # API接口封装
│   │   ├── components/# 公共组件
│   │   ├── router/    # 路由配置
│   │   ├── store/     # 状态管理
│   │   ├── views/     # 页面组件
│   │   └── assets/    # 静态资源
│   ├── package.json
│   └── Dockerfile
├── init/mysql/        # 数据库初始化脚本
├── docker-compose.yml # Docker编排
├── Dockerfile         # 后端镜像
└── requirements.txt   # Python依赖
```

## 功能特性

### 管理界面功能
- 📊 **仪表盘**: Token使用量统计、请求趋势图表、最近请求列表
- 🔑 **API密钥管理**: 创建/停用/删除API密钥，设置使用限制和过期时间
- 🤖 **模型管理**: 添加/编辑/删除AI模型，配置模型参数和定价
- 👥 **用户管理**: 创建/编辑用户，设置配额限制（日/周/月）
- 📝 **审计日志**: 全链路请求追踪，支持筛选和导出
- ⚠️ **风险告警**: 实时风险检测告警，支持告警规则配置
- 💬 **LLM对话**: 内置对话测试界面，支持流式响应

### 1. MaaS AI网关
- 支持 OpenAI、Azure、Anthropic 等提供商
- 兼容 OpenAI API 格式
- 流式响应支持 (SSE)
- 系统提示词自动注入

### 2. Token配额管理
- 日/周/月三级配额
- 实时配额检查
- 超额自动拦截

### 3. 审计日志
- 全链路请求追踪
- ClickHouse 存储（支持TB级）
- MySQL 实时统计

### 4. 风险检测
- Token滥用检测
- 非工作时间访问
- 敏感信息获取
- 异常请求频率
- IP异常检测
- 提示词注入攻击检测

## 前端开发

### 本地开发

```bash
# 进入前端目录
cd web

# 安装依赖（使用国内镜像）
npm install --registry=https://registry.npmmirror.com

# 启动开发服务器
npm run dev
```

开发服务器将在 http://localhost:3000 启动，并自动代理API请求到后端。

### 前端技术栈

- **Vue 3 Composition API**: 组件逻辑复用
- **Element Plus**: 企业级UI组件
- **Vue Router 4**: 路由管理
- **Pinia**: 状态管理
- **ECharts**: 数据可视化
- **Axios**: HTTP客户端

### 前端构建

```bash
# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

## 配置说明

编辑 `config.yaml` 文件：

```yaml
server:
  port: 8080
  debug: false

database:
  host: localhost
  port: 3306
  username: root
  password: password

redis:
  host: localhost
  port: 6379

clickhouse:
  host: localhost
  port: 8123

jwt:
  secret: "your-secret-key"
  expires_in: 86400

audit:
  off_hours_start: 22
  off_hours_end: 6
  token_threshold_hourly: 100000
```

## 许可证

MIT License
