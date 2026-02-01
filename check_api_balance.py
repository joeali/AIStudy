#!/usr/bin/env python3
"""
查询智谱AI API Key 额度和使用情况
"""

import requests
import json
import os
import sys

# 从 backend/main.py 读取 API Key
def get_api_key():
    try:
        with open("backend/main.py", "r") as f:
            content = f.read()
            # 提取默认的 API Key
            import re
            match = re.search(r'GLM_API_KEY = os\.getenv\("GLM_API_KEY", "([^"]+)"\)', content)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"读取 API Key 失败: {e}")
        return None

def check_balance():
    """查询 API 余额"""

    # 尝试从环境变量或配置文件获取
    api_key = os.getenv("GLM_API_KEY") or get_api_key()

    if not api_key:
        print("❌ 未找到 API Key")
        return False

    print(f"🔑 使用的 API Key: {api_key[:20]}...{api_key[-10:]}")
    print()

    # 智谱 AI 用户信息查询接口
    # 参考: https://open.bigmodel.cn/dev/api#user
    user_info_url = "https://open.bigmodel.cn/api/paas/v4/user/info"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print("正在查询余额信息...")
    try:
        response = requests.get(user_info_url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()

            print("=" * 60)
            print("           智谱 AI 账户余额信息")
            print("=" * 60)
            print()

            # 解析余额信息
            if "data" in data:
                user_data = data["data"]

                # 显示余额
                if "balance" in user_data:
                    balance = user_data["balance"]
                    print(f"💰 账户余额: {balance}")

                # 显示 token 使用情况
                if "total_tokens" in user_data:
                    total_tokens = user_data["total_tokens"]
                    print(f"📊 总使用 tokens: {total_tokens:,}")

                # 显示其他信息
                if "status" in user_data:
                    status = user_data["status"]
                    print(f"📌 账户状态: {status}")

            print()
            print("=" * 60)

            # 检查是否有免费额度
            if "data" in data and "free_balance" in data["data"]:
                free_balance = data["data"]["free_balance"]
                print(f"🎁 免费额度余额: {free_balance}")
                print()

            return True

        elif response.status_code == 401:
            print("❌ API Key 无效或已过期")
            print()
            print("建议:")
            print("  1. 检查 API Key 是否正确")
            print("  2. 访问 https://open.bigmodel.cn/ 重新获取")
            return False

        elif response.status_code == 429:
            print("❌ 余额不足")
            print()
            print("当前 API Key 的余额已用完，需要充值或获取免费额度")
            print()
            print("解决方法:")
            print("  1. 访问 https://open.bigmodel.cn/")
            print("  2. 登录并进入控制台")
            print("  3. 查看是否有免费额度可领取")
            print("  4. 或充值后继续使用")
            print()
            print("更换 API Key 方法:")
            print("  python3 update_api_key.py")
            return False

        else:
            print(f"❌ 查询失败 (HTTP {response.status_code})")
            print(f"响应: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ 请求超时，请检查网络连接")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 网络连接失败")
        print("请检查:")
        print("  - 网络连接是否正常")
        print("  - 是否需要代理")
        return False
    except Exception as e:
        print(f"❌ 查询出错: {e}")
        return False

def test_api_call():
    """测试 API 调用是否正常"""
    print()
    print("正在测试 API 调用...")
    print("-" * 60)

    api_key = os.getenv("GLM_API_KEY") or get_api_key()

    if not api_key:
        print("❌ 未找到 API Key")
        return False

    # 发送一个简单的测试请求
    test_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "glm-4-flash",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "max_tokens": 10
    }

    try:
        response = requests.post(test_url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            print("✅ API 调用成功！")
            print()
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                print(f"AI 回复: {content}")
            print()
            print("说明: API Key 有效，可以正常使用")
            return True
        elif response.status_code == 429:
            print("❌ API 调用失败: 余额不足")
            print()
            print("错误详情: 429 Too Many Requests / 余额不足")
            print()
            print("建议操作:")
            print("  1. 访问 https://open.bigmodel.cn/console/finance")
            print("  2. 查看账户余额和使用情况")
            print("  3. 充值或领取免费额度")
            print("  4. 使用 python3 update_api_key.py 更换 API Key")
            return False
        else:
            print(f"❌ API 调用失败 (HTTP {response.status_code})")
            try:
                error_data = response.json()
                print(f"错误信息: {error_data}")
            except:
                print(f"错误信息: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "智谱 AI 额度查询工具" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    # 查询余额
    balance_ok = check_balance()

    # 测试 API 调用
    api_ok = test_api_call()

    print()
    print("=" * 60)
    print("查询结果汇总")
    print("=" * 60)

    if balance_ok and api_ok:
        print()
        print("✅ 状态: API Key 有效，可以正常使用")
        print()
        print("您可以:")
        print("  • 继续使用 AI Study 应用")
        print("  • 访问 http://localhost:3000")
        print()
    else:
        print()
        print("❌ 状态: API Key 需要更新")
        print()
        print("建议操作:")
        print("  1. 访问 https://open.bigmodel.cn/")
        print("  2. 获取新的 API Key")
        print("  3. 运行: python3 update_api_key.py")
        print("  4. 重启服务: ./start.sh")
        print()

    print("=" * 60)
    print()

if __name__ == "__main__":
    main()
