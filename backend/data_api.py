"""
数据持久化 API 端点
处理用户数据的保存和加载
"""

from fastapi import HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_db, User, Mistake, Practice, Progress, AnalysisHistory, init_db
from sqlalchemy.orm import Session
import json


# ==================== 数据模型 ====================

class MistakeCreate(BaseModel):
    """创建错题请求"""
    username: str
    question_no: Optional[str] = None
    question: str
    question_image: Optional[str] = None
    student_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    error_reason: Optional[str] = None
    knowledge_point: Optional[str] = None
    subject: str = "数学"
    difficulty: Optional[str] = None
    analysis: Optional[str] = None
    suggestion: Optional[str] = None


class MistakeUpdate(BaseModel):
    """更新错题请求"""
    id: int
    mastered: Optional[bool] = None
    review_count: Optional[int] = None


class PracticeCreate(BaseModel):
    """创建练习记录请求"""
    username: str
    subject: str
    difficulty: Optional[str] = None
    question_count: int
    questions: List[dict]
    answers: List[dict]
    correct_count: int
    accuracy: float
    weak_points: Optional[List[str]] = None


class ProgressUpdate(BaseModel):
    """更新学习进度请求"""
    username: str
    subject: str
    total_questions: int
    correct_questions: int
    accuracy: float
    time_spent: int
    weak_points: Optional[List[str]] = None
    strong_points: Optional[List[str]] = None


class AnalysisHistoryCreate(BaseModel):
    """创建学情分析历史请求"""
    username: str
    image_data: Optional[str] = None
    mistakes: List[dict]
    analysis: str
    summary: str
    mistake_count: int


# ==================== 辅助函数 ====================

def get_or_create_user(db: Session, username: str) -> User:
    """获取或创建用户"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # 更新最后活跃时间
        user.last_active = datetime.utcnow()
        db.commit()
    return user


def get_week_start() -> datetime:
    """获取本周一的日期"""
    today = datetime.utcnow()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    return week_start.replace(hour=0, minute=0, second=0, microsecond=0)


# ==================== 错题管理 API ====================

def save_mistake(mistake_data: MistakeCreate, db: Session = Depends(get_db)):
    """保存错题"""
    try:
        # 获取或创建用户
        user = get_or_create_user(db, mistake_data.username)

        # 创建错题记录
        mistake = Mistake(
            user_id=user.id,
            question_no=mistake_data.question_no,
            question=mistake_data.question,
            question_image=mistake_data.question_image,
            student_answer=mistake_data.student_answer,
            correct_answer=mistake_data.correct_answer,
            error_reason=mistake_data.error_reason,
            knowledge_point=mistake_data.knowledge_point,
            subject=mistake_data.subject,
            difficulty=mistake_data.difficulty,
            analysis=mistake_data.analysis,
            suggestion=mistake_data.suggestion
        )

        db.add(mistake)
        db.commit()
        db.refresh(mistake)

        return {
            "success": True,
            "data": {
                "id": mistake.id,
                "question": mistake.question,
                "subject": mistake.subject,
                "created_at": mistake.created_at.isoformat()
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存错题失败: {str(e)}")


def get_mistakes(username: str, subject: Optional[str] = None, db: Session = Depends(get_db)):
    """获取用户的错题列表"""
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return {"success": True, "data": {"mistakes": []}}

        query = db.query(Mistake).filter(Mistake.user_id == user.id)
        if subject:
            query = query.filter(Mistake.subject == subject)

        mistakes = query.order_by(Mistake.created_at.desc()).all()

        return {
            "success": True,
            "data": {
                "mistakes": [
                    {
                        "id": m.id,
                        "question_no": m.question_no,
                        "question": m.question,
                        "question_image": m.question_image,
                        "student_answer": m.student_answer,
                        "correct_answer": m.correct_answer,
                        "error_reason": m.error_reason,
                        "knowledge_point": m.knowledge_point,
                        "subject": m.subject,
                        "difficulty": m.difficulty,
                        "analysis": m.analysis,
                        "suggestion": m.suggestion,
                        "mastered": m.mastered,
                        "review_count": m.review_count,
                        "created_at": m.created_at.isoformat(),
                        "reviewed_at": m.reviewed_at.isoformat() if m.reviewed_at else None
                    }
                    for m in mistakes
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错题失败: {str(e)}")


def update_mistake(mistake_data: MistakeUpdate, db: Session = Depends(get_db)):
    """更新错题状态"""
    try:
        mistake = db.query(Mistake).filter(Mistake.id == mistake_data.id).first()
        if not mistake:
            raise HTTPException(status_code=404, detail="错题不存在")

        if mistake_data.mastered is not None:
            mistake.mastered = mistake_data.mastered
            if mistake_data.mastered:
                mistake.reviewed_at = datetime.utcnow()

        if mistake_data.review_count is not None:
            mistake.review_count = mistake_data.review_count

        db.commit()

        return {"success": True, "data": {"id": mistake.id, "mastered": mistake.mastered}}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新错题失败: {str(e)}")


def delete_mistake(mistake_id: int, db: Session = Depends(get_db)):
    """删除错题"""
    try:
        mistake = db.query(Mistake).filter(Mistake.id == mistake_id).first()
        if not mistake:
            raise HTTPException(status_code=404, detail="错题不存在")

        db.delete(mistake)
        db.commit()

        return {"success": True, "message": "错题已删除"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除错题失败: {str(e)}")


# ==================== 练习记录 API ====================

def save_practice(practice_data: PracticeCreate, db: Session = Depends(get_db)):
    """保存练习记录"""
    try:
        user = get_or_create_user(db, practice_data.username)

        practice = Practice(
            user_id=user.id,
            subject=practice_data.subject,
            difficulty=practice_data.difficulty,
            question_count=practice_data.question_count,
            questions=practice_data.questions,
            answers=practice_data.answers,
            correct_count=practice_data.correct_count,
            accuracy=practice_data.accuracy,
            weak_points=practice_data.weak_points,
            completed_at=datetime.utcnow()
        )

        db.add(practice)
        db.commit()
        db.refresh(practice)

        return {
            "success": True,
            "data": {
                "id": practice.id,
                "subject": practice.subject,
                "accuracy": practice.accuracy,
                "completed_at": practice.completed_at.isoformat()
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存练习记录失败: {str(e)}")


def get_practices(username: str, subject: Optional[str] = None, db: Session = Depends(get_db)):
    """获取练习记录"""
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return {"success": True, "data": {"practices": []}}

        query = db.query(Practice).filter(Practice.user_id == user.id)
        if subject:
            query = query.filter(Practice.subject == subject)

        practices = query.order_by(Practice.created_at.desc()).limit(50).all()

        return {
            "success": True,
            "data": {
                "practices": [
                    {
                        "id": p.id,
                        "subject": p.subject,
                        "difficulty": p.difficulty,
                        "question_count": p.question_count,
                        "correct_count": p.correct_count,
                        "accuracy": p.accuracy,
                        "weak_points": p.weak_points,
                        "created_at": p.created_at.isoformat(),
                        "completed_at": p.completed_at.isoformat() if p.completed_at else None
                    }
                    for p in practices
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取练习记录失败: {str(e)}")


# ==================== 学习进度 API ====================

def update_progress(progress_data: ProgressUpdate, db: Session = Depends(get_db)):
    """更新学习进度"""
    try:
        user = get_or_create_user(db, progress_data.username)
        week_start = get_week_start()

        # 查找本周的进度记录
        progress = db.query(Progress).filter(
            Progress.user_id == user.id,
            Progress.subject == progress_data.subject,
            Progress.week_start == week_start
        ).first()

        if progress:
            # 更新现有记录
            progress.total_questions += progress_data.total_questions
            progress.correct_questions += progress_data.correct_questions
            progress.accuracy = progress.correct_questions / progress.total_questions if progress.total_questions > 0 else 0
            progress.time_spent += progress_data.time_spent
            if progress_data.weak_points:
                existing_weak = progress.weak_points or []
                progress.weak_points = list(set(existing_weak + progress_data.weak_points))
            if progress_data.strong_points:
                existing_strong = progress.strong_points or []
                progress.strong_points = list(set(existing_strong + progress_data.strong_points))
            progress.updated_at = datetime.utcnow()
        else:
            # 创建新记录
            progress = Progress(
                user_id=user.id,
                subject=progress_data.subject,
                week_start=week_start,
                total_questions=progress_data.total_questions,
                correct_questions=progress_data.correct_questions,
                accuracy=progress_data.accuracy,
                time_spent=progress_data.time_spent,
                weak_points=progress_data.weak_points,
                strong_points=progress_data.strong_points
            )
            db.add(progress)

        db.commit()

        return {
            "success": True,
            "data": {
                "subject": progress.subject,
                "week_start": progress.week_start.isoformat(),
                "accuracy": progress.accuracy,
                "time_spent": progress.time_spent
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新学习进度失败: {str(e)}")


def get_progress(username: str, weeks: int = 4, db: Session = Depends(get_db)):
    """获取学习进度"""
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return {"success": True, "data": {"progress": []}}

        # 获取最近N周的数据
        start_date = get_week_start() - timedelta(weeks=weeks)

        progress_list = db.query(Progress).filter(
            Progress.user_id == user.id,
            Progress.week_start >= start_date
        ).order_by(Progress.week_start.desc()).all()

        return {
            "success": True,
            "data": {
                "progress": [
                    {
                        "subject": p.subject,
                        "week_start": p.week_start.isoformat(),
                        "total_questions": p.total_questions,
                        "correct_questions": p.correct_questions,
                        "accuracy": p.accuracy,
                        "time_spent": p.time_spent,
                        "weak_points": p.weak_points,
                        "strong_points": p.strong_points
                    }
                    for p in progress_list
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学习进度失败: {str(e)}")


# ==================== 学情分析历史 API ====================

def save_analysis_history(analysis_data: AnalysisHistoryCreate, db: Session = Depends(get_db)):
    """保存学情分析历史"""
    try:
        user = get_or_create_user(db, analysis_data.username)

        history = AnalysisHistory(
            user_id=user.id,
            image_data=analysis_data.image_data,
            mistakes=analysis_data.mistakes,
            analysis=analysis_data.analysis,
            summary=analysis_data.summary,
            mistake_count=analysis_data.mistake_count
        )

        db.add(history)
        db.commit()
        db.refresh(history)

        return {
            "success": True,
            "data": {
                "id": history.id,
                "summary": history.summary,
                "mistake_count": history.mistake_count,
                "created_at": history.created_at.isoformat()
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存学情分析失败: {str(e)}")


def get_analysis_history(username: str, limit: int = 10, db: Session = Depends(get_db)):
    """获取学情分析历史"""
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return {"success": True, "data": {"history": []}}

        history_list = db.query(AnalysisHistory).filter(
            AnalysisHistory.user_id == user.id
        ).order_by(AnalysisHistory.created_at.desc()).limit(limit).all()

        return {
            "success": True,
            "data": {
                "history": [
                    {
                        "id": h.id,
                        "mistakes": h.mistakes,
                        "summary": h.summary,
                        "mistake_count": h.mistake_count,
                        "created_at": h.created_at.isoformat()
                    }
                    for h in history_list
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学情分析历史失败: {str(e)}")


# ==================== 统计数据 API ====================

def get_statistics(username: str, db: Session = Depends(get_db)):
    """获取用户统计数据"""
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return {
                "success": True,
                "data": {
                    "total_mistakes": 0,
                    "mastered_mistakes": 0,
                    "total_practices": 0,
                    "subjects": {}
                }
            }

        # 错题统计
        total_mistakes = db.query(Mistake).filter(Mistake.user_id == user.id).count()
        mastered_mistakes = db.query(Mistake).filter(
            Mistake.user_id == user.id,
            Mistake.mastered == True
        ).count()

        # 练习统计
        total_practices = db.query(Practice).filter(Practice.user_id == user.id).count()

        # 按学科统计
        subjects = {}
        for subject in ["数学", "英语", "语文", "物理", "化学", "生物"]:
            mistake_count = db.query(Mistake).filter(
                Mistake.user_id == user.id,
                Mistake.subject == subject
            ).count()

            if mistake_count > 0:
                subjects[subject] = {"mistake_count": mistake_count}

        return {
            "success": True,
            "data": {
                "total_mistakes": total_mistakes,
                "mastered_mistakes": mastered_mistakes,
                "total_practices": total_practices,
                "subjects": subjects
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")
