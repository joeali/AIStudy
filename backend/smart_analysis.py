"""
智能分析模块 - 判断试卷类型并执行相应分析
- 整张试卷（≥3道错题）→ 学情分析
- 单个错题（1-2道题）→ 针对性讲解
"""

import json
import re

# 学情分析模板
LEARNING_ANALYSIS_TEMPLATE = """你是一位经验丰富的教育专家，擅长分析学生的试卷并提供详细的学情分析。

请根据学生试卷的答题情况，生成学情分析报告：

一、学习现状分析

从卷面反馈来看，请分析学生的学习优势，包括但不限于：
1. 基础知识掌握情况
2. 解题能力表现
3. 学习习惯和态度
4. 值得肯定的方面

二、薄弱点与失分原因分析

请详细分析学生的薄弱环节，按题型或知识点分类：

失分点1：[题型/知识点]
- 题号：列出相关题号
- 正确答案：给出正确答案
- 学生答案：学生的错误答案
- 深度分析：为什么出错？概念不清/方法不对/计算失误/审题不清？具体是哪个环节出了问题？
- 典型错误：描述学生犯的具体错误

失分点2：[题型/知识点]
（同上结构）

失分点3：[题型/知识点]
（同上结构）

三、学习建议

针对上述薄弱点，给出具体、可操作的学习建议：

针对性提升建议
1. 建议1：具体的学习方法或练习策略
2. 建议2：针对某个薄弱点的改进方案
3. 建议3：学习习惯或技巧方面的建议

每日练习计划
- 练习内容1（具体题型和数量）
- 练习内容2
- 练习内容3

四、知识点梳理

列出本次试卷涉及的核心知识点及掌握情况：

知识点1：掌握程度及说明
知识点2：掌握程度及说明

五、下次考试目标

基于本次分析，设定具体、可衡量的提升目标：
- 目标分数：具体的分数目标
- 重点突破：需要重点掌握的知识点
- 提分策略：如何实现目标

要求：
1. 分析要详细、具体，避免空泛
2. 失分原因要深入到具体环节
3. 学习建议要可操作、可执行
4. 用词鼓励性强，既指出问题也给予肯定
5. 适合学生和家长阅读理解
6. 格式简洁，避免过多符号

现在请根据检测到的错题，生成学情分析报告：
"""

# 错题讲解模板
MISTAKE_GUIDE_TEMPLATE = """你是一位耐心的老师，正在帮助学生理解错题。

请按照苏格拉底式引导方法，通过提问引导学生自己找到答案，而不是直接给出解题步骤。

引导流程：

第一步：理解题目
- 提问1：引导学生理解题目在问什么
- 提问2：帮助学生识别已知条件和要求

第二步：回顾知识点
- 提问3：引导学生回顾相关的知识点或公式
- 提问4：检查学生是否掌握基础概念

第三步：启发思路
- 提问5：提示解题思路的方向（不直接说答案）
- 提问6：引导学生思考第一步该怎么做

第四步：深入引导
- 根据学生的回答，给出递进式的提示
- 如果学生回答正确，给予肯定并推进
- 如果学生回答错误，委婉指出并给出提示

教学原则：
1. 不要直接给出答案或完整解题步骤
2. 每次只问一个问题
3. 使用启发式提问："你觉得...？""为什么会...？""你注意到...吗？"
4. 给予鼓励和肯定
5. 从学生的错误中学习，分析错误原因

现在请针对这道错题，开始引导：
"""


def generate_learning_analysis_prompt(mistakes_data, paper_info=""):
    """生成学情分析的prompt"""

    mistakes_list = mistakes_data.get("mistakes", [])
    mistake_count = len(mistakes_list)

    prompt = f"""{LEARNING_ANALYSIS_TEMPLATE}

试卷基本信息：
- 检测到错题数量：{mistake_count}道
- 试卷信息：{paper_info if paper_info else "试卷"}

错题详情：
"""

    # 添加每道错题的详细信息
    for idx, mistake in enumerate(mistakes_list, 1):
        question_no = mistake.get("question_no", f"第{idx}题")
        question = mistake.get("question", "题目内容未识别")
        student_answer = mistake.get("student_answer", "未作答")
        correct_answer = mistake.get("correct_answer", "未知")
        reason = mistake.get("reason", "答题错误")
        analysis = mistake.get("analysis", "")

        prompt += f"""
---
错题{idx}：
- 题号：{question_no}
- 题目内容：{question}
- 学生答案：{student_answer}
- 正确答案：{correct_answer}
- 错误原因：{reason}
- 详细分析：{analysis}
"""

    prompt += """

请严格按照上述模板格式，生成详细的学情分析报告。
"""

    return prompt


def generate_mistake_guide_prompt(mistake_data):
    """生成错题讲解的prompt"""

    question_no = mistake_data.get("question_no", "?")
    question = mistake_data.get("question", "题目内容未识别")
    student_answer = mistake_data.get("student_answer", "未作答")
    correct_answer = mistake_data.get("correct_answer", "未知")
    reason = mistake_data.get("reason", "答题错误")

    prompt = f"""{MISTAKE_GUIDE_TEMPLATE}

题目信息：
- 题号：{question_no}
- 题目内容：{question}
- 学生答案：{student_answer}
- 正确答案：{correct_answer}
- 错误标记：{reason}

请针对这道错题，开始苏格拉底式引导教学。
"""

    return prompt


def analyze_content_type(detection_result, force_type=None):
    """
    判断内容类型：整张试卷 vs 单个错题

    Args:
        detection_result: 检测结果
        force_type: 强制指定分析类型 ('full', 'mistakes', 或 None)

    判断依据：
    1. 如果指定了 force_type，直接使用
    2. 用户标记数量：≥3个 → 整张试卷，1-2个 → 单个错题
    3. 检测到的错题数量：≥3道 → 整张试卷，1-2道 → 单个错题
    4. 图片内容复杂度：多道题目 → 整张试卷
    """
    # 如果强制指定了类型，直接返回
    if force_type == 'full':
        return {
            "is_full_paper": True,
            "reason": "用户选择整体分析",
            "recommended_action": "学情分析",
            "confidence": "high"
        }
    elif force_type == 'mistakes':
        return {
            "is_full_paper": False,
            "reason": "用户选择错题分析",
            "recommended_action": "错题讲解",
            "confidence": "high"
        }

    # 原有的自动判断逻辑
    user_marks_count = detection_result.get("user_marks_count", 0)
    mistakes = detection_result.get("mistakes", [])
    mistake_count = len(mistakes)

    # 判断逻辑
    is_full_paper = False
    reason = ""

    if user_marks_count >= 3:
        is_full_paper = True
        reason = f"用户标记了{user_marks_count}个区域，判断为整张试卷分析"
    elif mistake_count >= 3:
        is_full_paper = True
        reason = f"检测到{mistake_count}道错题，判断为整张试卷分析"
    elif user_marks_count > 0:
        is_full_paper = False
        reason = f"用户标记了{user_marks_count}个区域，判断为单个错题讲解"
    else:
        is_full_paper = False
        reason = f"检测到{mistake_count}道错题，判断为单个错题讲解"

    return {
        "is_full_paper": is_full_paper,
        "reason": reason,
        "recommended_action": "学情分析" if is_full_paper else "错题讲解",
        "confidence": "high" if (user_marks_count >= 3 or mistake_count >= 3) else "medium"
    }


# 示例使用
if __name__ == "__main__":
    # 测试判断逻辑
    test_cases = [
        {"user_marks_count": 5, "mistakes": [{"question_no": "1"}]},
        {"user_marks_count": 0, "mistakes": [{"question_no": "1"}, {"question_no": "2"}, {"question_no": "3"}]},
        {"user_marks_count": 1, "mistakes": [{"question_no": "1"}]},
    ]

    for case in test_cases:
        result = analyze_content_type(case)
        print(f"输入: {case}")
        print(f"输出: {result}")
        print()
