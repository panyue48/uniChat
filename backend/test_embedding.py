"""
测试阿里云 DashScope Embedding API 是否正常工作
使用自定义 DashScopeEmbeddings 类
"""
import os
from dotenv import load_dotenv
from dashscope_embeddings import DashScopeEmbeddings

load_dotenv()

api_base = os.getenv("OPENAI_API_BASE", "")
api_key = os.getenv("OPENAI_API_KEY", "")

if "dashscope" not in api_base.lower():
    print("当前配置不是阿里云 DashScope，跳过测试")
    exit(0)

print("=" * 50)
print("测试阿里云 DashScope Embedding API (自定义实现)")
print("=" * 50)
print(f"API Base: {api_base}")
print(f"API Key: {api_key[:10]}..." if api_key else "未配置")

# 测试不同的 embedding 模型名称
test_models = ["text-embedding-v2", "text-embedding-v1"]

for model_name in test_models:
    print(f"\n尝试模型: {model_name}")
    try:
        embeddings = DashScopeEmbeddings(
            api_key=api_key,
            base_url=api_base,
            model=model_name
        )
        
        # 测试单个查询
        test_text = "这是一个测试文本"
        result = embeddings.embed_query(test_text)
        
        print(f"✓ 成功！模型 {model_name} 可以正常工作")
        print(f"  向量维度: {len(result)}")
        
        # 测试批量文档
        test_docs = ["文档1", "文档2", "文档3"]
        batch_result = embeddings.embed_documents(test_docs)
        print(f"  批量测试: {len(batch_result)} 个文档，每个维度 {len(batch_result[0])}")
        
        print(f"  建议在 main.py 中使用: {model_name}")
        break
    except Exception as e:
        print(f"✗ 失败: {str(e)[:200]}")
        continue
else:
    print("\n所有模型都测试失败，请检查：")
    print("1. API Key 是否正确")
    print("2. API Key 是否有 embedding 权限")
    print("3. 网络连接是否正常")
    print("4. 账户余额是否充足")
    print("5. 是否已安装 openai 包: pip install openai")

