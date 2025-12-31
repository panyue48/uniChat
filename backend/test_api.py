"""
快速测试后端 API 是否正常工作
"""
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    """测试健康检查接口"""
    print("1. 测试健康检查接口...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print(f"   ✓ 健康检查通过: {response.json()}")
            return True
        else:
            print(f"   ✗ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ 连接失败: {e}")
        print("   请确保后端服务正在运行: python main.py")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("后端 API 测试")
    print("=" * 50)
    if test_health():
        print("\n✅ 后端服务运行正常！")
        print("\n下一步：")
        print("1. 确保已创建 .env 文件并配置了 API Key")
        print("2. 启动前端项目（微信开发者工具）")
        print("3. 测试上传 PDF 和问答功能")
    else:
        print("\n❌ 后端服务未正常运行")
        print("请检查：")
        print("1. 后端服务是否已启动（python main.py）")
        print("2. 端口 8000 是否被占用")

