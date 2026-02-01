#!/usr/bin/env python3
"""
API Key 更新助手
帮助用户快速更换 GLM API Key
"""

import os
import sys

def update_env_file(new_api_key):
    """更新 .env 文件"""
    env_path = "backend/.env"

    with open(env_path, "w") as f:
        f.write(f"# GLM API 配置\n")
        f.write(f"# 从 https://open.bigmodel.cn/ 获取您的 API Key\n")
        f.write(f"GLM_API_KEY={new_api_key}\n")

    print(f"✅ API Key 已保存到 {env_path}")
    return True

def update_backend_file(new_api_key):
    """直接修改 backend/main.py"""
    file_path = "backend/main.py"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 替换 API Key
    import re
    pattern = r'GLM_API_KEY = os\.getenv\("GLM_API_KEY", "[^"]*"\)'
    replacement = f'GLM_API_KEY = os.getenv("GLM_API_KEY", "{new_api_key}")'
    content = re.sub(pattern, replacement, content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ API Key 已更新到 {file_path}")
    return True

def main():
    print("=" * 60)
    print("        GLM API Key 更新助手")
    print("=" * 60)
    print()

    print("📌 获取新的 API Key:")
    print("   1. 访问 https://open.bigmodel.cn/")
    print("   2. 登录并进入控制台")
    print("   3. 获取 API Key")
    print()

    # 输入新的 API Key
    new_key = input("请输入新的 API Key: ").strip()

    if not new_key:
        print("❌ API Key 不能为空")
        return 1

    # 验证格式
    if "." not in new_key or len(new_key) < 30:
        print("⚠️  警告: API Key 格式可能不正确")
        confirm = input("是否继续? (y/n): ").strip().lower()
        if confirm != 'y':
            return 1

    print()
    print("选择保存方式:")
    print("  1. 保存到 .env 文件 (推荐)")
    print("  2. 直接修改 backend/main.py")

    choice = input("请选择 (1 或 2): ").strip()

    print()

    if choice == "1":
        # 安装 python-dotenv
        try:
            import dotenv
            print("✅ 检测到 python-dotenv 已安装")
        except ImportError:
            print("📦 正在安装 python-dotenv...")
            os.system("pip3 install python-dotenv")
            print()

        # 检查是否需要更新 backend/main.py
        with open("backend/main.py", "r", encoding="utf-8") as f:
            main_content = f.read()

        if "from dotenv import load_dotenv" not in main_content:
            print("📝 正在更新 backend/main.py 以支持 .env 文件...")
            # 在导入部分添加 dotenv
            main_content = main_content.replace(
                "import uvicorn",
                "from dotenv import load_dotenv\nimport uvicorn"
            )
            # 在 GLM_API_KEY 定义前添加 load_dotenv()
            main_content = main_content.replace(
                '# ==================== 配置 ====================',
                '# ==================== 配置 ====================\nload_dotenv()'
            )

            with open("backend/main.py", "w", encoding="utf-8") as f:
                f.write(main_content)
            print("✅ backend/main.py 已更新")

        update_env_file(new_key)
        print()
        print("💡 提示: .env 文件不会被 Git 追踪，更安全")

    elif choice == "2":
        update_backend_file(new_key)
        print()
        print("⚠️  注意: API Key 已硬编码到代码中，请勿提交到 Git")

    else:
        print("❌ 无效选择")
        return 1

    print()
    print("=" * 60)
    print("🎉 API Key 更新完成！")
    print("=" * 60)
    print()
    print("接下来:")
    print("  1. 重启后端服务")
    print("  2. 测试新的 API Key 是否有效")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
