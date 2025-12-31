import os
import shutil
import uuid
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# LangChain Imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate  # 新版 LangChain 使用 langchain_core.prompts
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

# 导入自定义 DashScope Embeddings
from dashscope_embeddings import DashScopeEmbeddings

# 加载环境变量
load_dotenv()

# --- 配置区域 (从环境变量读取) ---
# 示例使用 DeepSeek，也可以换成 Moonshot 或 OpenAI
# 如果 .env 文件中没有配置，则使用默认值
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("请配置 OPENAI_API_KEY 环境变量（在 .env 文件中）")
if not os.getenv("OPENAI_API_BASE"):
    os.environ["OPENAI_API_BASE"] = "https://api.deepseek.com"

app = FastAPI()

# 允许跨域 (方便本地开发)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 目录配置
UPLOAD_DIR = "./uploads"
DB_DIR = "./db"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# 初始化模型
# 根据 API_BASE 自动选择模型名称
api_base = os.getenv("OPENAI_API_BASE", "")
api_key = os.getenv("OPENAI_API_KEY", "")

if "dashscope" in api_base.lower():
    # 阿里云 DashScope 模型
    # 注意：使用自定义 DashScopeEmbeddings 类，兼容 LangChain
    # embedding 模型：text-embedding-v2 (推荐) 或 text-embedding-v1
    # LLM 模型：qwen-turbo, qwen-plus, qwen-max 等
    
    # 初始化 embedding（使用自定义类，直接调用 OpenAI SDK）
    try:
        embeddings = DashScopeEmbeddings(
            api_key=api_key,
            base_url=api_base,
            model="text-embedding-v2"  # 先尝试 v2
        )
        print(f"[配置] Embedding 模型: text-embedding-v2 (自定义实现)")
    except Exception as e:
        print(f"[警告] text-embedding-v2 初始化失败，尝试 v1: {e}")
        # 如果 v2 不行，尝试 v1
        embeddings = DashScopeEmbeddings(
            api_key=api_key,
            base_url=api_base,
            model="text-embedding-v1"
        )
        print(f"[配置] Embedding 模型: text-embedding-v1 (自定义实现)")
    
    # 初始化 LLM（可以使用 qwen-plus 获得更好效果，但 qwen-turbo 更便宜）
    llm = ChatOpenAI(
        model="qwen-turbo",  # 可以改为 qwen-plus 或 qwen-max 获得更好效果
        temperature=0.3,
        openai_api_base=api_base,
        openai_api_key=api_key
    )
    
    print(f"[配置] 使用阿里云 DashScope API")
    print(f"[配置] API Base: {api_base}")
    print(f"[配置] LLM 模型: qwen-turbo")
else:
    # DeepSeek 或其他兼容 OpenAI 的模型
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    llm = ChatOpenAI(model="deepseek-chat", temperature=0.3)
    print(f"[配置] 使用 DeepSeek API")

# RAG Prompt 模板
template = """
你是一个专业的文档助手。请基于下面的【上下文】回答用户的问题。
如果上下文中没有答案，请直接说"根据文档内容，我无法回答这个问题"，不要编造。

【上下文】：
{context}

【问题】：
{question}
"""
prompt = ChatPromptTemplate.from_template(template)

def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), session_id: str = Form(...)):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"开始上传文件: {file.filename} (session: {session_id})")
        
        # 1. 保存文件
        session_upload_path = os.path.join(UPLOAD_DIR, session_id)
        os.makedirs(session_upload_path, exist_ok=True)
        file_path = os.path.join(session_upload_path, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"文件保存成功: {file_path}")
    
        # 2. 解析与切分
        logger.info("开始解析PDF...")
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        logger.info(f"PDF解析完成，共 {len(docs)} 页")
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        splits = splitter.split_documents(docs)
        logger.info(f"文本切分完成，共 {len(splits)} 个片段")
    
        # 3. 存入 Chroma (持久化)
        persist_dir = os.path.join(DB_DIR, session_id)
        # 如果存在旧数据先清除，保证是针对当前文件的问答
        if os.path.exists(persist_dir):
            logger.info("清除旧向量数据...")
            shutil.rmtree(persist_dir)
        
        logger.info("开始生成向量并存入数据库...")
        try:
            vectorstore = Chroma.from_documents(
                documents=splits, 
                embedding=embeddings, 
                persist_directory=persist_dir
            )
            logger.info("向量数据库创建成功")
        except Exception as embed_error:
            logger.error(f"生成向量时出错: {embed_error}")
            raise HTTPException(
                status_code=500, 
                detail=f"生成向量失败: {str(embed_error)}。请检查 API Key 和模型配置。"
            )
        
        return {"status": "success", "count": len(splits)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文件时出错: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@app.post("/chat")
async def chat_stream(query: str = Form(...), session_id: str = Form(...)):
    import logging
    logger = logging.getLogger(__name__)
    
    persist_dir = os.path.join(DB_DIR, session_id)
    if not os.path.exists(persist_dir):
        raise HTTPException(status_code=400, detail="Session not found. Please upload PDF first.")

    logger.info(f"收到问题: {query[:50]}... (session: {session_id})")
    
    # 1. 加载向量库
    try:
        vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    except Exception as e:
        logger.error(f"加载向量库失败: {e}")
        raise HTTPException(status_code=500, detail=f"加载向量库失败: {str(e)}")
    
    # 2. 构建 Chain
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # 3. 生成流式生成器（纯文本格式，兼容微信小程序）
    async def generate():
        chunk_count = 0
        try:
            async for chunk in rag_chain.astream(query):
                if chunk:  # 确保 chunk 不为空
                    chunk_count += 1
                    yield chunk.encode('utf-8')  # 编码为 bytes
            logger.info(f"流式响应完成，共 {chunk_count} 个数据块")
        except Exception as e:
            logger.error(f"生成响应时出错: {e}")
            # 如果出错，返回错误信息
            error_msg = f"\n[错误: {str(e)}]"
            yield error_msg.encode('utf-8')
        finally:
            # 确保流正确结束
            logger.info("流式响应结束")
    
    return StreamingResponse(
        generate(), 
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 nginx 缓冲
        }
    )

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    import logging
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

