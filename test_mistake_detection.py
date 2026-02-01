"""
测试错题检测功能
"""
import requests
import base64
import json

API_URL = "http://localhost:8000/api/detect/mistakes"
IMAGE_PATH = "/Users/liulinlang/Documents/liulinlang/ai-study-companion/testdata/数学.jpg"

def encode_image_to_base64(image_path: str) -> str:
    """将图片编码为 base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def test_mistake_detection():
    """测试错题检测 API"""
    print("=" * 60)
    print("测试错题检测功能")
    print("=" * 60)

    # 读取并编码图片
    print(f"\n📷 读取图片: {IMAGE_PATH}")
    base64_image = encode_image_to_base64(IMAGE_PATH)
    print(f"✅ 图片编码完成，大小: {len(base64_image)} 字符")

    # 构建请求数据
    request_data = {
        "image_data": base64_image,
        "image_type": "image/jpeg"
    }

    print("\n🔍 发送检测请求...")
    try:
        response = requests.post(
            API_URL,
            json=request_data,
            timeout=60
        )

        print(f"📡 响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            # 打印完整响应用于调试
            print("\n📦 完整响应:")
            print(json.dumps(result, ensure_ascii=False, indent=2))

            if result.get("success"):
                data = result.get("data", {})
                mistakes = data.get("mistakes", [])
                summary = data.get("summary", "")
                elapsed_time = result.get("elapsed_time", "")

                print("\n" + "=" * 60)
                print("检测结果")
                print("=" * 60)

                print(f"\n⏱️  耗时: {elapsed_time}")
                print(f"\n📋 {summary}")

                if mistakes:
                    print(f"\n找到 {len(mistakes)} 道错题:")
                    print("-" * 60)
                    for idx, mistake in enumerate(mistakes, 1):
                        question_no = mistake.get("question_no", "未知")
                        reason = mistake.get("reason", "")
                        print(f"{idx}. 题号: {question_no}")
                        print(f"   标记特征: {reason}")
                else:
                    print("\n⚠️  未检测到错题标记")

                print("\n" + "=" * 60)
            else:
                print(f"\n❌ 检测失败: {result.get('error', '未知错误')}")
        else:
            print(f"\n❌ 请求失败: {response.status_code}")
            print(response.text)

    except requests.exceptions.Timeout:
        print("\n⏰ 请求超时")
    except requests.exceptions.ConnectionError:
        print("\n🔌 连接失败，请确保后端服务正在运行")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")

if __name__ == "__main__":
    test_mistake_detection()
