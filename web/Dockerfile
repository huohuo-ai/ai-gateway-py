# 构建阶段
FROM node:20-alpine AS builder

WORKDIR /app

# 使用国内镜像加速
RUN npm config set registry https://registry.npmmirror.com

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
