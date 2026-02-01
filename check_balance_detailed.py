import requests
import re

# 读取 API Key
with open("backend/main.py", "r") as f:
    content = f.read()
    match = re.search(r'GLM_API_KEY = os\.getenv\("GLM_API_KEY", "([^"]+)"\)', content)
    api_key = match.group(1) if match else "Not found"

print(f"🔑 API Key: {api_key[:20]}...{api_key[-10:]}")
print()

# 尝试多个可能的接口
endpoints = [
    ("用户信息", "https://open.bigmodel.cn/api/paas/v4/user/info"),
    ("账户余额", "https://open.bigmodel.cn/api/paas/v4/user/balance"),
    ("API密钥信息", "https://open.bigmodel.cn/api/paas/v4/api/key"),
]

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

for name, url in endpoints:
    print(f"尝试查询: {name}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ 成功! 响应: {response.text[:200]}")
        elif response.status_code == 401:
            print("❌ 未授权: API Key 无效")
        elif response.status_code == 404:
            print("⚠️  接口不存在 (404)")
        elif response.status_code == 429:
            print("❌ 余额不足 (429)")
        else:
            print(f"响应: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    print("-" * 60)

print()
print("💡 建议:")
print("   由于余额查询接口可能需要特殊权限，")
print("   请直接访问控制台查看详细余额信息:")
print("   https://open.bigmodel.cn/console/finance")
