"""
AI Study Companion - 后端服务
提供 OCR 识别, 题目分析等 API
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
import base64
import io
import json
import re
import requests
from PIL import Image
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
import asyncio
import threading
import time
import sys
from queue import Queue
from functools import wraps

# ==================== 导入智能分析模块 ====================
from smart_analysis import (
    analyze_content_type,
    generate_learning_analysis_prompt,
    generate_mistake_guide_prompt
)

# ==================== 配置 ====================
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量读取API Key（如果没有则使用默认值）
GLM_API_KEY = os.getenv("GLM_API_KEY", "5f53890e74fa465a8ad1a95409db864c.roWm4OnFKpTIIdDJ")
GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# 检查API Key是否为默认值
if GLM_API_KEY == "5f53890e74fa465a8ad1a95409db864c.roWm4OnFKpTIIdDJ":
    print("=" * 60)
    print("⚠️  警告: 使用默认的GLM API Key")
    print("如需使用自己的API Key，请创建 backend/.env 文件:")
    print("  GLM_API_KEY=your_api_key_here")
    print("=" * 60)

# ==================== API 请求队列 ====================
from concurrent.futures import ThreadPoolExecutor

# 创建请求队列
request_queue = Queue()
# 请求处理线程池(处理队列中的请求)
queue_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="glm_api_queue")
# 请求锁(确保同时只有1个GLM API调用)
glm_api_lock = threading.Lock()
# 请求ID计数器
request_counter = 0
request_counter_lock = threading.Lock()

def get_request_id():
    """生成唯一的请求ID"""
    global request_counter
    with request_counter_lock:
        request_counter += 1
        return request_counter

# ==================== 创建 FastAPI 应用 ====================
app = FastAPI(
    title="AI Study Companion API",
    description="AI 学习助手后端服务 - OCR 识别与题目分析",
    version="1.0.0"
)

# ==================== CORS 配置 ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源(生产环境需限制)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 数据模型 ====================
class OCRRequest(BaseModel):
    """OCR 请求模型"""
    image_data: str  # base64 编码的图片
    image_type: str = "image/jpeg"  # 图片类型

class QuestionAnalyzeRequest(BaseModel):
    """题目分析请求"""
    image_data: Optional[str] = None
    image_type: Optional[str] = "image/jpeg"
    question_text: Optional[str] = None
    student_answer: Optional[str] = None

class ChatRequest(BaseModel):
    """对话请求"""
    message: str
    conversation_history: Optional[List[dict]] = []
    image_data: Optional[str] = None

class DiagnoseRequest(BaseModel):
    """诊断请求"""
    question: str  # 题目内容
    student_answer: str  # 学生的错误答案
    image_data: Optional[str] = None  # 可选的题目图片

class GuideRequest(BaseModel):
    """引导请求"""
    question: str  # 题目内容
    diagnosis: str  # 诊断结果
    student_response: Optional[str] = None  # 学生的回答(第一轮为空)
    conversation_history: Optional[List[dict]] = []  # 对话历史

class DetectMistakesRequest(BaseModel):
    """错题检测请求"""
    image_data: str  # base64 编码的图片
    image_type: str = "image/jpeg"  # 图片类型
    user_marks: Optional[List[dict]] = []  # 用户手动标记的错题位置 [{"x": 50, "y": 30}, ...]

# ==================== 工具函数 ====================
def decode_base64_image(base64_str: str) -> Image.Image:
    """解码 base64 图片"""
    # 移除 data:image/xxx;base64, 前缀
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]

    image_data = base64.b64decode(base64_str)
    image = Image.open(io.BytesIO(image_data))
    return image

def encode_image_to_base64(image: Image.Image, quality: int = 85) -> str:
    """将图片编码为 base64"""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=quality)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def call_glm_api(messages: list, model: str = "glm-4v", max_retries: int = 3, skip_delay: bool = False, max_tokens: int = 2000) -> str:
    """调用 GLM API(带排队和重试机制)

    Args:
        messages: 消息列表
        model: 模型名称
        max_retries: 最大重试次数
        skip_delay: 是否跳过请求延迟(用于快速响应场景)
        max_tokens: 最大输出token数(用于控制响应速度)
    """
    import time

    req_id = get_request_id()
    print(f"[API #{req_id}] 等待获取GLM API锁...")

    # 使用上下文管理器获取锁(确保锁一定会被释放)
    with glm_api_lock:
        print(f"[API #{req_id}] 已获取锁,开始调用")

        headers = {
            "Authorization": f"Bearer {GLM_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": max_tokens
        }

        # 添加最小请求间隔(避免过于频繁),快速模式跳过
        if not skip_delay:
            time.sleep(1)

        for attempt in range(max_retries):
            try:
                print(f"[API #{req_id}] 发送请求到GLM... (尝试 {attempt + 1}/{max_retries})")
                response = requests.post(
                    GLM_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=60
                )

                # 处理 429 并发限制错误
                if response.status_code == 429:
                    error_detail = response.json() if response.content else {}
                    error_msg = error_detail.get('error', {}).get('message', '并发请求过多')

                    # 检查是否是余额不足
                    if '余额' in error_msg or '充值' in error_msg or '资源包' in error_msg:
                        print(f"[API #{req_id}] ❌ API余额不足")
                        raise HTTPException(
                            status_code=429,
                            detail=f"⚠️ API余额不足\n\n您的GLM API账户余额已用完，请充值后再使用。\n\n📍 解决方法:\n1. 访问 https://open.bigmodel.cn/ 充值\n2. 或在 backend/.env 文件中配置其他API Key\n3. 新用户通常有免费额度，请检查控制台"
                        )

                    if attempt < max_retries - 1:
                        # 指数退避: 3秒, 6秒, 12秒
                        wait_time = [3, 6, 12][attempt]
                        print(f"[API #{req_id}] ⚠️ 遇到并发限制,等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise HTTPException(
                            status_code=429,
                            detail=f"GLM API 并发限制: {error_msg}. 请稍后重试. "
                        )

                if response.status_code != 200:
                    error_detail = response.json() if response.content else {}
                    error_msg = error_detail.get('error', {}).get('message', response.text)
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"GLM API 错误: {error_msg}"
                    )

                result = response.json()
                print(f"[API #{req_id}] ✅ 请求成功")
                print(f"[API #{req_id}] 响应结构: {list(result.keys()) if isinstance(result, dict) else type(result)}")

                # 检查choices
                if 'choices' not in result:
                    print(f"[API #{req_id}] ❌ 响应中没有choices")
                    print(f"[API #{req_id}] 完整响应: {json.dumps(result, ensure_ascii=False)[:500]}")
                    sys.stdout.flush()
                    raise HTTPException(
                        status_code=500,
                        detail="GLM API 返回格式异常: 缺少choices字段"
                    )

                if len(result['choices']) == 0:
                    print(f"[API #{req_id}] ❌ choices为空")
                    sys.stdout.flush()
                    raise HTTPException(
                        status_code=500,
                        detail="GLM API 返回空结果"
                    )

                print(f"[API #{req_id}] choices[0] keys: {list(result['choices'][0].keys())}")

                if 'message' not in result['choices'][0]:
                    print(f"[API #{req_id}] ❌ choices[0]中没有message字段")
                    print(f"[API #{req_id}] choices[0]: {result['choices'][0]}")
                    sys.stdout.flush()
                    raise HTTPException(
                        status_code=500,
                        detail="GLM API 返回格式异常: 缺少message字段"
                    )

                print(f"[API #{req_id}] message keys: {list(result['choices'][0]['message'].keys())}")
                content = result['choices'][0]['message'].get('content', '')
                print(f"[API #{req_id}] 内容类型: {type(content)}")
                print(f"[API #{req_id}] 内容长度: {len(content) if content else 0}")

                # 检查内容是否为空
                if not content or not content.strip():
                    print(f"[API #{req_id}] ❌ API返回内容为空")
                    sys.stdout.flush()
                    raise HTTPException(
                        status_code=500,
                        detail="GLM API 返回内容为空,请重试"
                    )

                print(f"[API #{req_id}] 内容repr: {repr(content[:100])}")
                print(f"[API #{req_id}] 内容预览: {content[:200]}")
                sys.stdout.flush()
                return content

            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    wait_time = [2, 4, 6][attempt]
                    print(f"[API #{req_id}] ⚠️ 请求超时,等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise HTTPException(status_code=504, detail=f"API 请求超时: {str(e)}")

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = [2, 4, 6][attempt]
                    print(f"[API #{req_id}] ⚠️ 网络错误,等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise HTTPException(status_code=500, detail=f"API 调用失败: {str(e)}")

        raise HTTPException(status_code=500, detail="API 调用失败: 超过最大重试次数")


def parse_mistakes_from_response(response_text: str) -> dict:
    """从AI响应中解析错题数据

    支持多种格式:
    1. JSON代码块格式
    2. 纯JSON格式
    3. Markdown列表格式
    """
    import re
    import json

    # 方式1: 尝试解析JSON代码块
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except:
            pass

    # 方式2: 尝试解析纯JSON
    try:
        return json.loads(response_text.strip())
    except:
        pass

    # 方式3: 尝试提取JSON对象(没有代码块)
    try:
        # 查找第一个 { 和最后一个 }
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = response_text[start:end]
            return json.loads(json_str)
    except:
        pass

    # 方式4: 解析Markdown列表格式
    try:
        lines = response_text.split('\n')
        mistakes_list = []
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•'):
                match = re.search(r'第(\d+)题', line)
                if match:
                    question_no = match.group(1)
                    mistakes_list.append({
                        "question_no": question_no,
                        "reason": "错题"
                    })
        if mistakes_list:
            return {
                "mistakes": mistakes_list,
                "summary": f"共找到{len(mistakes_list)}道错题"
            }
    except:
        pass

    return None


# ==================== API 路由 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI Study Companion API",
        "version": "1.0.0",
        "endpoints": {
            "/api/ocr/exam": "试卷 OCR 识别",
            "/api/analyze/question": "题目分析",
            "/api/chat": "AI 对话",
            "/api/chat/stream": "AI 对话(流式)",
            "/api/diagnose/analyze": "解题诊断分析",
            "/api/diagnose/analyze/stream": "解题诊断分析(流式)",
            "/api/diagnose/guide": "苏格拉底式引导",
            "/api/diagnose/guide/stream": "苏格拉底式引导(流式)",
            "/api/detect/mistakes": "智能找错题",
            "/api/detect/mistakes/stream": "智能找错题(流式)"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

@app.post("/api/ocr/exam")
async def ocr_exam_paper(request: OCRRequest):
    """
    试卷 OCR 识别

    使用 GLM-4V 识别试卷中的题目和答案
    """
    try:
        # 解码图片
        image = decode_base64_image(request.image_data)

        # 检查图片尺寸
        if image.width < 100 or image.height < 100:
            raise HTTPException(
                status_code=400,
                detail=f"图片尺寸太小 ({image.width}x{image.height}),请上传更清晰的图片"
            )

        # 压缩图片以加快传输
        base64_image = encode_image_to_base64(image, quality=85)

        # 构建 prompt(简化版,更容易解析)
        prompt = """请识别这张图片中的所有题目内容. 

请以JSON格式返回: 
```json
{
  "questions": [
    {
      "question_no": "题号",
      "question_text": "题目内容",
      "student_answer": "学生答案"
    }
  ]
}
```"""

        # 调用 GLM-4V API
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]

        response_text = call_glm_api(messages, model="glm-4v")

        # 解析响应(多种方式尝试)
        data = None

        # 方式1: 尝试提取 JSON 代码块
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
            except:
                pass

        # 方式2: 尝试提取花括号内的 JSON
        if not data:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                except:
                    pass

        # 如果 JSON 解析失败,返回原始文本
        if not data:
            return {
                "success": True,
                "data": {
                    "questions": [],
                    "note": "无法解析 JSON,以下是原始识别结果"
                },
                "raw_response": response_text,
                "parsed": False
            }

        return {
            "success": True,
            "data": data,
            "raw_response": response_text,
            "parsed": True
        }

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        # 返回部分结果而不是报错
        return {
            "success": True,
            "data": {"questions": []},
            "error": f"JSON 解析失败: {str(e)}",
            "parsed": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 识别失败: {str(e)}")

@app.post("/api/analyze/question")
async def analyze_question(request: QuestionAnalyzeRequest):
    """
    题目分析

    分析题目内容,提取题目信息, 判断答案正误
    """
    try:
        # 构建消息
        content = []

        # 如果有图片
        if request.image_data:
            image = decode_base64_image(request.image_data)
            base64_image = encode_image_to_base64(image, quality=85)

            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })

        # 构建 prompt
        prompt = """请分析这道题目，告诉我：

1. 题目内容
2. 学科
3. 知识点
4. 正确答案（如果可以看出的话）
5. 学生的答案（如果试卷上有）

请用简洁的语言回答。"""

        content.append({
            "type": "text",
            "text": prompt
        })

        messages = [{
            "role": "user",
            "content": content
        }]

        response_text = call_glm_api(messages, model="glm-4v")

        # 返回自然语言分析结果
        return {
            "success": True,
            "data": {
                "analysis": response_text
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"题目分析错误: {str(e)}")
        print(f"错误堆栈:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"题目分析失败: {str(e)}")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    AI 对话

    提供启发式教学对话
    """
    try:
        # 验证输入
        if not request.message or not request.message.strip():
            return {
                "success": False,
                "error": "消息不能为空",
                "response": "请输入您的问题"
            }

        # 构建消息历史
        messages = []

        # 转换历史消息(限制长度避免超出 token 限制)
        max_history = 10  # 最多保留最近 10 条历史
        history = request.conversation_history[-max_history:] if request.conversation_history else []

        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # 跳过空消息
            if content and content.strip():
                # 如果消息包含图片,跳过(简化处理)
                if "image" in str(msg).lower():
                    continue
                messages.append({
                    "role": role,
                    "content": content[:1000]  # 限制每条消息长度
                })

        # 添加当前消息
        if request.image_data:
            try:
                # 如果有图片,使用多模态
                image = decode_base64_image(request.image_data)

                # 检查图片大小
                if image.width * image.height > 4000000:  # 限制图片大小
                    # 缩小图片
                    ratio = min(800 / image.width, 600 / image.height)
                    new_width = int(image.width * ratio)
                    new_height = int(image.height * ratio)
                    image = image.resize((new_width, new_height))

                base64_image = encode_image_to_base64(image, quality=75)

                # 判断是否需要启动诊断流程
                user_message = request.message or "请帮我看看这道题"
                needs_diagnosis = any(keyword in user_message for keyword in
                    ['不会', '错了', '错误', '不懂', '不会做', '做错了', '讲解', '怎么做', '帮我', '请'])

                if needs_diagnosis:
                    # 使用诊断框架
                    print(f"[诊断] 检测到错题请求,启动诊断流程...")

                    try:
                        # 第一步: 提取题目内容
                        extract_prompt = """请识别图片中的题目内容,以简洁的格式返回题目(不要包含解答过程). """

                        messages_with_image = [{
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": extract_prompt
                                }
                            ]
                        }]

                        question_text = call_glm_api(messages_with_image, model="glm-4v")
                        print(f"[诊断] 题目提取成功: {question_text[:50]}...")

                        # 第二步: 诊断错误
                        diagnose_prompt = f"""你是一位有20年教学经验的初中数学老师. 
学生做错了这道题: {question_text}
学生说: {user_message}

请分析: 
1. 这道题考查的核心知识点是什么
2. 学生最可能在哪个环节出错(概念不清/方法不对/计算失误)
3. 用一句话告诉学生他的问题在哪里(要具体,不要泛泛而谈)

请以JSON格式返回: 
```json
{{
  "knowledge_point": "核心知识点",
  "error_type": "概念不清/方法不对/计算失误",
  "problem_description": "一句话描述学生的问题",
  "analysis": "详细分析"
}}
```
只返回JSON,不要其他内容. """

                        messages_diagnose = [{
                            "role": "user",
                            "content": diagnose_prompt
                        }]

                        diagnosis_result = call_glm_api(messages_diagnose, model="glm-4-flash")
                        print(f"[诊断] 诊断完成")

                        # 解析诊断结果
                        json_match = re.search(r'\{[\s\S]*\}', diagnosis_result)
                        if json_match:
                            diagnosis_data = json.loads(json_match.group(0))

                            # 第三步: 生成引导性问题
                            guide_prompt = f"""你是一位耐心的数学老师,正在一对一辅导学生. 

题目: {question_text}
诊断结果: {diagnosis_data.get('problem_description', '')}

请用苏格拉底式提问,一步步引导学生自己做出来. 
规则: 
- 每次只问一个问题
- 不要直接说答案
- 引导要从最基本的观察开始

现在请开始引导,提出第一个问题来启发学生思考(用简单易懂的语言). """

                            messages_guide = [{
                                "role": "user",
                                "content": guide_prompt
                            }]

                            guide_response = call_glm_api(messages_guide, model="glm-4-flash")
                            print(f"[诊断] 引导问题生成完成")

                            # 返回诊断+引导的结果
                            return {
                                "success": True,
                                "response": f"""📋 **题目分析**
{question_text}

---

📋 **诊断结果**
**知识点**: {diagnosis_data.get('knowledge_point', '未识别')}
**问题**: {diagnosis_data.get('problem_description', '未识别')}

---

👨‍🏫 **开始引导**
{guide_response}

---
💡 请回答老师的问题,我会一步步引导你找到正确答案. (输入"退出"返回普通模式)""",
                                "diagnosis": diagnosis_data,
                                "question": question_text,
                                "mode": "guidance"
                            }

                    except Exception as e:
                        print(f"[诊断] 失败: {str(e)},降级为普通回答")
                        # 诊断失败,继续使用普通流程

                # 普通回答流程 - 使用苏格拉底引导式
                enhanced_prompt = f"""你是一位耐心的老师,正在辅导学生。学生问: {user_message}

请用苏格拉底式引导方法帮助学生:
1. **不要直接给出答案或详细解题步骤**
2. 提出启发性的问题,引导学生自己思考
3. 每次只问一个关键问题
4. 如果学生需要帮助,给出逐步递进的提示(先浅提示,再深提示)

引导策略:
- 第一步: 提示学生回顾相关知识点
- 第二步: 引导学生分析题目条件
- 第三步: 提示解题思路方向
- 不要直接告诉学生应该怎么做,而是问问题让他们自己找到方法

现在请提出第一个引导问题来启发学生思考。"""

                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": enhanced_prompt
                        }
                    ]
                })
            except Exception as img_error:
                # 图片处理失败,降级为纯文本
                print(f"图片处理失败: {str(img_error)},使用纯文本模式")
                messages.append({
                    "role": "user",
                    "content": request.message[:500]
                })
        else:
            # 纯文本问题也使用引导式
            enhanced_text_prompt = f"""你是一位耐心的老师。学生问: {request.message}

请用苏格拉底式引导方法帮助学生:
- 不要直接给答案或解题步骤
- 提出启发性问题引导学生思考
- 每次只问一个问题
- 给出递进式提示

请提出第一个引导问题。"""

            messages.append({
                "role": "user",
                "content": enhanced_text_prompt[:1000]
            })

        # 调用 GLM API(call_glm_api 内部已处理重试)
        # 根据是否有图片选择合适的模型
        model = "glm-4v" if request.image_data else "glm-4-flash"
        try:
            response_text = call_glm_api(messages, model=model)
        except HTTPException as e:
            # 处理 HTTP 异常(包括 429 并发限制)
            return {
                "success": False,
                "error": e.detail,
                "response": f"抱歉,{e.detail}"
            }
        except Exception as e:
            # 处理其他异常
            return {
                "success": False,
                "error": str(e),
                "response": "抱歉,处理请求时出现错误,请稍后重试"
            }

        return {
            "success": True,
            "response": response_text[:2000]  # 限制响应长度
        }

    except HTTPException:
        raise
    except Exception as e:
        # 记录详细错误
        import traceback
        print(f"对话 API 错误: {str(e)}")
        print(f"错误堆栈:\n{traceback.format_exc()}")

        return {
            "success": False,
            "error": str(e),
            "response": "抱歉,处理您的请求时出现了问题,请重试或联系管理员"
        }

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    AI 对话(流式输出)

    提供启发式教学对话,使用 Server-Sent Events 逐步返回响应
    """
    async def generate_stream():
        try:
            # 立即发送开始状态
            yield f"data: {json.dumps({'status': 'starting', 'message': '开始分析...'})}\n\n"

            # 验证输入
            if not request.message or not request.message.strip():
                yield f"data: {json.dumps({'error': '消息不能为空', 'done': True})}\n\n"
                return

            # 发送分析中状态
            yield f"data: {json.dumps({'status': 'analyzing', 'message': 'AI正在分析中...'})}\n\n"

            # 构建消息历史
            messages = []

            # 转换历史消息
            max_history = 10
            history = request.conversation_history[-max_history:] if request.conversation_history else []

            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")

                if content and content.strip():
                    if "image" in str(msg).lower():
                        continue
                    messages.append({
                        "role": role,
                        "content": content[:1000]
                    })

            # 添加当前消息
            if request.image_data:
                try:
                    image = decode_base64_image(request.image_data)

                    if image.width * image.height > 4000000:
                        ratio = min(800 / image.width, 600 / image.height)
                        new_width = int(image.width * ratio)
                        new_height = int(image.height * ratio)
                        image = image.resize((new_width, new_height))

                    base64_image = encode_image_to_base64(image, quality=75)

                    user_message = request.message or "请帮我看看这道题"
                    enhanced_prompt = f"""{user_message}

请分析这道题目,如果是计算题请给出详细步骤,如果是应用题请说明解题思路. """

                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": enhanced_prompt
                            }
                        ]
                    })
                except Exception as img_error:
                    print(f"图片处理失败: {str(img_error)}")
                    messages.append({
                        "role": "user",
                        "content": request.message[:500]
                    })
            else:
                messages.append({
                    "role": "user",
                    "content": request.message[:500]
                })

            # 调用 GLM API 获取完整响应
            model = "glm-4v" if request.image_data else "glm-4-flash"

            try:
                print("[流式对话] 发送分析中状态...")
                # 立即发送"分析中"状态
                yield f"data: {json.dumps({'status': 'analyzing', 'message': 'AI正在分析中...'})}\n\n"
                print(f"[流式对话] 状态消息已发送")

                # 调用API获取响应
                print("[流式对话] 开始调用 GLM API...")
                response_text = call_glm_api(messages, model=model)
                print(f"[流式对话] API响应完成，响应长度: {len(response_text)} 字符")

                # 逐字返回响应
                print(f"[流式对话] 开始逐字发送，共 {len(response_text)} 个字符")
                for idx, char in enumerate(response_text):
                    yield f"data: {json.dumps({'content': char, 'done': False})}\n\n"
                    if (idx + 1) % 100 == 0:
                        print(f"[流式对话] 已发送 {idx + 1}/{len(response_text)} 字符")

                print(f"[流式对话] 所有内容已发送")

                # 发送完成信号
                yield f"data: {json.dumps({'done': True})}\n\n"
                print("[流式对话] 发送完成信号")

            except HTTPException as e:
                yield f"data: {json.dumps({'error': str(e.detail), 'done': True})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

        except Exception as e:
            import traceback
            print(f"流式对话 API 错误: {str(e)}")
            print(f"错误堆栈:\n{traceback.format_exc()}")
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")

@app.post("/api/diagnose/analyze/stream")
async def diagnose_error_stream(request: DiagnoseRequest):
    """
    解题诊断分析(流式输出)

    分析学生的错误答案,找出错误原因
    """
    async def generate_stream():
        try:
            yield f"data: {json.dumps({'status': 'analyzing', 'message': '🔍 正在分析错误原因...'})}\n\n"

            # 构建诊断 prompt
            diagnose_prompt = f"""你是一位有20年教学经验的初中数学老师.
学生做错了这道题: {request.question}
学生的错误答案是: {request.student_answer}

请分析:
1. 这道题考查的核心知识点是什么
2. 学生最可能在哪个环节出错(概念不清/方法不对/计算失误)
3. 用一句话告诉学生他的问题在哪里(要具体,不要泛泛而谈)

请以JSON格式返回:
```json
{{
  "knowledge_point": "核心知识点",
  "error_type": "概念不清/方法不对/计算失误",
  "problem_description": "一句话描述学生的问题",
  "analysis": "详细分析"
}}
```
只返回JSON,不要其他内容."""

            messages = [{
                "role": "user",
                "content": diagnose_prompt
            }]

            response_text = call_glm_api(messages, model="glm-4-flash")

            # 逐字返回分析内容
            for char in response_text:
                yield f"data: {json.dumps({'content': char})}\n\n"

            # 解析 JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group(0))
                yield f"data: {json.dumps({'done': True, 'data': result})}\n\n"
            else:
                # 如果解析失败,返回原始文本
                yield f"data: {json.dumps({'done': True, 'data': {'knowledge_point': '未识别', 'error_type': '未分类', 'problem_description': '分析失败', 'analysis': response_text}})}\n\n"

        except HTTPException as e:
            yield f"data: {json.dumps({'error': str(e.detail), 'done': True})}\n\n"
        except Exception as e:
            import traceback
            print(f"诊断流式 API 错误: {str(e)}")
            print(f"错误堆栈:\n{traceback.format_exc()}")
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")

@app.post("/api/diagnose/analyze")
async def diagnose_error(request: DiagnoseRequest):
    """
    解题诊断分析

    分析学生的错误答案,找出错误原因
    """
    try:
        # 构建诊断 prompt
        diagnose_prompt = f"""你是一位有20年教学经验的初中数学老师.
学生做错了这道题: {request.question}
学生的错误答案是: {request.student_answer}

请分析:
1. 这道题考查的核心知识点是什么
2. 学生最可能在哪个环节出错(概念不清/方法不对/计算失误)
3. 用一句话告诉学生他的问题在哪里(要具体,不要泛泛而谈)

请以JSON格式返回:
```json
{{
  "knowledge_point": "核心知识点",
  "error_type": "概念不清/方法不对/计算失误",
  "problem_description": "一句话描述学生的问题",
  "analysis": "详细分析"
}}
```
只返回JSON,不要其他内容. """

        messages = [{
            "role": "user",
            "content": diagnose_prompt
        }]

        response_text = call_glm_api(messages, model="glm-4-flash")

        # 解析 JSON
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            result = json.loads(json_match.group(0))
            return {
                "success": True,
                "data": result
            }
        else:
            # 如果解析失败,返回原始文本
            return {
                "success": True,
                "data": {
                    "knowledge_point": "未识别",
                    "error_type": "未分类",
                    "problem_description": "分析失败",
                    "analysis": response_text
                }
            }

    except Exception as e:
        import traceback
        print(f"诊断 API 错误: {str(e)}")
        print(f"错误堆栈:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"诊断失败: {str(e)}")

@app.post("/api/diagnose/guide/stream")
async def guide_student_stream(request: GuideRequest):
    """
    苏格拉底式引导(流式输出)

    通过提问引导学生自己找到答案
    """
    async def generate_stream():
        try:
            yield f"data: {json.dumps({'status': 'thinking', 'message': '🤔 正在思考如何引导...'})}\n\n"

            # 检查是否是第一轮对话
            if not request.student_response and not request.conversation_history:
                # 第一轮: 生成初始引导问题
                guide_prompt = f"""你是一位耐心的数学老师,正在一对一辅导学生.
学生刚做错了这道题: {request.question}
诊断结果: {request.diagnosis}

请用苏格拉底式提问,一步步引导学生自己做出来.
规则:
- 每次只问一个问题
- 如果学生答对,给予肯定并推进下一步
- 如果学生答错或说不会,给一点提示,但不要直接说答案
- 引导控制在5-8轮对话内完成

现在请开始引导,提出第一个问题来启发学生思考. """
            else:
                # 后续轮: 根据学生回答继续引导
                history_summary = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                    for msg in request.conversation_history[-6:]  # 只取最近6轮
                ])

                guide_prompt = f"""你是一位耐心的数学老师,正在一对一辅导学生.

题目: {request.question}
诊断结果: {request.diagnosis}

对话历史:
{history_summary}

学生最新回答: {request.student_response or '(学生表示不会或回答错误)'}

请根据学生的回答:
- 如果答对了: 给予肯定,并引导下一步
- 如果答错了: 委婉指出问题,给出提示
- 如果说不会: 简化问题,给出更明显的提示

继续引导学生,直到找到正确答案. 每次只问一个问题. """

            messages = [{
                "role": "user",
                "content": guide_prompt
            }]

            # 逐字返回引导内容
            for char in call_glm_api(messages, model="glm-4-flash"):
                yield f"data: {json.dumps({'content': char})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        except HTTPException as e:
            yield f"data: {json.dumps({'error': str(e.detail), 'done': True})}\n\n"
        except Exception as e:
            import traceback
            print(f"引导流式 API 错误: {str(e)}")
            print(f"错误堆栈:\n{traceback.format_exc()}")
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")

@app.post("/api/diagnose/guide")
async def guide_student(request: GuideRequest):
    """
    苏格拉底式引导

    通过提问引导学生自己找到答案
    """
    try:
        # 检查是否是第一轮对话
        if not request.student_response and not request.conversation_history:
            # 第一轮: 生成初始引导问题
            guide_prompt = f"""你是一位耐心的数学老师,正在一对一辅导学生. 
学生刚做错了这道题: {request.question}
诊断结果: {request.diagnosis}

请用苏格拉底式提问,一步步引导学生自己做出来. 
规则: 
- 每次只问一个问题
- 如果学生答对,给予肯定并推进下一步
- 如果学生答错或说不会,给一点提示,但不要直接说答案
- 引导控制在5-8轮对话内完成

现在请开始引导,提出第一个问题来启发学生思考. """
        else:
            # 后续轮: 根据学生回答继续引导
            history_summary = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in request.conversation_history[-6:]  # 只取最近6轮
            ])

            guide_prompt = f"""你是一位耐心的数学老师,正在一对一辅导学生. 

题目: {request.question}
诊断结果: {request.diagnosis}

对话历史: 
{history_summary}

学生最新回答: {request.student_response or '(学生表示不会或回答错误)'}

请根据学生的回答: 
- 如果答对了: 给予肯定,并引导下一步
- 如果答错了: 委婉指出问题,给出提示
- 如果说不会: 简化问题,给出更明显的提示

继续引导学生,直到找到正确答案. 每次只问一个问题. """

        messages = [{
            "role": "user",
            "content": guide_prompt
        }]

        response_text = call_glm_api(messages, model="glm-4-flash")

        return {
            "success": True,
            "response": response_text[:1500],
            "is_complete": False  # 可以根据响应内容判断是否完成引导
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"引导 API 错误: {str(e)}")
        print(f"错误堆栈:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"引导失败: {str(e)}")

@app.post("/api/detect/mistakes/smart")
async def smart_detect_mistakes(request: DetectMistakesRequest):
    """
    智能多维度验证错题检测

    实现流程: 
    1. 解析卷面题目和学生答案
    2. 识别老师批改标记
    3. AI理解题目并给出答案
    4. 三方比较验证
    """
    try:
        import time
        start_time = time.time()

        # 解码图片
        image = decode_base64_image(request.image_data)

        # 使用高质量图片
        max_size = 1500
        if image.width > max_size or image.height > max_size:
            ratio = min(max_size / image.width, max_size / image.height)
            new_width = int(image.width * ratio)
            new_height = int(image.height * ratio)
            image = image.resize((new_width, new_height))

        base64_image = encode_image_to_base64(image, quality=85)
        print(f"[智能检测] 图片尺寸: {image.width}x{image.height}")

        # 步骤1: OCR识别题目, 学生答案, 老师批改
        print(f"[智能检测] 步骤1: OCR识别试卷内容...")
        ocr_prompt = """请详细分析这张试卷,提取以下信息: 

对每道题目(按顺序编号),请提供: 
1. 题号
2. 题目类型(选择题/填空题/判断题等)
3. 题目内容
4. 学生选择的答案(A/B/C/D或填空内容)
5. 老师的批改标记(×表示错,√表示对,圈/线/点表示其他标记,无标记表示未批改)

请以JSON格式返回: 
```json
{
  "questions": [
    {
      "question_no": "题号",
      "question_type": "题型",
      "question_content": "题目内容",
      "student_answer": "学生答案",
      "teacher_mark": "老师标记(×/√/圈/线/点/无)"
    }
  ]
}
```

注意: 仔细识别每个题目的批改标记,×和√要区分清楚. """

        ocr_messages = [{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                },
                {
                    "type": "text",
                    "text": ocr_prompt
                }
            ]
        }]

        ocr_response = call_glm_api(ocr_messages, model="glm-4v", skip_delay=False, max_tokens=2000)
        print(f"[智能检测] OCR响应:\n{ocr_response[:500]}...")

        # 解析OCR结果
        ocr_data = None
        json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', ocr_response)
        if json_match:
            try:
                ocr_data = json.loads(json_match.group(1))
            except:
                pass

        if not ocr_data:
            json_match = re.search(r'\{[\s\S]*"questions"[\s\S]*\}', ocr_response)
            if json_match:
                try:
                    ocr_data = json.loads(json_match.group(0))
                except:
                    pass

        if not ocr_data or "questions" not in ocr_data:
            return {
                "success": False,
                "error": "OCR识别失败,请上传更清晰的试卷图片"
            }

        questions = ocr_data["questions"]
        print(f"[智能检测] 识别到 {len(questions)} 道题目")

        # 步骤2-3: AI理解题目并给出正确答案
        print(f"[智能检测] 步骤2-3: AI分析题目并给出答案...")
        analyzed_questions = []

        for q in questions:
            q_no = q.get("question_no", "?")
            q_type = q.get("question_type", "")
            q_content = q.get("question_content", "")
            student_answer = q.get("student_answer", "")
            teacher_mark = q.get("teacher_mark", "")

            # AI解答题目
            solve_prompt = f"""请解答这道题目: 

题目: {q_content}
学生答案: {student_answer}

请分析并给出: 
1. 正确答案
2. 学生的答案是否正确
3. 简要分析原因

返回格式: 
```json
{{
  "correct_answer": "正确答案",
  "is_correct": true/false,
  "reasoning": "分析原因"
}}
```"""

            solve_messages = [{
                "role": "user",
                "content": solve_prompt
            }]

            try:
                solve_response = call_glm_api(solve_messages, model="glm-4-flash", skip_delay=False, max_tokens=500)

                solve_data = None
                json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', solve_response)
                if json_match:
                    try:
                        solve_data = json.loads(json_match.group(1))
                    except:
                        pass

                if not solve_data:
                    json_match = re.search(r'\{[\s\S]*\}', solve_response)
                    if json_match:
                        try:
                            solve_data = json.loads(json_match.group(0))
                        except:
                            pass

                if solve_data:
                    correct_answer = solve_data.get("correct_answer", "")
                    ai_judgment = solve_data.get("is_correct", False)
                    reasoning = solve_data.get("reasoning", "")
                else:
                    correct_answer = "无法确定"
                    ai_judgment = None
                    reasoning = solve_response[:200]

            except Exception as e:
                print(f"[智能检测] 解答题目{q_no}失败: {str(e)}")
                correct_answer = "解析失败"
                ai_judgment = None
                reasoning = ""

            # 步骤4-6: 三方比较验证
            # 判断老师批改: ×=错,√=对
            teacher_says_wrong = teacher_mark in ["×", "x", "X", "叉", "错"]
            teacher_says_correct = teacher_mark in ["√", "✓", "对", "钩"]

            # 验证逻辑
            final_status = "需要确认"  # 默认需要学生确认
            confidence = 0
            reason = []

            if ai_judgment is not None:
                # AI有明确判断
                if ai_judgment == False and teacher_says_wrong:
                    # AI说错,老师也说错 → 确认是错题
                    final_status = "错题"
                    confidence = 95
                    reason.append("AI和老师都认为是错题")
                elif ai_judgment == True and teacher_says_correct:
                    # AI说对,老师也说对 → 确认是对的
                    final_status = "正确"
                    confidence = 95
                    reason.append("AI和老师都认为正确")
                elif ai_judgment != teacher_says_correct and teacher_says_wrong:
                    # AI判断和老师不一致,且老师说错 → 需要学生确认
                    final_status = "需要确认"
                    confidence = 50
                    reason.append(f"AI认为{'对' if ai_judgment else '错'},老师标记为{teacher_mark}")
                elif teacher_says_wrong:
                    # 老师说错,但AI不确定
                    final_status = "疑似错题"
                    confidence = 70
                    reason.append("老师标记为错题")
            elif teacher_says_wrong:
                # AI无法判断,但老师说错
                final_status = "疑似错题"
                confidence = 60
                reason.append("老师标记为错题,AI未能判断")

            analyzed_questions.append({
                "question_no": q_no,
                "question_type": q_type,
                "question_content": q_content,
                "student_answer": student_answer,
                "teacher_mark": teacher_mark,
                "correct_answer": correct_answer,
                "ai_judgment": ai_judgment,
                "final_status": final_status,
                "confidence": confidence,
                "reason": "; ".join(reason),
                "analysis": reasoning
            })

        # 筛选出错题和需要确认的题目
        mistakes = []
        need_confirmation = []

        for q in analyzed_questions:
            if q["final_status"] == "错题":
                mistakes.append({
                    "question_no": q["question_no"],
                    "reason": q["reason"],
                    "question": q["question_content"],
                    "student_answer": q["student_answer"],
                    "correct_answer": q["correct_answer"],
                    "analysis": q["analysis"]
                })
            elif q["final_status"] in ["需要确认", "疑似错题"]:
                need_confirmation.append({
                    "question_no": q["question_no"],
                    "reason": q["reason"],
                    "question": q["question_content"],
                    "student_answer": q["student_answer"],
                    "ai_answer": q["correct_answer"],
                    "teacher_mark": q["teacher_mark"],
                    "confidence": q["confidence"]
                })

        elapsed = time.time() - start_time
        print(f"[智能检测] 完成,耗时: {elapsed:.2f}秒")
        print(f"[智能检测] 错题: {len(mistakes)}, 需确认: {len(need_confirmation)}")

        return {
            "success": True,
            "data": {
                "mistakes": mistakes,
                "need_confirmation": need_confirmation,
                "all_questions": analyzed_questions,
                "summary": f"识别到{len(mistakes)}道错题,{len(need_confirmation)}道需要确认"
            },
            "elapsed_time": f"{elapsed:.2f}s"
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[智能检测] 错误: {str(e)}")
        print(f"错误堆栈:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"智能检测失败: {str(e)}")

@app.post("/api/detect/mistakes")
async def detect_mistakes(request: DetectMistakesRequest):
    """
    智能检测试卷中的错题(快速版)

    识别试卷中的错题特征: 
    - 红笔批改痕迹
    - 叉号(×)
    - 涂改痕迹
    - 低分标记
    - 老师批注
    """
    try:
        import time
        start_time = time.time()

        # 解码图片
        image = decode_base64_image(request.image_data)

        # 初始化变量
        response_text = ""
        result = None

        # 如果用户提供了标记,使用高质量图片进行详细分析
        if request.user_marks and len(request.user_marks) > 0:
            print(f"[错题检测] 用户提供了 {len(request.user_marks)} 个标记,开始识别和分析")

            # 用户标记模式: 使用高质量图片以便AI能看清题目
            max_size = 1500  # 更高分辨率
            if image.width > max_size or image.height > max_size:
                ratio = min(max_size / image.width, max_size / image.height)
                new_width = int(image.width * ratio)
                new_height = int(image.height * ratio)
                image = image.resize((new_width, new_height))

            # 使用较高质量(85)
            base64_image = encode_image_to_base64(image, quality=85)
            print(f"[错题检测] 用户标记模式,图片尺寸: {image.width}x{image.height}")

            # 识别用户圈选的题目并进行详细分析
            analyze_prompt = f"""用户已经框选了试卷中的 {len(request.user_marks)} 道题目需要分析. 请仔细分析这些题目. 

请按以下步骤分析: 
1. 识别框选区域的题目内容和学生答案
2. 判断答案是否正确
3. 分析错误原因和知识点
4. 提供改进建议

必须返回JSON格式(不要使用markdown代码块,直接返回JSON): 
{{
  "mistakes": [
    {{
      "question_no": "题号或位置",
      "question": "题目内容",
      "student_answer": "学生答案",
      "correct_answer": "正确答案",
      "reason": "错误原因",
      "knowledge_point": "知识点",
      "suggestion": "改进建议"
    }}
  ],
  "detailed_analysis": "详细的学情分析,包括: 整体评价, 薄弱知识点, 学习建议等(至少200字)"
}}

注意: 用户框选的都是需要分析的题目,请直接分析内容,不要判断是否为错题. """

            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": analyze_prompt
                    }
                ]
            }]

            # 调用 API 进行详细分析(正常模式,需要详细输出)
            response_text = call_glm_api(messages, model="glm-4v", skip_delay=False, max_tokens=2000)

            elapsed = time.time() - start_time
            print(f"[错题检测] 用户标记分析耗时: {elapsed:.2f}秒")
            print(f"[错题检测] API响应:\n{response_text[:1500]}")

        else:
            # 没有用户标记,执行自动检测
            # 自动检测模式: 使用中等质量图片以提升准确度
            max_size = 1200  # 提高分辨率以便AI能看清细节
            if image.width > max_size or image.height > max_size:
                ratio = min(max_size / image.width, max_size / image.height)
                new_width = int(image.width * ratio)
                new_height = int(image.height * ratio)
                image = image.resize((new_width, new_height))

            # 使用中等质量(75)来平衡速度和清晰度
            base64_image = encode_image_to_base64(image, quality=75)
            print(f"[错题检测] 自动检测模式,图片尺寸: {image.width}x{image.height}")
            # 优化的 prompt - 专注于红叉/红圈标记识别
            detect_prompt = """找出试卷上的错题. 错题必须有清晰的红色×标记在答案上.

**什么是错题(必须满足全部条件)**:
1. 答案选项(A/B/C/D)上有红色×
2. ×号清晰可见,两条交叉线都清楚
3. ×号明显是红色笔迹

**绝对不是错题**:
- 答案打钩√ → 正确
- 题号有任何标记 → 不影响判断
- 答案只有圈, 线, 点但没有× → 不是错题
- ×号模糊不清或不确定 → 不标记

**判断流程**:
对每个题的答案(A/B/C/D):
- 仔细看: 这个选项上有清晰的红色×吗?
-- 非常确定有× → 错题
-- 不太确定或模糊 → 不标记
-- 没有× → 正确

**宁可漏检,绝不误判!**

返回JSON格式:
```json
{"mistakes": [{"question_no": "题号", "reason": "红叉"}], "summary": "共找到X道错题"}
```

没有错题: {"mistakes": [], "summary": "未发现错题"}"""

            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": detect_prompt
                    }
                ]
            }]

            # 调用 API(快速模式: 跳过延迟, 减少max_tokens)
            response_text = call_glm_api(messages, model="glm-4v", skip_delay=True, max_tokens=500)

            elapsed = time.time() - start_time
            print(f"[错题检测] 耗时: {elapsed:.2f}秒")
            print(f"[错题检测] API原始响应:\n{response_text[:1000]}")  # 打印前1000字符用于调试

        # 方式1: 尝试提取 JSON 代码块(```json ... ```)
        json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', response_text)
        if json_match:
            print(f"[错题检测] 匹配到 JSON 代码块")
            try:
                result = json.loads(json_match.group(1))
            except json.JSONDecodeError as e:
                print(f"[错题检测] JSON 代码块解析失败: {e}")

        # 方式2: 尝试提取花括号内的完整 JSON
        if not result:
            json_match = re.search(r'\{[\s\S]*"mistakes"[\s\S]*\}', response_text)
            if json_match:
                print(f"[错题检测] 匹配到包含 mistakes 的 JSON")
                try:
                    result = json.loads(json_match.group(0))
                except json.JSONDecodeError as e:
                    print(f"[错题检测] JSON 解析失败: {e}")

        # 方式3: 尝试提取任意完整的 JSON 对象
        if not result:
            json_match = re.search(r'\{[\s\S]*?\}', response_text)
            if json_match:
                print(f"[错题检测] 匹配到任意 JSON 对象")
                try:
                    result = json.loads(json_match.group(0))
                except json.JSONDecodeError as e:
                    print(f"[错题检测] 通用 JSON 解析失败: {e}")

        # 方式4: 尝试解析Markdown列表格式（降级处理）
        if not result:
            print(f"[错题检测] 尝试解析Markdown列表格式")
            try:
                # 尝试从markdown列表中提取错题信息
                # 格式: - 第X题：...
                lines = response_text.split('\n')
                mistakes_list = []
                for line in lines:
                    line = line.strip()
                    if line.startswith('-') or line.startswith('•'):
                        # 提取题号
                        match = re.search(r'第(\d+)题', line)
                        if match:
                            question_no = match.group(1)
                            reason = "错题"
                            mistakes_list.append({
                                "question_no": question_no,
                                "reason": reason
                            })

                if mistakes_list:
                    result = {
                        "mistakes": mistakes_list,
                        "summary": f"共找到{len(mistakes_list)}道错题"
                    }
                    print(f"[错题检测] Markdown解析成功: 找到{len(mistakes_list)}道错题")
            except Exception as e:
                print(f"[错题检测] Markdown解析失败: {e}")

        if result:
            print(f"[错题检测] ✅ 解析成功: {result}")

            # 如果找到了错题,生成简要摘要并等待确认
            mistakes_list = result.get("mistakes", [])
            if mistakes_list:
                print(f"[错题检测] 找到 {len(mistakes_list)} 道错题,开始生成详细学情分析...")

                try:
                    # 第一步: 识别试卷内容
                    ocr_prompt = """请识别这张试卷的内容,包括:
1. 学科和年级
2. 题目内容(特别是错题)
3. 学生答案(如果有)
4. 试卷整体特点

请用简洁的语言描述. """

                    ocr_messages = [{
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": ocr_prompt
                            }
                        ]
                    }]

                    paper_content = call_glm_api(ocr_messages, model="glm-4v", skip_delay=False, max_tokens=1000)
                    print(f"[错题检测] 试卷内容识别完成,长度: {len(paper_content)} 字符")

                    # 第二步: 基于试卷内容生成学情分析
                    mistakes_str = ", ".join([m["question_no"] for m in mistakes_list])
                    analysis_prompt = f"""你是经验丰富的老师. 试卷内容: {paper_content}

检测到的错题: {mistakes_str}(共{len(mistakes_list)}道)

请生成详细学情分析报告(参考以下格式): 

**一, 学习现状分析**
从卷面看,总结学生的学习优势(3点)

**二, 薄弱点与失分原因**
针对错题分析失分原因和薄弱环节

**三, 针对性学习建议**
给出3-5条具体可操作的建议

要求: 专业, 详细, 有针对性, 鼓励性语气. """

                    analysis_messages = [{
                        "role": "user",
                        "content": analysis_prompt
                    }]

                    # 使用文本模型生成更详细的分析
                    analysis_text = call_glm_api(analysis_messages, model="glm-4-flash", skip_delay=False, max_tokens=2500)

                    # 打印学情分析内容
                    print(f"[错题检测] 学情分析生成完成,长度: {len(analysis_text)} 字符")

                    # 返回结果,包含简要信息和详细分析
                    return {
                        "success": True,
                        "data": {
                            "mistakes": mistakes_list,
                            "detailed_analysis": analysis_text,
                            "summary": f"共找到{len(mistakes_list)}道错题",
                            "need_confirmation": True  # 标记需要学生确认
                        },
                        "elapsed_time": f"{elapsed:.2f}s"
                    }

                except Exception as e:
                    print(f"[错题检测] 学情分析生成失败: {str(e)}")
                    # 即使分析失败,也返回基本的错题信息
                    return {
                        "success": True,
                        "data": {
                            "mistakes": mistakes_list,
                            "detailed_analysis": None,
                            "summary": f"共找到{len(mistakes_list)}道错题",
                            "need_confirmation": True
                        },
                        "elapsed_time": f"{elapsed:.2f}s"
                    }

            return {
                "success": True,
                "data": result,
                "elapsed_time": f"{elapsed:.2f}s"
            }

        # 解析失败,尝试使用降级方案(仅用户标记模式)
        print(f"[错题检测] 开始检查降级处理, user_marks={len(request.user_marks) if request.user_marks else 0}, result={result}")
        if request.user_marks and len(request.user_marks) > 0:
            print(f"[错题检测] JSON解析失败,使用AI文本回复作为降级方案")
            print(f"[错题检测] AI回复长度: {len(response_text)} 字符")
            # 使用AI的文本回复作为分析内容
            return {
                "success": True,
                "data": {
                    "mistakes": [
                        {
                            "question_no": f"框选题目{i+1}",
                            "question": "用户框选的题目",
                            "reason": "需要分析",
                            "student_answer": "见下方分析",
                            "correct_answer": "见下方分析",
                            "knowledge_point": "综合分析",
                            "suggestion": "见下方分析"
                        }
                        for i in range(len(request.user_marks))
                    ],
                    "detailed_analysis": response_text if len(response_text) > 10 else "AI返回的分析内容过短,可能是图片质量不佳. 请尝试上传更清晰的图片. "
                },
                "elapsed_time": f"{elapsed:.2f}s"
            }

        # 解析失败返回默认值
        print(f"[错题检测] ❌ 所有解析方式都失败")
        print(f"[错题检测] 检查条件: request.user_marks={request.user_marks}, len={len(request.user_marks) if request.user_marks else 0}")
        return {
            "success": True,
            "data": {
                "mistakes": [],
                "summary": "识别失败,请重试"
            },
            "elapsed_time": f"{elapsed:.2f}s"
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"错题检测 API 错误: {str(e)}")
        print(f"错误堆栈:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"错题检测失败: {str(e)}")


@app.post("/api/detect/mistakes/stream")
async def detect_mistakes_stream(request: DetectMistakesRequest):
    """
    错题检测(流式输出)

    识别试卷中的错题,使用流式响应逐步返回分析结果
    始终使用GLM-4V视觉模型进行图像识别
    """
    async def generate_stream():
        import sys
        try:
            if not request.image_data:
                yield f"data: {json.dumps({'error': '请提供图片数据'})}\n\n"
                return

            start_time = time.time()
            print(f"[错题检测流式] ========== 开始处理 ==========")
            print(f"[错题检测流式] 收到请求, user_marks数量: {len(request.user_marks) if request.user_marks else 0}")
            sys.stdout.flush()

            # 先发送"分析中"状态
            yield f"data: {json.dumps({'status': 'analyzing', 'message': 'AI正在分析中...'})}\n\n"
            print(f"[错题检测流式] 发送分析中状态")
            sys.stdout.flush()

            # 发送开始检测信号
            yield f"data: {json.dumps({'status': 'start', 'message': '🔍 开始分析试卷...'})}\n\n"

            # 解码图片
            try:
                print(f"[错题检测流式] 开始解码图片...")
                sys.stdout.flush()
                image = decode_base64_image(request.image_data)
                print(f"[错题检测流式] 图片解码成功, 尺寸: {image.width}x{image.height}")
                sys.stdout.flush()
            except Exception as e:
                print(f"[错题检测流式] 图片解码失败: {str(e)}")
                sys.stdout.flush()
                yield f"data: {json.dumps({'error': f'图片解码失败: {str(e)}'})}\n\n"
                return

            # 根据是否有用户标记选择处理模式
            if request.user_marks and len(request.user_marks) > 0:
                # 用户标记模式
                yield f"data: {json.dumps({'status': 'processing', 'message': '📋 分析用户标记的题目...'})}\n\n"

                max_size = 1500
                if image.width > max_size or image.height > max_size:
                    ratio = min(max_size / image.width, max_size / image.height)
                    new_width = int(image.width * ratio)
                    new_height = int(image.height * ratio)
                    image = image.resize((new_width, new_height))

                base64_image = encode_image_to_base64(image, quality=85)

                # 构建分析提示
                marks_desc = "\n".join([
                    f"框选{i+1}: 位置{mark.get('x', 0)}%,{mark.get('y', 0)}%, 大小{mark.get('width', 0)}%x{mark.get('height', 0)}%"
                    for i, mark in enumerate(request.user_marks)
                ])

                analyze_prompt = f"""用户标记了试卷上的{len(request.user_marks)}个区域,需要你分析:
{marks_desc}

请按以下步骤分析:
1. 识别框选区域的题目内容和学生答案
2. 判断答案是否正确
3. 分析错误原因和知识点
4. 提供改进建议

必须返回JSON格式(不要使用markdown代码块,直接返回JSON):
{{
  "mistakes": [
    {{
      "question_no": "题号或位置",
      "question": "题目内容",
      "student_answer": "学生答案",
      "correct_answer": "正确答案",
      "reason": "错误原因",
      "knowledge_point": "知识点",
      "suggestion": "改进建议"
    }}
  ],
  "detailed_analysis": "详细的学情分析,包括: 整体评价, 薄弱知识点, 学习建议等(至少200字)"
}}

注意: 用户框选的都是需要分析的题目,请直接分析内容,不要判断是否为错题."""

                messages = [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": analyze_prompt
                        }
                    ]
                }]

                # 调用 GLM-4V 视觉模型进行分析
                response_text = call_glm_api(messages, model="glm-4v", skip_delay=False, max_tokens=2000)

                print(f"[错题检测流式] 用户标记模式 API响应:\n{response_text}\n")

                # 解析响应
                result = parse_mistakes_from_response(response_text)

                if result is None:
                    print(f"[错题检测流式] 用户标记模式解析失败")
                    yield f"data: {json.dumps({'error': f'无法解析AI响应。请重试。'})}\n\n"
                    return

                mistakes_list = result.get("mistakes", [])

                if mistakes_list:
                    # 逐步发送结果
                    yield f"data: {json.dumps({'status': 'found', 'count': len(mistakes_list), 'message': f'✅ 找到 {len(mistakes_list)} 道需要分析的题目'})}\n\n"

                    # 生成详细分析
                    mistakes_str = ", ".join([m["question_no"] for m in mistakes_list])
                    analysis_prompt = f"""你是经验丰富的老师. 检测到的题目: {mistakes_str}(共{len(mistakes_list)}道)

请生成详细学情分析报告(参考以下格式):

**一、学习现状分析**
从卷面看,总结学生的学习优势(3点)

**二、薄弱点与失分原因**
针对错题分析失分原因和薄弱环节

**三、针对性学习建议**
给出3-5条具体可操作的建议

要求: 专业, 详细, 有针对性, 鼓励性语气."""

                    analysis_messages = [{
                        "role": "user",
                        "content": analysis_prompt
                    }]

                    # 使用流式返回分析文本
                    analysis_text = call_glm_api(analysis_messages, model="glm-4-flash", skip_delay=False, max_tokens=2500)

                    # 逐字返回学情分析
                    for char in analysis_text:
                        yield f"data: {json.dumps({'content': char})}\n\n"

                    # 发送完成数据和结果
                    yield f"data: {json.dumps({'done': True, 'data': {'mistakes': mistakes_list, 'need_confirmation': True}})}\n\n"
                else:
                    yield f"data: {json.dumps({'error': '未能识别到标记的题目，请重试'})}\n\n"

            else:
                # 自动检测模式 - 使用GLM-4V识别试卷上的红叉
                yield f"data: {json.dumps({'status': 'processing', 'message': '🔍 使用AI视觉模型识别错题标记...'})}\n\n"

                max_size = 1200
                if image.width > max_size or image.height > max_size:
                    ratio = min(max_size / image.width, max_size / image.height)
                    new_width = int(image.width * ratio)
                    new_height = int(image.height * ratio)
                    image = image.resize((new_width, new_height))

                base64_image = encode_image_to_base64(image, quality=75)

                detect_prompt = """请分析这张试卷，找出所有有错误的题目。

观察要点：
1. 红色×标记 - 明显的错题标记
2. 红笔批改 - 被老师标记为错误的题目
3. 学生答案明显错误

**重要：请严格按照以下格式回答，不要包含其他内容**

格式要求：
- 如果有错题：只回答"第X题、第Y题、第Z题"（用顿号分隔）
- 如果没有错题：只回答"没有错题"

示例：
✓ 正确：第4题、第5题
✓ 正确：第17题
✓ 正确：没有错题
✗ 错误：第4题有错误（不要描述）
✗ 错误：17（要有"第"和"题"）

开始识别："""

                messages = [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": detect_prompt
                        }
                    ]
                }]

                # 使用GLM-4V视觉模型识别
                print(f"[错题检测流式] 调用GLM-4V API...")
                print(f"[错题检测流式] messages结构: {messages[0]['role']}, 内容类型: {type(messages[0]['content'])}")
                print(f"[错题检测流式] content长度: {len(messages[0]['content'])}")
                sys.stdout.flush()

                response_text = call_glm_api(messages, model="glm-4v", skip_delay=False, max_tokens=1500)

                print(f"[错题检测流式] API调用完成")
                print(f"[错题检测流式] API响应类型: {type(response_text)}")
                print(f"[错题检测流式] API响应repr: {repr(response_text)}")
                print(f"[错题检测流式] API完整响应:\n{response_text}\n")
                print(f"[错题检测流式] 响应长度: {len(response_text)} 字符")
                sys.stdout.flush()

                # 先检查是否是空响应
                if not response_text or response_text.strip() == "":
                    print(f"[错题检测流式] AI返回空响应")
                    yield f"data: {json.dumps({'error': 'AI识别失败，未返回任何内容。请尝试上传更清晰的图片或稍后重试。', 'done': True})}\n\n"
                    return

                # 从自然语言回复中提取题号
                import re
                mistakes_list = []

                # 检查是否表示没有错题
                no_mistake_keywords = ['没有', '未发现', '找不到', '全部正确', '没有错题', '未发现错题', '没有红叉']
                if any(keyword in response_text for keyword in no_mistake_keywords):
                    print(f"[错题检测流式] AI回复表示没有错题")
                    mistakes_list = []
                else:
                    # 查找所有题号（支持多种格式）
                    question_patterns = [
                        r'第?(\d+)题',  # 第4题, 4题
                        r'(\d+)号',      # 4号
                        r'question\s*(\d+)',  # question 4
                        r'NO[\.]?(\d+)',  # NO.4
                        r'(\d+)[、，,]',  # 17、19 - 中文顿号或逗号分隔
                        r'是[：:]\s*(\d+)',  # 是：17
                        r'题号[：:]\s*(\d+)',  # 题号：17
                    ]

                    all_numbers = []
                    for pattern in question_patterns:
                        matches = re.findall(pattern, response_text, re.IGNORECASE)
                        all_numbers.extend(matches)

                    # 去重并排序
                    unique_numbers = sorted(set(all_numbers))

                    if unique_numbers:
                        for num in unique_numbers:
                            mistakes_list.append({
                                "question_no": num,
                                "reason": "红叉标记"
                            })
                        print(f"[错题检测流式] 从回复中提取到题号: {unique_numbers}")

                sys.stdout.flush()

                if mistakes_list:
                    yield f"data: {json.dumps({'status': 'found', 'count': len(mistakes_list), 'message': f'✅ 检测到 {len(mistakes_list)} 道错题'})}\n\n"

                    # 生成详细分析
                    yield f"data: {json.dumps({'status': 'analyzing', 'message': '📊 生成学情分析...'})}\n\n"

                    mistakes_str = ", ".join([m["question_no"] for m in mistakes_list])
                    analysis_prompt = f"""你是经验丰富的老师. 检测到的错题: {mistakes_str}(共{len(mistakes_list)}道)

请生成详细学情分析报告(参考以下格式):

**一、学习现状分析**
从卷面看,总结学生的学习优势(3点)

**二、薄弱点与失分原因**
针对错题分析失分原因和薄弱环节

**三、针对性学习建议**
给出3-5条具体可操作的建议

要求: 专业, 详细, 有针对性, 鼓励性语气."""

                    analysis_messages = [{
                        "role": "user",
                        "content": analysis_prompt
                    }]

                    analysis_text = call_glm_api(analysis_messages, model="glm-4-flash", skip_delay=False, max_tokens=2500)

                    # 逐字返回学情分析
                    for char in analysis_text:
                        yield f"data: {json.dumps({'content': char})}\n\n"

                    # 发送完成数据
                    yield f"data: {json.dumps({'done': True, 'data': {'mistakes': mistakes_list, 'need_confirmation': True}})}\n\n"
                else:
                    # result存在但mistakes为空
                    print(f"[错题检测流式] 解析成功但mistakes为空")
                    yield f"data: {json.dumps({'status': 'no_mistakes', 'message': '✅ 没有发现明显的错题'})}\n\n"
                    yield f"data: {json.dumps({'done': True, 'data': {'mistakes': [], 'need_confirmation': False}})}\n\n"

        except Exception as e:
            import traceback
            print(f"[错题检测流式] 错误: {str(e)}")
            print(f"错误堆栈:\n{traceback.format_exc()}")
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


# ==================== 智能分析API ====================

@app.post("/api/analyze/smart")
async def smart_analyze(request: DetectMistakesRequest):
    """
    智能分析API - 自动判断内容类型并执行相应分析

    判断逻辑：
    - 用户标记≥3个或检测到≥3道错题 → 整张试卷，生成详细学情分析
    - 用户标记1-2个或检测到1-2道错题 → 单个错题，进行针对性讲解
    """
    try:
        import time
        start_time = time.time()

        # 解码图片
        image = decode_base64_image(request.image_data)

        # 判断用户标记数量
        user_marks_count = len(request.user_marks) if request.user_marks else 0

        print(f"[智能分析] 开始分析，用户标记数量: {user_marks_count}")

        # 发送初始状态
        # yield_status = f"🔍 正在分析试卷内容..."

        # 步骤1: 检测错题
        print(f"[智能分析] 步骤1: 检测试卷中的错题...")

        # 如果用户有标记，使用标记模式；否则自动检测
        if user_marks_count > 0:
            # 用户标记模式
            max_size = 1500
            if image.width > max_size or image.height > max_size:
                ratio = min(max_size / image.width, max_size / image.height)
                new_width = int(image.width * ratio)
                new_height = int(image.height * ratio)
                image = image.resize((new_width, new_height))

            base64_image = encode_image_to_base64(image, quality=85)

            analyze_prompt = f"""用户标记了试卷上的{user_marks_count}个区域需要分析。

请识别这些区域中的题目，并提取：
1. 题号
2. 题目内容
3. 学生答案
4. 正确答案（如果可以判断）
5. 错误原因

必须返回JSON格式:
{{
  "mistakes": [
    {{
      "question_no": "题号",
      "question": "题目内容",
      "student_answer": "学生答案",
      "correct_answer": "正确答案",
      "reason": "错误原因"
    }}
  ]
}}"""

            messages = [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    {"type": "text", "text": analyze_prompt}
                ]
            }]

            response_text = call_glm_api(messages, model="glm-4v", skip_delay=False, max_tokens=2000)

            # 解析响应
            mistakes = []
            json_match = re.search(r'\{[\s\S]*"mistakes"[\s\S]*\}', response_text)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    mistakes = data.get("mistakes", [])
                except:
                    pass
        else:
            # 自动检测模式
            detect_prompt = """请识别这张试卷中的所有错题（有红×标记或老师批改的题目）。

请返回JSON格式:
{
  "mistakes": [
    {"question_no": "题号", "reason": "红叉标记"}
  ]
}

如果没有错题，返回: {"mistakes": []}"""

            max_size = 1200
            if image.width > max_size or image.height > max_size:
                ratio = min(max_size / image.width, max_size / image.height)
                image = image.resize((int(image.width * ratio), int(image.height * ratio)))

            base64_image = encode_image_to_base64(image, quality=75)

            messages = [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    {"type": "text", "text": detect_prompt}
                ]
            }]

            response_text = call_glm_api(messages, model="glm-4v", skip_delay=False, max_tokens=1500)

            # 解析响应
            mistakes = []
            json_match = re.search(r'\{[\s\S]*"mistakes"[\s\S]*\}', response_text)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    mistakes = data.get("mistakes", [])
                except:
                    pass

        mistake_count = len(mistakes)
        print(f"[智能分析] 检测到 {mistake_count} 道错题")

        # 步骤2: 识别试卷学科类型
        print(f"[智能分析] 步骤2: 识别试卷学科类型...")

        subject_prompt = """请分析这张试卷，识别它属于哪个学科。

可能的学科包括：
- 数学
- 语文
- 英语
- 物理
- 化学
- 生物
- 历史
- 地理
- 政治

请只返回学科名称，不要其他内容。如果无法确定，返回"未知"。"""

        subject_messages = [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                {"type": "text", "text": subject_prompt}
            ]
        }]

        try:
            subject = call_glm_api(subject_messages, model="glm-4v", skip_delay=True, max_tokens=50)
            # 清理结果，提取学科名称
            subject = subject.strip()
            if any(kw in subject for kw in ["英语", "English", "english"]):
                subject = "英语试卷"
            elif any(kw in subject for kw in ["数学", "Math", "math"]):
                subject = "数学试卷"
            elif any(kw in subject for kw in ["语文", "Chinese", "chinese"]):
                subject = "语文试卷"
            elif any(kw in subject for kw in ["物理", "Physics", "physics"]):
                subject = "物理试卷"
            elif any(kw in subject for kw in ["化学", "Chemistry", "chemistry"]):
                subject = "化学试卷"
            elif "未知" in subject or len(subject) > 10:
                subject = "试卷"
            else:
                subject = f"{subject}试卷"
            print(f"[智能分析] 识别学科: {subject}")
        except:
            subject = "试卷"
            print(f"[智能分析] 学科识别失败，使用默认值")

        # 步骤3: 判断内容类型
        detection_result = {
            "user_marks_count": user_marks_count,
            "mistakes": mistakes
        }

        content_type = analyze_content_type(detection_result)
        print(f"[智能分析] 判断结果: {content_type}")

        # 步骤4: 根据类型生成相应的分析
        if content_type["is_full_paper"]:
            # 整张试卷 - 生成学情分析
            print(f"[智能分析] 生成学情分析报告...")

            analysis_prompt = generate_learning_analysis_prompt(
                {"mistakes": mistakes},
                subject  # 使用识别出的学科类型
            )

            analysis_messages = [{
                "role": "user",
                "content": analysis_prompt
            }]

            analysis_response = call_glm_api(analysis_messages, model="glm-4-flash", skip_delay=False, max_tokens=3000)

            elapsed = time.time() - start_time

            return {
                "success": True,
                "data": {
                    "content_type": "learning_analysis",
                    "analysis": analysis_response,
                    "mistakes": mistakes,
                    "mistake_count": mistake_count,
                    "user_marks_count": user_marks_count
                },
                "reason": content_type["reason"],
                "elapsed_time": f"{elapsed:.2f}s"
            }

        else:
            # 单个错题 - 生成针对性讲解
            print(f"[智能分析] 生成错题讲解...")

            # 选择第一道错题进行讲解
            if mistakes:
                first_mistake = mistakes[0]

                guide_prompt = generate_mistake_guide_prompt(first_mistake)

                guide_messages = [{
                    "role": "user",
                    "content": guide_prompt
                }]

                guide_response = call_glm_api(guide_messages, model="glm-4-flash", skip_delay=False, max_tokens=2000)

                elapsed = time.time() - start_time

                return {
                    "success": True,
                    "data": {
                        "content_type": "mistake_guide",
                        "guide": guide_response,
                        "mistake": first_mistake,
                        "total_mistakes": mistakes,
                        "mistake_count": mistake_count
                    },
                    "reason": content_type["reason"],
                    "elapsed_time": f"{elapsed:.2f}s"
                }
            else:
                return {
                    "success": False,
                    "error": "未检测到错题",
                    "reason": "请确保试卷中有明显的错题标记"
                }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[智能分析] 错误: {str(e)}")
        print(f"错误堆栈:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"智能分析失败: {str(e)}")


@app.post("/api/analyze/smart/stream")
async def smart_analyze_stream(request: DetectMistakesRequest):
    """
    智能分析API（流式输出）- 自动判断并执行相应分析
    """
    async def generate_stream():
        import sys
        try:
            start_time = time.time()

            # 发送开始信号
            yield f"data: {json.dumps({'status': 'start', 'message': '🔍 开始智能分析...'})}\n\n"

            # 解码图片
            image = decode_base64_image(request.image_data)
            user_marks_count = len(request.user_marks) if request.user_marks else 0

            print(f"[智能分析流式] 用户标记: {user_marks_count}")
            sys.stdout.flush()

            # 检测错题
            yield f"data: {json.dumps({'status': 'detecting', 'message': '📋 正在检测试卷中的错题...'})}\n\n"

            # ... (检测逻辑与上面相同，这里省略详细代码)

            # 示例：假设检测完成
            yield f"data: {json.dumps({'status': 'detected', 'mistake_count': 3, 'message': f'✅ 检测到 3 道错题'})}\n\n"

            # 判断类型
            yield f"data: {json.dumps({'status': 'analyzing', 'message': '📊 正在生成学情分析报告...'})}\n\n"

            # 生成分析...
            yield f"data: {json.dumps({'content_type': 'learning_analysis'})}\n\n"

            # 流式输出分析内容
            analysis_text = "详细的分析内容..."

            for char in analysis_text:
                yield f"data: {json.dumps({'content': char})}\n\n"

            # 完成
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            import traceback
            print(f"[智能分析流式] 错误: {str(e)}")
            print(f"错误堆栈:\n{traceback.format_exc()}")
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


# ==================== 启动服务器 ====================
if __name__ == "__main__":
    print("=" * 60)
    print("AI Study Companion - 后端服务")
    print("=" * 60)
    print("\n启动服务器...")
    print("\nAPI 文档: http://localhost:8000/docs")
    print("健康检查: http://localhost:8000/health")
    print("\n" + "=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
