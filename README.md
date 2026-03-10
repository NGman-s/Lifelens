# LifeLens

LifeLens 是一个基于 Uni-app + FastAPI + 多模态模型的饮食识别与营养分析项目。当前仓库默认面向 Docker H5 轻量公网演示站，同时保留 Uni-app 多端构建能力。

## 项目结构

- `frontend/`: Uni-app 前端（Vue 3 + Pinia + Vite）
- `backend/`: FastAPI 后端，负责图片校验、上传、模型调用与结果清洗
- `docker-compose.yml`: 前后端一体化部署
- `nginx.conf`: H5 静态资源与 `/api`、`/uploads` 反向代理配置

## 环境变量

根目录提供示例文件 [`.env.example`](/E:/a_work/Ruanchuangsai/work/.env.example)。常用配置如下：

- `DASHSCOPE_API_KEY`: 必填，DashScope API Key
- `DASHSCOPE_BASE_URL`: 可选，默认 DashScope OpenAI 兼容地址
- `CORS_ALLOW_ORIGINS`: 逗号分隔的允许来源
- `MAX_UPLOAD_SIZE_MB`: 单张图片上传大小限制，默认 `10`
- `THUMBNAIL_RETENTION_DAYS`: 历史缩略图保留天数，默认 `30`
- `THUMBNAIL_MAX_EDGE`: 缩略图长边像素限制，默认 `512`
- `THUMBNAIL_QUALITY`: WebP 缩略图质量，默认 `70`
- `UPLOAD_STORAGE_LIMIT_MB`: 上传目录总量上限，默认 `3072`
- `FRONTEND_PORT`: Docker 暴露的 H5 端口，默认 `80`
- `VITE_API_BASE_URL`: 可选，仅在非 H5 或需要直连后端时覆盖前端请求基址

## 本地开发

### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python main.py
```

后端默认监听 `http://localhost:8080`。

### 2. 启动前端 H5

```bash
cd frontend
npm install
npm run dev:h5 -- --host
```

H5 开发环境默认使用同源相对路径，并通过 `Vite proxy` 将 `/api` 与 `/uploads` 转发到 `http://localhost:8080`，不需要再手动修改前端 IP。

### 3. 非 H5 或直连后端调试

如需让前端直接访问后端，请设置：

```bash
VITE_API_BASE_URL=http://localhost:8080
```

APK / 原生 App 打包时必须提供 `VITE_API_BASE_URL`，且必须是带协议的绝对地址；H5 的相对路径代理在原生 App 中不可用。推荐示例：

```bash
VITE_API_BASE_URL=https://example.com
VITE_API_BASE_URL=http://1.2.3.4:8080
```

如果不设置该值，H5 可能仍然正常，但 APK 中的 `uni.uploadFile` / `uni.request` 会直接失败。

## Docker 部署

```bash
cp .env.example .env
docker compose up -d --build
```

默认访问地址：

- 前端 H5: `http://localhost`
- 健康检查: `http://localhost/api/v1/health`

如需修改前端端口，设置 `FRONTEND_PORT` 后重新执行 `docker compose up -d --build`。

## 接口概览

- `GET /api/v1/health`: 健康检查
- `POST /api/v1/vision/analyze`: 上传图片并返回营养分析结果
- `POST /api/v1/vision/generate-alternatives`: 生成更健康的替代建议

后端会对上传图片执行格式白名单、实际图片验证和 10MB 默认大小限制。成功分析后，原图只用于当前分析请求并立即删除，接口返回的是历史缩略图 `image_url` 与到期时间 `image_expires_at`；缩略图可通过同域 `/uploads/...` 直接访问，并会按保留天数和总量上限自动清理。

## 测试

后端自动化测试：

```bash
cd backend
python test_app.py
```

保留了一个手动烟雾测试脚本：

```bash
cd backend
python test_api.py
```


