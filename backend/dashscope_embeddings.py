"""
阿里云 DashScope Embeddings 兼容类
使用原生 OpenAI SDK 实现，兼容 LangChain
"""
from typing import List, Optional
from langchain_core.embeddings import Embeddings
from openai import OpenAI
import os


class DashScopeEmbeddings(Embeddings):
    """阿里云 DashScope Embeddings 实现"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: str = "text-embedding-v2"
    ):
        """
        初始化 DashScope Embeddings
        
        Args:
            api_key: API Key，如果不提供则从环境变量读取
            base_url: API Base URL
            model: 模型名称，支持 text-embedding-v2, text-embedding-v1 等
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = base_url
        self.model = model
        
        if not self.api_key:
            raise ValueError("请提供 API Key 或设置 OPENAI_API_KEY 环境变量")
        
        # 初始化 OpenAI 客户端（兼容 DashScope）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        对文档列表进行 embedding
        
        Args:
            texts: 文本列表
            
        Returns:
            embedding 向量列表
        """
        # 阿里云 DashScope 支持批量处理
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts  # 直接传入列表
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            # 如果批量失败，尝试单个处理
            print(f"[警告] 批量 embedding 失败，改用单个处理: {e}")
            embeddings = []
            for text in texts:
                try:
                    response = self.client.embeddings.create(
                        model=self.model,
                        input=[text]  # 单个文本也要放在列表中
                    )
                    embeddings.append(response.data[0].embedding)
                except Exception as err:
                    print(f"[错误] 处理文本失败: {err}")
                    # 返回零向量作为占位符
                    embeddings.append([0.0] * 1536)  # 默认维度
            return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """
        对单个查询文本进行 embedding
        
        Args:
            text: 查询文本
            
        Returns:
            embedding 向量
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=[text]  # 单个文本也要放在列表中
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[错误] Embedding 查询失败: {e}")
            raise

