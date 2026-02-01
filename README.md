# LifeLens (智眼生活) - 基于多模态大模型的智能饮食健康管家

> **第十九届全国大学生软件创新大赛参赛作品** | 赛题：端侧智能 · 场景感知

## 1. 项目摘要 (Abstract)

针对传统饮食管理应用普遍存在的“手动记录繁琐”、“营养反馈滞后”等痛点，**LifeLens** 提出了一种基于 **"Camera-First" (相机优先)** 交互范式的解决方案。项目深度融合了 **多模态大语言模型 (Qwen-VL)** 与 **端侧智能技术**，实现了“拍照即识别、识别即分析”的极简体验。通过 Uni-app 跨端架构与 Python FastAPI 云端网关的协同，结合 **OPPO Health Service** 生态能力，为用户提供实时的营养摄入监控与动态健康建议，致力于成为用户的贴身数字营养师。

---

## 2. 创新亮点 (Innovation Highlights)

本项目在交互模式、技术应用及架构设计三个维度进行了深入创新：

### 2.1 交互模式创新：Camera-First 极简范式
- **零阻力启动**：摒弃传统 App 复杂的菜单层级，启动即进入全屏取景框，将操作步骤缩减至极致（1步：点击快门）。
- **AR 沉浸式反馈**：采用 **Glassmorphism (毛玻璃)** 风格的悬浮卡片，将 AI 分析出的热量、营养素数据直接叠加在实物画面上，实现“所见即所得”的增强现实体验。

### 2.2 技术应用创新：RAG-lite 多模态架构
- **非结构化到结构化**：利用精心设计的 Prompt Engineering，迫使视觉大模型 (VLM) 将复杂的菜品图像直接转化为标准的 JSON 营养档案（包含卡路里、碳水、蛋白质、脂肪及健康评级）。
- **端云协同推理**：前端负责图像的智能压缩（保留纹理特征同时压缩至 <100KB），后端负责高并发推理，有效平衡了识别精度与响应延迟。

### 2.3 工程架构创新：高可用演示保障
- **Mock Mode (演示保障模式)**：针对竞赛答辩场景网络不稳定的风险，内置了基于**隐形手势触发**的本地 Mock 引擎。该模式下，系统将调用本地预置的高保真数据集进行响应，确保演示环节的绝对稳定与零延迟。

---

## 3. 技术架构 (Technical Architecture)

### 3.1 系统架构图
系统采用典型的前后端分离微服务架构，容器化部署：

```mermaid
graph LR
    User[用户/终端] -->|1. 拍摄 & 压缩| Client[Uni-app 前端]
    Client -->|2. HTTPs/5G| Gateway[FastAPI 网关]
    Gateway -->|3. API 调用| LLM[阿里云 DashScope (Qwen-VL)]
    LLM -->|4. 结构化 JSON| Gateway
    Gateway -->|5. 渲染指令| Client
    Client -->|6. AR 叠加展示| User
```

### 3.2 技术栈清单 (Tech Stack)

| 模块 | 技术选型 | 版本/说明 |
| :--- | :--- | :--- |
| **客户端** | **Uni-app** | 基于 Vue 3 + Vite + Pinia，支持编译为 Android APK 与微信小程序 |
| **服务端** | **Python FastAPI** | 高性能异步 Web 框架，Docker 容器化部署 |
| **AI 引擎** | **Qwen3-VL-Flash** | 通义千问视觉大模型，负责 OCR 与语义理解 |
| **UI 框架** | **Uni-UI / CSS3** | 深度定制的 Glassmorphism 样式库 |

### 3.3 OPPO 生态集成规划
为了充分利用赛题指定的终端能力，项目规划了以下集成方案：
1.  **OPPO Health Service**：通过 SDK 获取用户当日**实时步数**与**活动能量消耗**，实现“摄入-消耗”闭环算法。
2.  **ColorOS 端侧 AI**：利用手机 NPU 能力进行本地基础 OCR（如包装袋文字提取），降低云端依赖。

---

## 4. 商业与社会价值 (Value Proposition)

- **社会价值**：通过降低记录门槛，辅助糖尿病、高血压等慢病群体进行精准的饮食干预，缓解公共医疗负担。
- **商业模式**：采用 **Freemium (免费+增值)** 模式。基础识别功能免费以获取海量用户数据；高级营养报告、微量元素分析及长期健康趋势追踪为付费增值服务。

---

## 5. 工程与部署 (Engineering & Deployment)

### 5.1 资源链接 (Resources)
- **代码仓库**: [GitHub - LifeLens](https://github.com/NGman-s/Lifelens)

### 5.2 项目结构
```bash
.
├── frontend/               # Uni-app 前端工程 (Vue 3)
│   ├── src/pages/          # 业务页面 (相机、个人中心、历史)
│   ├── src/components/     # 通用组件 (AR卡片、图表)
│   └── src/utils/          # 工具库 (图像压缩、API请求)
├── backend/                # FastAPI 后端工程
│   ├── services/           # LLM 对接逻辑
│   ├── Dockerfile          # 容器化配置
│   └── main.py             # 网关入口
└── work/                   # 项目文档与规划
```

### 5.3 快速启动指南 (Quick Start)

#### 后端服务 (Backend)
```bash
cd backend
pip install -r requirements.txt
# 在 .env 文件中配置 DASHSCOPE_API_KEY
python main.py
# 服务将运行在 http://0.0.0.0:8000
```

#### 前端应用 (Frontend)
1.  修改 `frontend/src/utils/request.js`，将 `BASE_URL` 设置为后端服务器的局域网 IP。
2.  安装依赖并运行 H5 调试模式：
    ```bash
    cd frontend
    npm install
    npm run dev:h5 -- --host
    ```

### 5.4 演示模式说明 (对于评委)
为了确保在任何网络环境下均能体验完整流程，请按以下步骤激活 **Mock Mode**：
1.  打开 App 进入首页（相机界面）。
2.  连续点击屏幕左上角的 Logo 区域 **5次**。
3.  屏幕将提示 "Demo Mode Activated"。
4.  此时拍摄任何物体，系统均会返回预置的完美演示数据。

---
*LifeLens Team | 2026*
