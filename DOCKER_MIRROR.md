# Docker 镜像加速配置指南

本项目已配置国内软件源加速，但 Docker 基础镜像拉取仍需配置镜像加速器以获得最佳效果。

## 已配置的加速项

### Dockerfile (Python 后端)
- ✅ pip 使用阿里云镜像
- ✅ apt-get 使用阿里云 Debian 源

### web/Dockerfile (Node.js 前端)
- ✅ npm 使用 npmmirror 镜像
- ✅ apk 使用阿里云 Alpine 源

## Docker 守护进程镜像加速器配置（重要）

为了加速 Docker 基础镜像拉取，请配置 Docker 镜像加速器。

### macOS (Docker Desktop)

1. 打开 Docker Desktop
2. 点击右上角齿轮图标 → Settings
3. 选择 Docker Engine
4. 在 JSON 配置中添加 `registry-mirrors`：

```json
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me"
  ]
}
```

5. 点击 "Apply & Restart"

### Linux

1. 创建或编辑 Docker 配置文件：

```bash
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me"
  ]
}
EOF
```

2. 重启 Docker 服务：

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

3. 验证配置是否生效：

```bash
docker info | grep -A 5 "Registry Mirrors"
```

### Windows (Docker Desktop)

1. 打开 Docker Desktop
2. 点击右上角齿轮图标 → Settings
3. 选择 Docker Engine
4. 在 JSON 配置中添加 `registry-mirrors`：

```json
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me"
  ]
}
```

5. 点击 "Apply & Restart"

## 可用的国内镜像加速器

| 镜像加速器 | 地址 | 状态 |
|-----------|------|------|
| Docker 1ms | https://docker.1ms.run | 可用 |
| DaoCloud | https://docker.xuanyuan.me | 可用 |
| 阿里云 | https://\<你的ID\>.mirror.aliyuncs.com | 需登录获取 |

> 注意：阿里云镜像加速器需要登录 [阿里云容器镜像服务](https://cr.console.aliyun.com/) 获取专属加速地址。

## 构建项目

配置完成后，执行以下命令构建项目：

```bash
docker-compose build
```

或使用不缓存的方式重新构建：

```bash
docker-compose build --no-cache
```

## 验证加速效果

构建完成后，可以查看构建日志确认镜像拉取速度是否有明显提升。