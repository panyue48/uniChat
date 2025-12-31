# 微信小程序 RAG-AI 问答助手

基于 Uni-app 和 FastAPI 的智能文档问答系统，支持上传 PDF 文档并进行 RAG（检索增强生成）问答。

## 项目结构

```
uniChat/
├── backend/              # Python FastAPI 后端
│   ├── main.py          # 主应用文件
│   ├── requirements.txt # Python 依赖
│   └── .gitignore
├── frontend/            # Uni-app 前端项目
│   ├── pages/          # 页面目录
│   │   └── index/      # 聊天页面
│   ├── manifest.json   # Uni-app 配置
│   ├── pages.json      # 页面路由配置
│   ├── App.vue         # 应用入口
│   └── package.json    # 前端依赖
├── env_setup.md        # 环境配置说明
├── backend-server.md   # 后端 API 说明
└── project-content.md  # 项目需求文档
```

## 快速开始

### 1. 后端环境搭建

#### 1.1 创建 Conda 环境

```bash
# 创建 Python 3.10 环境
conda create -n rag_bot python=3.10 -y

# 激活环境
conda activate rag_bot
```

#### 1.2 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 1.3 配置环境变量

在 `backend` 目录下创建 `.env` 文件：

```env
OPENAI_API_KEY=sk-你的API-KEY
OPENAI_API_BASE=https://api.deepseek.com
```

> 注意：可以使用 DeepSeek、Moonshot 或其他兼容 OpenAI API 的服务。

#### 1.4 启动后端服务

```bash
cd backend
python main.py
```

后端服务将在 `http://localhost:8000` 启动。

### 2. 前端环境搭建

#### 2.1 安装依赖

```bash
cd frontend
npm install
```

#### 2.2 配置 API 地址

编辑 `frontend/pages/index/index.vue`，修改 `API_BASE` 变量：

```javascript
// 本地开发使用
const API_BASE = 'http://127.0.0.1:8000'

// 真机调试需要改为局域网 IP，例如：
// const API_BASE = 'http://192.168.1.5:8000'
```

#### 2.3 运行项目

**使用 HBuilderX：**
1. 打开 HBuilderX
2. 文件 -> 导入 -> 从本地目录导入 -> 选择 `frontend` 目录
3. 运行 -> 运行到小程序模拟器 -> 微信开发者工具

**使用命令行：**
```bash
cd frontend
npm run dev:mp-weixin
```

然后在微信开发者工具中打开 `frontend/dist/dev/mp-weixin` 目录。

## 功能说明

### 后端 API

1. **POST /upload** - 上传 PDF 文档
   - 参数：`file` (文件), `session_id` (会话ID)
   - 功能：解析 PDF，切分文本，向量化存储

2. **POST /chat** - 流式问答
   - 参数：`query` (问题), `session_id` (会话ID)
   - 功能：基于文档内容进行 RAG 问答，支持流式返回

3. **GET /health** - 健康检查

### 前端功能

- 📄 PDF 文档上传（点击左下角 "+" 按钮）
- 💬 聊天界面（类似微信风格）
- ⚡ 流式响应（打字机效果）
- 📱 微信小程序适配

## 开发注意事项

### 微信小程序配置

1. **网络请求域名**：需要在微信公众平台配置服务器域名
   - 开发阶段：在微信开发者工具中勾选"不校验合法域名"

2. **文件上传**：
   - 微信小程序使用 `wx.chooseMessageFile` 选择文件
   - 仅支持 PDF 格式

3. **流式响应**：
   - 使用 `wx.request` 的 `enableChunked: true` 参数
   - 通过 `onChunkReceived` 监听数据块

### 后端注意事项

1. **Session 管理**：每个 `session_id` 对应独立的向量数据库
2. **文件存储**：上传的文件保存在 `backend/uploads/` 目录
3. **向量数据库**：ChromaDB 数据保存在 `backend/db/` 目录

## 常见问题

1. **ChromaDB 安装失败**：
   - Windows 用户可能需要安装 "C++ Build Tools"
   - 或使用预编译版本

2. **API 调用失败**：
   - 检查 `.env` 文件中的 API KEY 是否正确
   - 确认网络连接正常

3. **小程序无法连接后端**：
   - 确认后端服务已启动
   - 真机调试时使用局域网 IP 而非 localhost
   - 检查微信开发者工具的网络设置

## 技术栈

- **前端**：Uni-app (Vue3 + Vite)
- **后端**：Python 3.10+, FastAPI
- **AI/RAG**：LangChain, ChromaDB, OpenAI/DeepSeek API
- **协议**：HTTP REST API (支持流式 Streaming)

## 下一步开发

- [ ] 添加错误处理和重试机制
- [ ] 优化流式响应处理
- [ ] 添加多文档支持
- [ ] 实现会话历史记录
- [ ] 添加用户认证
- [ ] 优化 UI/UX

## 许可证

MIT License

