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
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# --- 配置区域 (建议放入 .env) ---
# 示例使用 DeepSeek，也可以换成 Moonshot 或 OpenAI
os.environ["OPENAI_API_KEY"] = "sk-你的API-KEY" 
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
embeddings = OpenAIEmbeddings(model="text-embedding-3-small") # DeepSeek 兼容此 model 参数
llm = ChatOpenAI(model="deepseek-chat", temperature=0.3)

# RAG Prompt 模板
template = """
你是一个专业的文档助手。请基于下面的【上下文】回答用户的问题。
如果上下文中没有答案，请直接说“根据文档内容，我无法回答这个问题”，不要编造。

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
    try:
        # 1. 保存文件
        session_upload_path = os.path.join(UPLOAD_DIR, session_id)
        os.makedirs(session_upload_path, exist_ok=True)
        file_path = os.path.join(session_upload_path, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
        # 2. 解析与切分
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        splits = splitter.split_documents(docs)
    
        # 3. 存入 Chroma (持久化)
        persist_dir = os.path.join(DB_DIR, session_id)
        # 如果存在旧数据先清除，保证是针对当前文件的问答
        if os.path.exists(persist_dir):
            shutil.rmtree(persist_dir)
            
        vectorstore = Chroma.from_documents(
            documents=splits, 
            embedding=embeddings, 
            persist_directory=persist_dir
        )
        
        return {"status": "success", "count": len(splits)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_stream(query: str = Form(...), session_id: str = Form(...)):
    persist_dir = os.path.join(DB_DIR, session_id)
    if not os.path.exists(persist_dir):
        raise HTTPException(status_code=400, detail="Session not found. Please upload PDF first.")

    # 1. 加载向量库
    vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    
    # 2. 构建 Chain
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # 3. 生成流式生成器
    async def generate():
        async for chunk in rag_chain.astream(query):
            yield chunk
    
    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)