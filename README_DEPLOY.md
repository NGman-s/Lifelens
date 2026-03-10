# LifeLens 部署指南

## 1. 准备环境

服务器需要安装 Docker 与 Docker Compose，并开放你准备暴露的 H5 端口（默认 `80`）。

## 2. 准备配置

在项目根目录复制示例环境变量：

```bash
cp .env.example .env
```

至少需要确认这些值：

- `DASHSCOPE_API_KEY`: 必填
- `CORS_ALLOW_ORIGINS`: 生产环境请改成你的实际域名，不要继续使用 `*`
- `MAX_UPLOAD_SIZE_MB`: 默认 `10`
- `THUMBNAIL_RETENTION_DAYS`: 默认 `30`
- `THUMBNAIL_MAX_EDGE`: 默认 `512`
- `THUMBNAIL_QUALITY`: 默认 `70`
- `UPLOAD_STORAGE_LIMIT_MB`: 默认 `3072`
- `FRONTEND_PORT`: 默认 `80`

## 3. 启动服务

```bash
docker compose up -d --build
```

容器说明：

- `lifelens-backend`: FastAPI 后端，监听容器内 `8080`
- `lifelens-frontend`: Nginx + H5 静态资源，默认对外暴露 `${FRONTEND_PORT}`

## 4. 验证部署

- 前端首页：`http://你的服务器IP或域名`
- 健康检查：`http://你的服务器IP或域名/api/v1/health`
- 上传图片资源：分析成功后返回的 `/uploads/...` 地址可直接在同域访问

## 5. 线上行为说明

- H5 前端默认走同源 `/api` 与 `/uploads`，不需要手改前端请求地址。
- Nginx 已对 AI 接口启用基础限流：
  - `/api/v1/vision/analyze`: `10 req/min/IP`，`burst 5`
  - `/api/v1/vision/generate-alternatives`: `30 req/min/IP`，`burst 10`
- 后端会校验上传图片真实格式，仅接受 `JPG/JPEG/PNG/WEBP/BMP/AVIF`。
- 原图仅用于当前识别请求，识别完成后立即删除；历史页依赖的 `/uploads/...` 资源是服务端缩略图，并会按保留时间和总量阈值自动清理。

## 6. 常见操作

查看日志：

```bash
docker compose logs -f
```

重建并重启：

```bash
docker compose down
docker compose up -d --build
```

仅检查后端健康：

```bash
curl http://你的服务器IP或域名/api/v1/health
```
