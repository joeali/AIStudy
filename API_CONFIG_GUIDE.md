"""
模拟API模式 - 用于前端功能测试
不需要真实的API Key
"""
import asyncio
import random
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Study Mock API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模拟的AI响应
MOCK_RESPONSES = {
    "greeting": "你好！我是AI学习助手，请问有什么可以帮你的吗？",
    "default": "这是一个很好的问题。让我们一步步来分析...",
    "mistake": "我发现了这道题的错误原因。学生可能在计算过程中出现了失误...",
    "guide": "好的，让我来引导你思考。首先，你能告诉我这道题在问什么吗？"
}

@app.post("/api/chat")
async def mock_chat(request: dict):
    """模拟对话API"""
    await asyncio.sleep(0.5)  # 模拟网络延迟
    return {
        "success": True,
        "response": MOCK_RESPONSES["default"]
    }

@app.post("/api/detect/mistakes")
async def mock_detect(request: dict):
    """模拟错题检测"""
    await asyncio.sleep(1)
    return {
        "success": True,
        "data": {
            "mistakes": [
                {"question_no": "3", "reason": "计算错误"},
                {"question_no": "7", "reason": "概念不清"}
            ],
            "detailed_analysis": "通过分析试卷，发现学生在基础计算上存在问题..."
        }
    }
}

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🎭 Mock API 模式启动（仅用于测试）")
    print("提示: 这是模拟模式，不会调用真实的AI API")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
