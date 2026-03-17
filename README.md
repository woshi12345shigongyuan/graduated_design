# 尝尝咸淡 - 技术报告

---

## 一、项目概述

### 1.1 项目目标

**尝尝咸淡** 是一个基于 **RAG（检索增强生成）** 的智能食谱问答系统，面向“今天吃什么”等选择困难场景，提供食谱检索、步骤指导与多模态交互能力。项目以后端 RAG 管线为核心，通过 FastAPI 暴露 HTTP API，由 Vue 3 前端实现聊天界面、语音输入/播放与虚拟数字人展示，形成完整的“问答 + 语音 + 数字人”闭环。

### 1.2 主要功能

- **智能食谱问答**：基于本地食谱 Markdown 知识库，支持按菜品名、分类、难度等查询，返回列表推荐或分步制作说明。
- **语音交互**：浏览器端语音识别（Web Speech API）输入；回复文本经 edge-tts 合成语音，可播放。
- **虚拟数字人**：支持上传人物基础图，通过火山引擎即梦 OmniHuman 1.0 快速模式生成口播视频；无基础图时展示内置 SVG 厨师形象与状态/表情动画。
- **对话与持久化**：单会话多轮对话，前端将消息与语音设置持久化到 localStorage。

### 1.3 适用场景

- 个人或教学场景下的食谱查询与制作指导  
- 需要“语音问 + 语音答”的厨房/双手占用场景  
- 展示 RAG + 大模型 + TTS + 数字人集成的原型或毕设项目  

---

## 二、功能特性

### 2.1 核心功能列表

| 功能 | 描述 | 使用方式 |
|------|------|----------|
| **RAG 问答** | 根据用户问题检索食谱片段并生成回答 | 前端输入问题 → 调用 `/api/chat/send` → 返回文本（及可选音频/视频 URL） |
| **系统初始化** | 加载嵌入模型、构建/加载 FAISS 索引、初始化 LLM | 首次使用前调用 `POST /api/chat/init`；前端会先 `GET /api/chat/status` 判断是否已就绪 |
| **流式回复** | 打字机式逐字输出 | `POST /api/chat/stream`，SSE 流，前端可解析 `data:` 行并追加到消息 |
| **语音合成 (TTS)** | 将回复文本转为语音文件 | 聊天接口内可选 `enable_tts`；也可单独调用 `POST /api/tts/synthesize` |
| **数字人基础图** | 上传/删除/查询当前人物图 | `GET /api/digital_human/avatar/status`、`POST /api/digital_human/avatar`（上传）、`DELETE /api/digital_human/avatar` |
| **数字人视频生成** | 用基础图 + 语音生成口播视频 | 聊天回复时若已上传基础图且配置火山 AK/SK，后端自动调用即梦 API，返回 `video_url` |
| **语音输入** | 浏览器麦克风语音转文字 | 前端使用 Web Speech API（`speech.js`），识别结果填入输入框，可再点击发送 |
| **对话历史** | 消息列表与清空 | 前端 Pinia store 持久化到 localStorage；清空时弹窗确认并重新生成 sessionId |
| **示例问题** | 空状态下点击即发问 | 前端 `MessageList` 发出 `example` 事件，`ChatPanel` 调用 `handleSend` 发送该条问题 |

### 2.2 使用方式说明

- **问答**：在输入框输入或点击示例问题 → 发送 → 等待回复（含可选打字机占位）；回复可带 `audio_url` / `video_url`，前端自动播放。
- **语音输入**：点击语音按钮 → 授权麦克风 → 说话 → 结果填入输入框，再点发送。
- **数字人**：在左侧“上传数字人基础图”上传图片；有图且后端配置好火山引擎密钥后，回复会生成数字人视频并展示在 Avatar 区域。

---

## 三、系统架构

### 3.1 整体架构

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                    前端 (Vue 3 + Vite)                    │
                    │  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐ │
                    │  │ ChatPanel   │  │ Avatar       │  │ MessageInput      │ │
                    │  │ MessageList │  │ (SVG/图/视频) │  │ speech.js 语音输入 │ │
                    │  └─────────────┘  └──────────────┘  └───────────────────┘ │
                    │         │  Pinia(chat)  │                    │              │
                    │         └───────────────┴────────────────────┘              │
                    │                         api.js (axios)                        │
                    └─────────────────────────────────┬─────────────────────────┘
                                                         │ HTTP /api/*
                                                         ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │                    后端 (FastAPI)                         │
                    │  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐ │
                    │  │ chat.py     │  │ tts.py       │  │ digital_human.py   │ │
                    │  │ (send/stream│  │ (synthesize, │  │ (avatar CRUD,      │ │
                    │  │  init)      │  │  audio)      │  │  image)            │ │
                    │  └──────┬──────┘  └──────┬───────┘  └─────────┬─────────┘ │
                    │         │                │                     │           │
                    │         ▼                ▼                     ▼           │
                    │  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐ │
                    │  │ rag_service │  │ tts_service   │  │ omnihuman_service  │ │
                    │  └──────┬──────┘  │ (edge-tts)    │  │ (火山即梦 视频生成)  │ │
                    │         │        └───────────────┘  └───────────────────┘ │
                    └─────────┼────────────────────────────────────────────────┘
                              ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │                  RAG 管线 (rag_modules)                 │
                    │  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐ │
                    │  │ data_       │  │ index_       │  │ retrieval_        │ │
                    │  │ preparation │  │ construction │  │ optimization      │ │
                    │  │ (加载/分块)  │  │ (FAISS+嵌入)  │  │ (混合检索+RRF)    │ │
                    │  └──────┬──────┘  └──────┬───────┘  └─────────┬─────────┘ │
                    │         │                │                     │           │
                    │         └────────────────┴─────────────────────┘           │
                    │                              │                             │
                    │                              ▼                             │
                    │  ┌─────────────────────────────────────────────────────────┐│
                    │  │ generation_integration (Ollama/本地 LLM, 路由/重写/生成)   ││
                    │  └─────────────────────────────────────────────────────────┘│
                    └─────────────────────────────────────────────────────────────┘
```

### 3.2 模块划分

- **前端**：单页应用，无路由。`App.vue` 为根，包含头部、左侧 Avatar 区、右侧 ChatPanel；ChatPanel 内为 MessageList + MessageInput，以及清空确认弹窗。状态集中在 `stores/chat.js`，API 与语音在 `services/`。
- **后端**：FastAPI 应用 `api/app.py` 挂载 CORS、静态目录（audio、video）、三个路由模块；`run_server.py` 负责加载 `.env`、设置 HF 镜像并启动 uvicorn。
- **RAG**：`rag_service` 单例串联数据准备 → 索引构建/加载 → 检索优化 → 生成集成；对外提供 `initialize()` 与 `ask_question(question, stream)`。

### 3.3 数据流（单次问答）

1. 用户在前端输入或点击示例 → `ChatPanel.handleSend(text)`  
2. `chatStore.addUserMessage(text)`、`addTypingMessage()`，请求 `chatApi.sendMessage(text, { enableTts, voice, sessionId })`  
3. 后端 `chat.py` 调用 `rag_service.ask_question(message)` 得到 `answer`；若 `enable_tts` 则调用 `tts_service.synthesize` 得到 `audio_url`；若有基础图且配置即梦则调用 `omnihuman_service.create_digital_human_video(image_url, audio_url)` 得到 `video_url`  
4. 返回 `ChatResponse(answer, audio_url, video_url, session_id)`  
5. 前端 `chatStore.updateMessage(typingId, { content, audioUrl, isTyping: false })`，根据 `video_url`/`audio_url` 与 `autoPlay` 设置播放并更新 Avatar 状态（idle/thinking/speaking）

### 3.4 设计模式

- **单例**：`RAGService`、`TTSService`、`OmniHumanService`、前端 `speechRecognition` / `audioPlayer`  
- **依赖注入**：前端通过 `provide/inject` 传递 Avatar 状态与回调（如 `avatarStatus`、`onPlaybackEnded`）  
- **管道/链式**：生成模块中 LCEL（`|`）串联 prompt → LLM → StrOutputParser  

---

## 四、项目结构

```
code_C8/
├── main.py                      # RAG 交互式命令行入口（独立于 API）
├── config.py                    # RAG 配置 dataclass（路径、模型、检索/生成参数）
├── requirements.txt             # Python 依赖
├── run_server.py                # 后端启动入口（uvicorn）
├── start.ps1                    # PowerShell 启动脚本（可选后端/前端/同时启动）
├── .env                         # 可选：VOLC_ACCESS_KEY_ID, VOLC_SECRET_ACCESS_KEY, PUBLIC_BASE_URL
│
├── rag_modules/                 # RAG 核心
│   ├── __init__.py
│   ├── data_preparation.py      # 数据加载、Markdown 分块、元数据增强、父子文档映射
│   ├── index_construction.py    # 嵌入模型、FAISS 构建/加载/保存
│   ├── retrieval_optimization.py # 向量+BM25 混合检索、RRF 重排、元数据过滤
│   └── generation_integration.py# 查询路由/重写、列表/基础/分步回答（含流式）
│
├── api/                         # FastAPI 后端
│   ├── __init__.py
│   ├── app.py                   # 应用创建、CORS、生命周期、静态挂载、路由注册
│   ├── routes/
│   │   ├── __init__.py          # 导出 chat_router, tts_router, digital_human_router
│   │   ├── chat.py              # /api/chat: status, init, send, stream, voices
│   │   ├── tts.py               # /api/tts: synthesize, audio/:filename, voices, cleanup
│   │   └── digital_human.py     # /api/digital_human: avatar status/upload/delete/image
│   └── services/
│       ├── __init__.py
│       ├── rag_service.py       # RAGService 单例，封装 RAG 管线
│       ├── tts_service.py       # edge-tts 合成、文件落盘、清理
│       └── omnihuman_service.py # 火山即梦视频生成（提交任务 + 轮询 + 下载到本地）
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js           # Vue 插件、dev 端口 3000、/api -> 8000 代理
│   ├── index.html               # 入口 HTML、全局 CSS 变量（深色主题）
│   └── src/
│       ├── main.js               # createApp、Pinia、mount App
│       ├── App.vue               # 布局、初始化遮罩、Avatar 区、ChatPanel、provide
│       ├── components/
│       │   ├── ChatPanel.vue     # 聊天头部、MessageList、MessageInput、清空确认
│       │   ├── MessageList.vue   # 空状态/示例问题、消息列表、Markdown、打字/音频/时间戳
│       │   ├── MessageInput.vue  # 输入框、语音、发送
│       │   ├── Avatar.vue        # 数字人展示（视频/上传图/SVG）、状态与表情
│       │   └── VoiceRecorder.vue # 按住说话（当前未在主流程使用）
│       ├── stores/
│       │   └── chat.js           # Pinia：messages、sessionId、loading、voiceSettings、持久化
│       ├── services/
│       │   ├── api.js            # axios 封装、chatApi/ttsApi/digitalHumanApi
│       │   └── speech.js         # 语音识别 + 音频播放单例
│   └── composables/
│       ├── useLipSync.js         # 基于 Web Audio 的唇形同步（未在 Avatar 中接入）
│       └── useAvatarRenderer.js # Canvas 2D 数字人渲染（未在 Avatar 中接入）
│
├── audio/                       # TTS 生成的 mp3 文件
├── video/                       # 数字人视频 current.mp4
├── uploads/avatar/              # 上传的数字人基础图 current.jpg
├── dishes/                      # 食谱 Markdown 数据（按分类子目录）
└── vector_index/                # FAISS 索引持久化目录（由 config 指定）
```

---

## 五、核心代码分析

### 5.1 后端

#### `config.py`

- **作用**：集中管理 RAG 路径、模型、检索与生成参数。
- **RAGConfig**：dataclass，包含 `data_path`、`index_save_path`、`embedding_model`、`llm_model`、`local_model_path`、`use_local_model`、`model_device`、`top_k`、`temperature`、`max_tokens`。提供 `from_dict` / `to_dict`。
- **DEFAULT_CONFIG**：默认配置实例。

#### `run_server.py`

- **作用**：设置项目根目录为 cwd、加载 `.env`、设置 `HF_ENDPOINT`、启动 uvicorn 运行 `api.app:app`（host 0.0.0.0，port 8000，reload）。

#### `api/app.py`

- **作用**：FastAPI 应用入口、中间件、静态挂载、健康与根路径。
- **lifespan**：启动时创建 `audio` 目录；关闭时打日志。
- **CORS**：允许所有来源、凭证、方法与头。
- **中间件**：为响应添加 `ngrok-skip-browser-warning: 1`（代码中为 `@app.middleware("https")`，Starlette 通常使用 `"http"`，若需对所有 HTTP 请求生效可改为 `"http"`）。
- **路由**：注册 `chat_router`、`tts_router`、`digital_human_router`。
- **静态**：`/audio` → `audio` 目录；`/api/digital_human/video` → `video` 目录。
- **/health**：返回 `rag_ready`（来自 `rag_service.is_ready`）。

#### `api/routes/chat.py`

- **ChatRequest / ChatResponse / InitResponse**：Pydantic 模型。
- **get_status**：返回 RAG 是否就绪及统计信息。
- **initialize_system**：`run_in_threadpool(rag_service.initialize)`，返回状态信息。
- **send_message**：若未就绪返回 503；否则调用 `rag_service.ask_question`；若 `enable_tts` 且存在答案则合成 TTS（有数字人基础图时仅合成前约 60 字以控成本）；若有基础图且即梦可用则调用 `omnihuman_service.create_digital_human_video`；返回 answer、audio_url、video_url、session_id。
- **stream_message**：SSE 流式；在后台线程中消费 RAG 流式生成器，通过 asyncio.Queue 将 chunk 转到 async 生成器，避免阻塞事件循环。
- **get_available_voices**：返回 TTS 可用语音列表。

#### `api/routes/tts.py`

- **synthesize_text**：调用 `tts_service.synthesize`，返回音频 URL。
- **get_audio**：按文件名从 `AUDIO_DIR` 返回 FileResponse。
- **stream_synthesize**：流式 TTS 生成并返回音频流。
- **get_voices**：返回带描述的语音列表。
- **cleanup_audio**：清理过期音频文件。

#### `api/routes/digital_human.py`

- **作用**：数字人基础图的上传、删除、状态与图片获取。
- **存储**：`uploads/avatar/current.jpg`；进程内缓存 base64 便于聊天时使用。
- **get_avatar_status**：返回是否已有图及图片 URL。
- **upload_avatar**：校验类型与大小（≤10MB），写入 `CURRENT_AVATAR_FILE` 并更新缓存。
- **delete_avatar**：删除文件并清缓存。
- **get_avatar_image**：返回当前图片的 FileResponse。
- **get_current_avatar_base64**：供 chat 等模块判断是否启用数字人视频。

#### `api/services/rag_service.py`

- **RAGService**：单例，封装 RAG 四模块。
- **initialize()**：检查数据路径；依次初始化数据准备、索引构建、生成集成；`_build_knowledge_base()` 中尝试加载已有索引，否则构建并保存；最后初始化检索优化模块并设置 `_ready`。
- **ask_question(question, stream)**：查询路由 → 查询重写（非 list）→ 检索（含元数据过滤）→ 取父文档 → 按路由类型调用列表/分步/基础生成（支持 stream）。
- **_extract_filters_from_query**：从问题中提取分类、难度等过滤条件。
- **get_statistics**：返回数据模块统计信息。

#### `api/services/tts_service.py`

- **TTSService**：使用 edge-tts，语音列表为中文 Neural 音色。
- **synthesize**：异步，生成唯一文件名，`Communicate.save` 到 `AUDIO_DIR`，返回路径。
- **synthesize_stream**：异步生成器，按 chunk 产出音频数据。
- **clean_old_audio**：按文件修改时间删除超过指定小时的 mp3。

#### `api/services/omnihuman_service.py`

- **OmniHumanService**：读取环境变量 `VOLC_ACCESS_KEY_ID` / `VOLC_SECRET_ACCESS_KEY`、`PUBLIC_BASE_URL`；使用火山引擎 VisualService 的 `cv_submit_task` 与 `cv_get_result`（req_key 为即梦快速模式视频生成）。
- **create_digital_human_video(image_url, audio_url)**：将 image/audio URL 转为公网 URL（依赖 PUBLIC_BASE_URL）；提交任务后轮询直到 success/done 或失败/超时；将返回的 video_url 下载到本地 `video/current.mp4`，返回本地可访问的 URL 路径。

#### `rag_modules/data_preparation.py`

- **DataPreparationModule**：从 `data_path` 递归加载 `.md`，构建父文档、增强元数据（分类、难度、dish_name）；`chunk_documents` 使用 MarkdownHeaderTextSplitter 按标题分块，维护父子映射；`get_parent_documents` 按检索到的子块去重并排序父文档；提供分类/难度过滤与统计。

#### `rag_modules/index_construction.py`

- **IndexConstructionModule**：HuggingFaceEmbeddings（含 normalize）、FAISS 构建/加载/保存、`similarity_search`；支持向已有索引 `add_documents`。

#### `rag_modules/retrieval_optimization.py`

- **RetrievalOptimizationModule**：向量检索器 + BM25Retriever；`hybrid_search` 用 RRF 融合两路结果；`metadata_filtered_search` 在混合检索结果上按元数据过滤。

#### `rag_modules/generation_integration.py`

- **GenerationIntegrationModule**：支持 Ollama 与本地 HuggingFace 模型；`query_router` 将问题分为 list/detail/general；`query_rewrite` 对非 list 查询做重写；`generate_list_answer` 仅输出菜品名列表；`generate_basic_answer` / `generate_step_by_step_answer` 及对应 stream 版本；`_build_context` 拼接文档并限制长度。

#### `main.py`

- **RecipeRAGSystem**：独立于 API 的 RAG 封装，与 `rag_service` 逻辑类似；提供 `initialize_system`、`build_knowledge_base`、`ask_question`、`run_interactive` 等，用于命令行交互式问答。

---

### 5.2 前端

#### `frontend/src/main.js`

- 创建 Vue 应用，挂载 Pinia，挂载 `App.vue` 到 `#app`。

#### `frontend/src/App.vue`

- **布局**：头部标题与副标题；主区左侧 Avatar 区（上传/删除按钮 + Avatar 组件），右侧 ChatPanel；未就绪时全屏初始化遮罩（含初始化按钮）。
- **逻辑**：`checkStatus` 与 `fetchAvatarStatus` 在 onMounted 执行；用户点击初始化后调用 `chatApi.init()`，成功后 `isReady = true`；通过 `provide` 向子组件提供 `avatarStatus`、`isSpeaking`、`currentEmotion`、`videoUrlToPlay`、`onPlaybackEnded`。

#### `frontend/src/components/ChatPanel.vue`

- **头部**：标题、消息数、清空按钮。
- **MessageList**：监听 `@example`，直接调用 `handleSend`，实现示例问题点击即发送。
- **handleSend(message)**：统一将 message 转为字符串；若为空或正在加载则返回；添加用户消息与 typing 占位；调用 `chatApi.sendMessage`；成功后更新占位消息内容、audioUrl、isTyping，并根据回复设置情绪、播放视频/音频；失败时更新为错误消息并设置情绪；最后滚动到底部。
- **setEmotionFromAnswer**：根据回复关键词设置 neutral/happy/confused/sorry。

#### `frontend/src/components/MessageList.vue`

- **空状态**：标题“有什么可以帮您？”、示例问题按钮，点击 emit `example`。
- **消息列表**：每条消息包含头像（您/厨）、内容（Markdown 渲染、打字指示器）、音频按钮与时间戳；`defineExpose({ scrollToBottom })` 供父组件滚动。
- **renderMarkdown**：使用 `marked`（breaks、gfm）；`formatTime` 今日 HH:mm，否则 MM/DD HH:mm；`playAudio` 使用 `audioPlayer` 并维护 `playingAudioUrl`。

#### `frontend/src/components/MessageInput.vue`

- **语音中**：显示波形动画与“停止”按钮，调用 `speechRecognition`。
- **普通**：textarea（Enter 发送、Shift+Enter 换行）、语音按钮（若支持）、发送按钮；发送时 emit `send` 并清空输入框。

#### `frontend/src/components/Avatar.vue`

- **展示**：有 `videoUrl` 播视频；否则有 `avatarImageUrl` 显示图片；否则显示内置 SVG 厨师（含眨眼、眉毛/嘴型随 emotion 与 isSpeaking 变化）。
- **状态**：idle/thinking/speaking 对应不同文案与动画；emotion 显示在角标。
- **事件**：视频结束或错误时 `emit('playback-ended')`。

#### `frontend/src/stores/chat.js`

- **状态**：messages、sessionId、isLoading、currentInput、voiceSettings。
- **方法**：addUserMessage、addAssistantMessage、addTypingMessage、updateMessage、appendMessageContent、finishTyping、deleteMessage、clearMessages、setLoading、updateVoiceSettings；持久化到 localStorage（key：`changchangxiandan_chat_history`），loadFromStorage 在 store 创建时执行。

#### `frontend/src/services/api.js`

- **axios 实例**：baseURL `/api`，长超时；响应拦截器返回 `response.data`。
- **chatApi**：getStatus、init、sendMessage（支持超时与 options）、sendMessageStream（fetch SSE 解析）、getVoices。
- **ttsApi**：synthesize、getAudioUrl、getVoices。
- **digitalHumanApi**：getAvatarStatus、uploadAvatar、deleteAvatar、getAvatarImageUrl。

#### `frontend/src/services/speech.js`

- **SpeechRecognitionService**：封装 Web Speech API，lang 为 zh-CN，interimResults 为 true；暴露 start/stop/abort、checkPermission 及 onResult/onError/onStart/onEnd 回调。
- **AudioPlayerService**：封装 Audio 播放、暂停、停止、音量与 onEnded 等回调。

#### `frontend/src/composables/useLipSync.js`

- 基于 Web Audio API 分析当前播放音频的振幅，驱动 `mouthOpenness` ref；当前未在 Avatar 中接入。

#### `frontend/src/composables/useAvatarRenderer.js`

- Canvas 2D 绘制人脸/五官，支持嘴部开合、表情等；当前未在 Avatar 中接入。

---

## 六、注释文档汇总

### 6.1 后端

- **run_server.py**：`"""启动后端服务器"""`；说明设置工作目录、加载 .env、HF 镜像。
- **config.py**：`"""RAG系统配置文件"""`；RAGConfig 各字段含义；`from_dict`/`to_dict` 用途。
- **api/app.py**：`"""尝尝咸淡 API - FastAPI 应用入口"""`；尽早加载 .env；lifespan 管理；CORS、静态挂载说明。
- **api/routes/chat.py**：`"""聊天路由 - 处理聊天相关的 API 请求"""`；MAX_TTS_CHARS_FOR_VIDEO 约 15 秒语音；send_message 中数字人未调用时的日志说明；stream 中“RAG 的 stream 生成器是同步阻塞的”需放后台线程。
- **api/routes/tts.py**：各路由的 Args/Returns 说明。
- **api/routes/digital_human.py**：`"""数字人基础图上传/删除与状态接口"""`；单例存储、进程内缓存、多进程时以磁盘为准。
- **api/services/rag_service.py**：单例、初始化步骤、ask_question 流程、_extract_filters_from_query 用途。
- **api/services/tts_service.py**：类与方法级注释，说明 edge-tts、语音列表、clean_old_audio 参数。
- **api/services/omnihuman_service.py**：文件头说明即梦快速模式、仅视频生成、image_url/audio_url 须公网；_build_public_url 说明 PUBLIC_BASE_URL；create_digital_human_video 的 Args/Returns。
- **rag_modules/data_preparation.py**：数据准备、Markdown 分块、父子映射、分类/难度常量。
- **rag_modules/index_construction.py**：嵌入、FAISS、load_index 的 allow_dangerous_deserialization。
- **rag_modules/retrieval_optimization.py**：混合检索、RRF、metadata_filtered_search。
- **rag_modules/generation_integration.py**：路由类型、重写规则、各生成方法的 prompt 与 LCEL 链。

### 6.2 前端

- **stores/chat.js**：`/** 聊天状态管理 - Pinia Store */`；各方法注释（添加/更新/清空/持久化）；generateSessionId/generateMessageId。
- **services/api.js**：`/** API 服务 - 与后端通信 */`；axios 超时说明；chatApi/ttsApi/digitalHumanApi 各方法注释。
- **services/speech.js**：`/** 语音识别服务 - 使用 Web Speech API */`；配置与事件；AudioPlayerService 的 play/stop 等。
- **composables/useLipSync.js**：`/** 唇形同步 - 基于 Web Audio API 的振幅驱动口型开合 */`；参数与返回值说明。
- **composables/useAvatarRenderer.js**：`/** 虚拟数字人实时渲染 - Canvas 2D 每帧绘制 */`。

### 6.3 特殊实现细节

- **数字人视频**：TTS 仅合成前约 60 字以控制成本；image_url/audio_url 必须为公网 URL，本地开发需 ngrok 等并设置 PUBLIC_BASE_URL。
- **流式回复**：RAG 流式生成器在同步线程中迭代，通过 asyncio.Queue 将 chunk 转到 async 生成器，避免阻塞。
- **对话持久化**：仅前端 localStorage，不含服务端会话；sessionId 当前主要用于后端兼容，清空对话会重新生成。

---

## 七、依赖与环境

### 7.1 Python 依赖（requirements.txt）

| 依赖 | 用途 |
|------|------|
| langchain, langchain-huggingface, langchain-text-splitters, langchain-community | RAG 链、嵌入、文档、检索器 |
| faiss-cpu | 向量索引 |
| sentence-transformers, rank_bm25 | 嵌入与 BM25 |
| fastapi, uvicorn, python-multipart, aiofiles | 后端 API |
| edge-tts | 语音合成 |
| python-dotenv | 环境变量 |
| volcengine-python-sdk | 即梦数字人 API |

（其余如 Markdown、unstructured、openai 等为项目或传递依赖。）

### 7.2 前端依赖（package.json）

- **vue** ^3.4.0  
- **pinia** ^2.1.7  
- **axios** ^1.6.0  
- **marked** ^11.0.0  
- **vite** ^5.0.0、**@vitejs/plugin-vue** ^5.0.0  

### 7.3 环境要求

- **Python**：建议 3.10+，满足 LangChain/transformers 等要求。  
- **Node**：建议 18+，用于前端构建与 dev。  
- **Ollama**：若使用 Ollama 作为 LLM，需本地安装并拉取对应模型（如 config 中的 `llm_model`）。  
- **CUDA**：可选，嵌入与本地模型可加速。  
- **环境变量**（可选）：  
  - `VOLC_ACCESS_KEY_ID` / `VOLC_SECRET_ACCESS_KEY`：即梦数字人；  
  - `PUBLIC_BASE_URL`：公网访问地址，供即梦拉取图片与音频；  
  - `HF_ENDPOINT`：已在 run_server.py 中设为 `https://hf-mirror.com`。

### 7.4 配置文件

- **config.py**：RAG 数据路径、索引路径、嵌入/LLM 模型名、是否本地模型、设备、top_k、temperature、max_tokens。  
- **vite.config.js**：开发端口 3000，`/api` 代理到 `http://localhost:8000`。  
- **.env**：存放密钥与 PUBLIC_BASE_URL，不提交版本库。

---

## 八、使用示例

### 8.1 快速开始

**1. 克隆与依赖**

```bash
cd code_C8
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

**2. 准备数据与模型**

- 将食谱 Markdown 放入 `dishes/`（按需分子目录）。  
- 若用 Ollama：安装并执行 `ollama pull <config.llm_model>`。  
- 若用本地模型：在 config 中设置 `use_local_model` 与 `local_model_path`。

**3. 启动后端**

```bash
python run_server.py
```

- 首次访问前可先调用 `POST /api/chat/init` 初始化 RAG（或由前端按钮触发）。  
- API 文档：http://localhost:8000/docs  
- 健康检查：http://localhost:8000/health  

**4. 启动前端**

```bash
cd frontend && npm run dev
```

- 浏览器打开 http://localhost:3000  
- 若未就绪，点击“开始初始化系统”；就绪后输入问题或点击示例问题即可。

**5. 可选：PowerShell 一键启动**

```powershell
.\start.ps1
```

- 选择 3 可同时启动前后端，并做后端健康检查后再启前端。

### 8.2 基本示例

- **仅文本问答**：前端发送“宫保鸡丁怎么做？”→ 后端 RAG 检索并生成分步回答→ 前端展示 Markdown。  
- **带语音**：同上，且 enable_tts 为 true → 返回 answer + audio_url → 前端可自动或手动播放。  
- **带数字人**：已上传基础图且配置火山 AK/SK 与 PUBLIC_BASE_URL → 返回 video_url → 左侧 Avatar 播放口播视频。

---

## 九、总结

### 9.1 优点

- **功能完整**：RAG 问答、流式输出、TTS、数字人、语音输入、对话持久化一应俱全，适合作为原型或毕设展示。  
- **架构清晰**：前后端分离、RAG 管线模块化、单例服务与路由划分明确。  
- **可本地化**：LLM 可用 Ollama/本地模型，嵌入与 FAISS 本地运行，edge-tts 免费，仅数字人依赖火山引擎。  
- **前端体验**：深色主题、示例问题即点即发、打字占位、Markdown 与代码块展示，符合现代聊天界面习惯。

### 9.2 缺点与注意点

- **数字人依赖公网 URL**：本地开发需内网穿透与 PUBLIC_BASE_URL，部署与配置成本较高。  
- **无服务端会话**：历史仅存前端，换设备或清缓存即丢失；sessionId 未用于服务端多轮上下文。  
- **流式与数字人未在前端打通**：当前默认走非流式 send，流式接口已实现但前端未在主要流程中使用。  
- **Composables 未接入**：useLipSync、useAvatarRenderer 未在 Avatar 中使用，口型与 Canvas 渲染能力未发挥。  
- **中间件类型**：`api/app.py` 中 `@app.middleware("https")` 在 Starlette 中应为 `"http"` 才能对所有 HTTP 请求生效，建议改为 `"http"`。

### 9.3 改进建议

1. **服务端会话**：为 sessionId 维护服务端对话历史或摘要，便于多轮上下文与跨设备恢复。  
2. **前端默认流式**：主流程改用 `/api/chat/stream`，配合 `appendMessageContent` 实现打字机效果并保留 TTS/数字人可选。  
3. **数字人降级**：在无 PUBLIC_BASE_URL 或即梦不可用时，仅返回 TTS 或仅展示 SVG/静态图，并给出明确提示。  
4. **接入 LipSync/AvatarRenderer**：在 Avatar 中接入 useLipSync（随音频振幅驱动口型）或 useAvatarRenderer，提升无视频时的表现。  
5. **修正中间件**：将 `@app.middleware("https")` 改为 `@app.middleware("http")`。  
6. **安全与限流**：生产环境限制 CORS 来源、对 init/send 做限流与鉴权，避免滥用。  
7. **单元测试**：为 RAG 各模块与 API 路由补充单元/集成测试，保证重构与升级时行为稳定。

---

*本技术报告基于项目代码整理，若部分注释不足处已根据实现逻辑做了合理推断并注明。*
