# AI Gateway - Python 版本

企业级AI网关管理系统，提供MaaS（Model as a Service）能力，支持多模型管理、用户配额控制、审计日志和风险行为检测。

## 技术栈

- **Python 3.11+**
- **FastAPI**: 高性能Web框架
- **SQLAlchemy 2.0**: ORM框架
- **Pydantic V2**: 数据验证
- **MySQL**: 主数据存储
- **Redis**: 缓存和限流
- **ClickHouse**: 审计日志存储

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
├── app/
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
├── init/mysql/        # 数据库初始化脚本
├── docker-compose.yml # Docker编排
├── Dockerfile         # 后端镜像
└── requirements.txt   # Python依赖
```

## 功能特性

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
