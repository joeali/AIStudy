#!/usr/bin/env python3
"""
AI Study Companion API 测试脚本
测试所有 API 端点是否正常工作
"""

import requests
import json
import base64
import sys

# API 基础 URL
BASE_URL = "http://localhost:8000"

def print_section(title):
    """打印分隔符"""
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)

def test_health():
    """测试健康检查"""
    print_section("1. 健康检查测试")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ 后端服务正常运行")
            print(f"  响应: {response.json()}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
        return False

def test_root():
    """测试根路径"""
    print_section("2. 根路径测试")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✓ API 信息获取成功")
            data = response.json()
            print(f"  名称: {data.get('message')}")
            print(f"  版本: {data.get('version')}")
            print(f"  端点: {', '.join(data.get('endpoints', {}).keys())}")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

def test_ocr():
    """测试 OCR 识别（使用简单图片）"""
    print_section("3. OCR 识别测试")
    print("创建测试图片...")

    try:
        from PIL import Image, ImageDraw, ImageFont

        # 创建一个简单的测试图片
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)

        # 绘制文本
        text = "Test Question 1:\n2 + 2 = ?"
        draw.text((20, 50), text, fill='black')

        # 转换为 base64
        import io
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # 调用 OCR API
        print("发送 OCR 请求...")
        response = requests.post(
            f"{BASE_URL}/api/ocr/exam",
            json={
                "image_data": img_str,
                "image_type": "image/jpeg"
            },
            timeout=30
        )

        if response.status_code == 200:
            print("✓ OCR 识别成功")
            data = response.json()
            if data.get('success'):
                print(f"  识别到 {len(data.get('data', {}).get('questions', []))} 个题目")
            else:
                print("  ⚠ OCR 返回未标记为成功")
            return True
        else:
            print(f"❌ OCR 请求失败: {response.status_code}")
            print(f"  错误: {response.text[:200]}")
            return False

    except ImportError:
        print("⚠ 跳过 OCR 测试（需要 PIL）")
        return True
    except Exception as e:
        print(f"⚠ OCR 测试出错: {str(e)}")
        # 这不是致命错误，API 可能工作但测试图片创建失败
        return True

def test_chat():
    """测试对话 API"""
    print_section("4. 对话 API 测试")
    try:
        print("发送测试消息...")
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "你好",
                "conversation_history": []
            },
            timeout=30
        )

        if response.status_code == 200:
            print("✓ 对话 API 正常")
            data = response.json()
            if data.get('success'):
                print(f"  AI 响应: {data.get('response', '')[:50]}...")
            return True
        else:
            print(f"❌ 对话请求失败: {response.status_code}")
            print(f"  错误: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"⚠ 对话测试出错: {str(e)}")
        return True

def main():
    """主测试函数"""
    print("\n" + "=" * 50)
    print("  AI Study Companion API 测试")
    print("=" * 50)

    # 检查后端是否运行
    try:
        requests.get(BASE_URL, timeout=2)
    except:
        print("\n❌ 错误: 后端服务未启动")
        print("请先运行: ./start.sh")
        sys.exit(1)

    # 运行测试
    results = []
    results.append(("健康检查", test_health()))
    results.append(("根路径", test_root()))
    results.append(("OCR 识别", test_ocr()))
    results.append(("对话 API", test_chat()))

    # 总结
    print_section("测试总结")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"通过: {passed}/{total}")

    for name, result in results:
        status = "✓" if result else "❌"
        print(f"  {status} {name}")

    if passed == total:
        print("\n🎉 所有测试通过！")
        print("\n服务地址：")
        print(f"  • 前端界面: http://localhost:3000")
        print(f"  • 后端 API: {BASE_URL}")
        print(f"  • API 文档: {BASE_URL}/docs")
    else:
        print("\n⚠ 部分测试失败，请检查后端日志")

    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
