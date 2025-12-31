# 项目名称：微信小程序 RAG-AI 问答助手 (WeChat RAG Bot)

## 1. 项目目标

构建一个基于微信小程序的 AI 问答助手，用户上传 PDF 文档，系统基于文档内容进行 RAG（检索增强生成）问答。

## 2. 技术栈

- **前端**: Uni-app (Vue3 + Vite), 目标平台: 微信小程序
- **后端**: Python 3.10+, FastAPI
- **AI/RAG**: LangChain, ChromaDB (向量库), OpenAI/DeepSeek API (LLM)
- **协议**: HTTP REST API (支持流式 Streaming)

## 3. 系统架构

### 3.1 目录结构

/root

/backend (Python API 服务)

\- main.py (入口)

\- /uploads (临时文件存储)

\- /db (ChromaDB 持久化存储)

/frontend (Uni-app 项目)

\- /pages/index/index.vue (聊天主页)

## 4. 后端 API 规范 (Base URL: http://localhost:8000)

### 接口 1: 上传 PDF

- **Endpoint**: `POST /upload`

- **功能**: 接收 PDF，解析文本，切割(Chunking)，向量化存入 ChromaDB。

- **Params**: `file` (Multipart), `session_id` (String)

- **Response**:

  ```
  { "status": "success", "message": "Ready to chat", "chunks": 120 }
  ```

### 接口 2: 问答 (流式)

- **Endpoint**: `POST /chat`
- **功能**: 接收问题，检索相关片段，生成回答。
- **Params**: `query` (String), `session_id` (String)
- **Response**: `StreamingResponse` (text/event-stream)。
- **逻辑**:
  1. 根据 session_id 加载对应的 ChromaDB。
  2. Perform Similarity Search (k=4)。
  3. Construct Prompt: "Use the following context to answer the question: {context}".
  4. Stream output from LLM.

## 5. 核心业务逻辑 (RAG Pipeline)

1. **Loader**: 使用 `PyPDFLoader` 加载文件。
2. **Splitter**: `RecursiveCharacterTextSplitter`, chunk_size=500, overlap=50。
3. **Embeddings**: 使用 `OpenAIEmbeddings` (兼容模式，指向 DeepSeek 或 Moonshot)。
4. **LLM**: 使用 `ChatOpenAI`，temperature=0.3。
5. **Session**: 基于文件系统的简单 Session 管理，每个 `session_id` 对应一个独立的 Chroma 文件夹。

## 6. 前端 UI/UX 规范

- **风格**: 极简聊天界面，模仿微信。
- **功能**:
  - 左下角 "+" 号按钮 -> 触发 `wx.chooseMessageFile` (只选 PDF)。
  - 聊天气泡：绿色(用户), 白色(AI)。
  - **流式渲染**: 必须支持打字机效果，后端返回的数据块需要实时追加到当前消息。
  - **状态管理**: 上传中显示 Loading Toast，回答中禁用发送按钮。

## 7. 环境变量 (.env)

后端需包含:

- OPENAI_API_KEY
- OPENAI_BASE_URL (例如: https://www.google.com/search?q=https://api.deepseek.com)