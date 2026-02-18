# 🍽️ 尝尝咸淡 - 智能食谱助手

基于 RAG (检索增强生成) 技术的智能食谱问答系统，支持语音交互和虚拟数字人。

## 功能特性

- **智能问答**: 基于食谱知识库的智能问答，支持菜品查询、食材询问、做法指导等
- **语音交互**: 支持语音输入（浏览器 Web Speech API）和语音播放回复（edge-tts）
- **虚拟数字人**: SVG + CSS 动画实现的可爱厨师形象，支持多种表情和状态
- **对话历史**: 自动保存对话历史，支持清除功能
- **流式输出**: 支持打字机效果的流式回复

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3)                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Chat 模块   │  │  虚拟数字人   │  │  语音输入/播放     │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      后端 (FastAPI)                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Chat API   │  │   TTS API    │  │   RAG Service     │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     RAG 系统核心                             │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ 数据准备模块 │  │  索引构建模块  │  │    检索优化模块    │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    生成集成模块 (Qwen3-4B)               ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 安装依赖

```bash
# 安装后端依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
```

### 2. 启动服务

**方式一：使用启动脚本（推荐）**

Windows:
```bash
start.bat
```

Linux/Mac:
```bash
chmod +x start.sh
./start.sh
```

**方式二：手动启动**

```bash
# 终端 1: 启动后端
python run_server.py

# 终端 2: 启动前端
cd frontend
npm run dev
```

### 3. 访问应用

- 前端界面: http://localhost:3000
- 后端 API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 项目结构

```
code_C8/
├── main.py                    # 原 RAG 交互式问答
├── config.py                  # 系统配置
├── requirements.txt           # Python 依赖
├── run_server.py              # 后端启动脚本
├── start.bat                  # Windows 启动脚本
├── start.sh                   # Linux/Mac 启动脚本
│
├── rag_modules/               # RAG 核心模块
│   ├── data_preparation.py    # 数据准备
│   ├── index_construction.py  # 索引构建
│   ├── retrieval_optimization.py # 检索优化
│   └── generation_integration.py # 生成集成
│
├── api/                       # FastAPI 后端
│   ├── app.py                 # 应用入口
│   ├── routes/
│   │   ├── chat.py            # 聊天路由
│   │   └── tts.py             # 语音合成路由
│   └── services/
│       ├── rag_service.py     # RAG 服务封装
│       └── tts_service.py     # TTS 服务
│
├── frontend/                  # Vue 3 前端
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── components/
│       │   ├── ChatPanel.vue      # 聊天面板
│       │   ├── MessageList.vue    # 消息列表
│       │   ├── MessageInput.vue   # 输入框
│       │   ├── Avatar.vue         # 虚拟数字人
│       │   └── VoiceRecorder.vue  # 语音录制
│       ├── stores/
│       │   └── chat.js            # Pinia 状态管理
│       └── services/
│           ├── api.js             # API 调用
│           └── speech.js          # 语音识别/播放
│
├── audio/                     # 生成的语音文件
└── dishes/                    # 食谱数据
```

## API 接口

### 聊天接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chat/status` | GET | 获取系统状态 |
| `/api/chat/init` | POST | 初始化 RAG 系统 |
| `/api/chat/send` | POST | 发送消息 |
| `/api/chat/stream` | POST | 流式发送消息 |
| `/api/chat/voices` | GET | 获取可用语音 |

### TTS 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/tts/synthesize` | POST | 文本转语音 |
| `/api/tts/audio/{filename}` | GET | 获取音频文件 |
| `/api/tts/voices` | GET | 获取可用语音列表 |

## 技术栈

### 后端
- **FastAPI**: Web 框架
- **LangChain**: RAG 流程编排
- **FAISS**: 向量索引
- **Qwen3-4B**: 本地大语言模型
- **edge-tts**: 语音合成

### 前端
- **Vue 3**: 前端框架
- **Pinia**: 状态管理
- **Vite**: 构建工具
- **Web Speech API**: 语音识别

## 注意事项

1. **首次启动**: 首次启动需要加载模型和构建索引，可能需要几分钟时间
2. **语音识别**: 需要使用 Chrome 浏览器并在 HTTPS 或 localhost 环境下
3. **语音合成**: 需要网络连接（edge-tts 调用微软服务，但免费无需 API Key）
4. **GPU 加速**: 建议使用 CUDA GPU 以获得更好的推理速度

## 成本说明

本项目完全免费，不产生任何费用：

- ✅ 本地大语言模型 (Qwen3-4B)
- ✅ 本地向量索引 (FAISS)
- ✅ 免费语音合成 (edge-tts)
- ✅ 浏览器语音识别 (Web Speech API)
- ✅ 开源前端框架 (Vue 3)

## 许可证

MIT License
