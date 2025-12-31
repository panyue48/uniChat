# Python 开发环境指南 (Conda)

## 1. 环境概述

本项目使用独立的 Conda 虚拟环境，严禁使用 `base` 环境。

- **环境名称**: `rag_bot`
- **Python 版本**: 3.10 (稳定支持 LangChain 与 ChromaDB)

## 2. 首次安装流程 (命令行执行)

### 2.1 创建并激活环境

```
# 1. 创建环境 (如果不加 -y 需要手动确认)
conda create -n rag_bot python=3.10 -y

# 2. 激活环境 (Windows/Mac/Linux 通用)
conda activate rag_bot
```

### 2.2 安装核心依赖

确保在 `(rag_bot)` 激活状态下执行：

```
pip install fastapi uvicorn[standard] 
pip install langchain langchain-community langchain-openai 
pip install chromadb pypdf python-multipart
pip install python-dotenv # 用于加载环境变量
```

## 3. Cursor / VS Code 配置

### 3.1 选择解释器 (Select Interpreter)

1. 打开 Cursor。
2. 按 `Cmd+Shift+P` (Mac) 或 `Ctrl+Shift+P` (Win)。
3. 输入并选择: `Python: Select Interpreter`。
4. 在列表中找到: `rag_bot` (通常路径为 `~/anaconda3/envs/rag_bot/bin/python` 或类似)。
   - *如果找不到*：输入 `conda info --envs` 查看路径，手动输入路径。

### 3.2 验证环境

在 Cursor 终端中输入：

```
python --version
# 输出应为 Python 3.10.x

pip list | grep langchain
# 应该能看到 langchain 相关包
```

## 4. 依赖管理

当安装了新包后，务必导出依赖文件，以便部署使用：

```
pip freeze > requirements.txt
```

## 5. 常见问题

- **ChromaDB 安装失败**: Windows 用户可能需要安装 "C++ Build Tools"。
- **OpenAI 报错**: 检查 `os.environ` 或 `.env` 文件中的 API KEY 是否正确。