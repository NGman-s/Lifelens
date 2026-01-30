# LifeLens (智眼生活)

LifeLens 是一款专为“智慧餐饮”设计的 AI 原生移动应用。它利用多模态大语言模型 (Qwen3-VL-Flash)，通过“镜头即入口”的交互界面，提供实时的营养分析服务。

项目采用 **Apple 官网极简主义风格**，界面清新现代，交互自然流畅。

## 🚀 核心功能
- **镜头即入口 (Camera-First)**: 极简全屏取景框，无干扰 UI，仅保留核心快门按钮。
- **AI 视觉分析**: 由 Qwen3-VL-Flash 驱动，实现极速的菜品识别与营养价值估算。
- **极简主义 UI**:
    - **Light Mode**: 全局采用简约风格的白/浅灰配色 (`#F5F5F7`, `#FFFFFF`)。
    - **Bottom Sheet**: 结果展示采用现代化的底部抽屉式交互。
    - **Glassmorphism**: 底部导航栏采用高斯模糊毛玻璃效果。
    - **Typography**: 优化的排版层级，信息展示更清晰。
- **个性化建议**: 基于用户画像（年龄、健身目标、健康状况）提供针对性的饮食建议。
- **演示稳定性保障**: 内置“Mock 模式”（隐形触发）和“自动降级”逻辑，确保演示顺畅。
- **本地历史记录**: 卡片式流布局展示历史饮食记录。

## 🛠 技术栈
- **前端**: Uni-app (Vue3 + Vite + Pinia)
- **后端**: Python FastAPI + Uvicorn
- **AI**: Qwen3-VL-Flash (通过 DashScope API 接入)

## 📂 项目结构
```
.
├── frontend/               # Uni-app 前端项目
│   ├── src/
│   │   ├── components/
│   │   │   ├── ResultOverlay.vue # 结果浮层 (Bottom Sheet)
│   │   │   ├── BottomNav.vue     # 底部导航 (毛玻璃效果)
│   │   │   └── TrendChart.vue    # 趋势图表
│   │   ├── pages/
│   │   │   ├── index/            # 首页 (相机)
│   │   │   ├── profile/          # 个人档案 (iOS 设置风格)
│   │   │   └── history/          # 历史记录 (卡片流)
│   │   ├── store/          # Pinia 状态管理
│   │   └── utils/          # 网络请求、图片处理
├── backend/                # FastAPI 后端项目
│   ├── services/           # Qwen-VL 集成服务
│   ├── temp_images/        # 临时图像存储
│   └── main.py             # API 入口
└── PRD.md                  # 产品需求文档
```

## 🏁 快速开始

### 🔗 仓库地址
- **GitHub**: https://github.com/NGman-s/Lifelens
- **部署端口**: 8080 (默认)

### 后端配置
1. 进入 `backend` 目录。
2. 安装依赖: `pip install -r requirements.txt`
3. 配置环境变量: 在 `.env` 中填入你的 `DASHSCOPE_API_KEY`。
4. 启动服务器: `python main.py`

### 前端配置
1. 进入 `frontend` 目录。
2. 安装依赖: `npm install`
3. **关键步骤**: 修改 `src/utils/request.js` 中的 `BASE_URL` 为你电脑的 **局域网 IP** (例如 `http://192.168.1.5:8000`)，否则手机无法连接后端。
4. 运行 H5 版本:
   ```bash
   npm run dev:h5 -- --host
   ```
5. 手机连接同一 Wi-Fi，访问终端显示的 IP 地址 (如 `http://192.168.1.5:5173`)。

## 📺 演示模式说明
- **激活 Mock 模式**: 点击首页左上角（隐形区域）**5 次**。
- **功能**: 在无网环境下模拟 AI 返回结果，确保演示不翻车。
