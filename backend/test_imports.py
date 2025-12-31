"""
测试脚本：验证所有导入是否正确
"""
print("正在测试导入...")

try:
    print("1. 测试 langchain_community...")
    from langchain_community.document_loaders import PyPDFLoader
    print("   ✓ PyPDFLoader 导入成功")
    
    print("2. 测试 langchain_text_splitters...")
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    print("   ✓ RecursiveCharacterTextSplitter 导入成功")
    
    print("3. 测试 langchain_community.vectorstores...")
    from langchain_community.vectorstores import Chroma
    print("   ✓ Chroma 导入成功")
    
    print("4. 测试 langchain_openai...")
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    print("   ✓ OpenAIEmbeddings, ChatOpenAI 导入成功")
    
    print("5. 测试 langchain_core.prompts...")
    from langchain_core.prompts import ChatPromptTemplate
    print("   ✓ ChatPromptTemplate 导入成功")
    
    print("6. 测试 langchain_core.output_parsers...")
    from langchain_core.output_parsers import StrOutputParser
    print("   ✓ StrOutputParser 导入成功")
    
    print("7. 测试 langchain_core.runnables...")
    from langchain_core.runnables import RunnablePassthrough
    print("   ✓ RunnablePassthrough 导入成功")
    
    print("\n✅ 所有导入测试通过！")
    
except ImportError as e:
    print(f"\n❌ 导入失败: {e}")
    print("\n请运行以下命令安装缺失的包：")
    print("pip install langchain langchain-community langchain-openai langchain-core langchain-text-splitters")

