#!/usr/bin/env python3
"""
自动化测试框选错题功能
"""
import requests
import base64
import json
import os
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def encode_image_to_base64(image_path):
    """将图片编码为 base64"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def test_mistake_detection(image_path, description=""):
    """测试错题检测功能"""
    print(f"\n{'='*60}")
    print(f"测试图片: {os.path.basename(image_path)}")
    if description:
        print(f"描述: {description}")
    print(f"{'='*60}")

    # 编码图片
    print("正在编码图片...")
    image_data = encode_image_to_base64(image_path)
    print(f"图片大小: {len(image_data) / 1024:.1f} KB")

    # 模拟用户框选2个错题区域
    user_marks = [
        {
            "id": 1,
            "x": 20,
            "y": 30,
            "width": 25,
            "height": 15
        },
        {
            "id": 2,
            "x": 55,
            "y": 45,
            "width": 30,
            "height": 20
        }
    ]
    print(f"模拟框选: {len(user_marks)} 个错题区域")

    # 调用 API
    print("\n正在调用错题检测 API...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/detect/mistakes",
            json={
                "image_data": image_data,
                "image_type": "jpeg",
                "user_marks": user_marks
            },
            timeout=60
        )

        print(f"HTTP 状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ API 调用成功")
            print(f"耗时: {data.get('elapsed_time', 'N/A')}")

            result = data.get('data', {})
            mistakes = result.get('mistakes', [])
            detailed_analysis = result.get('detailed_analysis', '')

            print(f"\n检测到的错题数量: {len(mistakes)}")
            for i, mistake in enumerate(mistakes, 1):
                print(f"\n  错题 {i}:")
                print(f"    题号: {mistake.get('question_no', 'N/A')}")
                print(f"    原因: {mistake.get('reason', 'N/A')}")

            if detailed_analysis:
                print(f"\n详细分析:")
                print(f"  {detailed_analysis[:200]}...")
            else:
                print(f"\n⚠️ 没有详细分析")

            return True
        else:
            print(f"❌ API 调用失败: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("="*60)
    print("自动化错题检测测试")
    print("="*60)

    # 测试图片列表
    test_images = [
        ("/Users/liulinlang/Documents/liulinlang/ai-study-companion/testdata/数学.jpg", "数学试卷"),
        ("/Users/liulinlang/Documents/liulinlang/ai-study-companion/testdata/test_enhanced.jpg", "增强版试卷"),
        ("/Users/liulinlang/Documents/liulinlang/ai-study-companion/testdata/test_crop.jpg", "裁剪版试卷"),
        ("/Users/liulinlang/Documents/liulinlang/ai-study-companion/testdata/diagnose_small.jpg", "诊断小图"),
    ]

    # 检查后端是否运行
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务未正常运行")
            return
        print("✅ 后端服务正常运行")
    except Exception as e:
        print(f"❌ 无法连接到后端服务: {str(e)}")
        return

    # 运行测试
    results = []
    for image_path, description in test_images:
        if os.path.exists(image_path):
            success = test_mistake_detection(image_path, description)
            results.append((os.path.basename(image_path), success))
        else:
            print(f"⚠️ 图片不存在: {image_path}")
            results.append((os.path.basename(image_path), False))

    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{status} - {name}")

    success_count = sum(1 for _, s in results if s)
    print(f"\n总计: {success_count}/{len(results)} 通过")

if __name__ == "__main__":
    main()
