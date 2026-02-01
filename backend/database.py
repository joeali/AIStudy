"""
数据库模型定义
使用 SQLAlchemy 进行数据持久化
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aistudy.db")

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    settings = Column(JSON, default={})  # 用户设置

    # 关系
    mistakes = relationship("Mistake", back_populates="user", cascade="all, delete-orphan")
    practices = relationship("Practice", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("Progress", back_populates="user", cascade="all, delete-orphan")


class Mistake(Base):
    """错题记录表"""
    __tablename__ = "mistakes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_no = Column(String(50))
    question = Column(Text, nullable=False)
    question_image = Column(Text)  # base64编码的图片
    student_answer = Column(String(500))
    correct_answer = Column(Text)
    error_reason = Column(Text)
    knowledge_point = Column(String(200))
    subject = Column(String(50), default="数学")  # 学科
    difficulty = Column(String(20))  # 难度
    analysis = Column(Text)  # 详细分析
    suggestion = Column(Text)  # 改进建议
    mastered = Column(Boolean, default=False)  # 是否已掌握
    review_count = Column(Integer, default=0)  # 复习次数
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)  # 最后复习时间

    # 关系
    user = relationship("User", back_populates="mistakes")


class Practice(Base):
    """练习记录表"""
    __tablename__ = "practices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(50), nullable=False)
    difficulty = Column(String(20))
    question_count = Column(Integer)
    questions = Column(JSON)  # 练习题列表
    answers = Column(JSON)  # 用户答案
    correct_count = Column(Integer)  # 正确数量
    accuracy = Column(Float)  # 正确率
    weak_points = Column(JSON)  # 薄弱知识点
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # 关系
    user = relationship("User", back_populates="practices")


class Progress(Base):
    """学习进度表"""
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(50), nullable=False)
    week_start = Column(DateTime, nullable=False)  # 周开始日期
    total_questions = Column(Integer, default=0)
    correct_questions = Column(Integer, default=0)
    accuracy = Column(Float, default=0)
    time_spent = Column(Integer, default=0)  # 学习时间(分钟)
    weak_points = Column(JSON)  # 薄弱知识点列表
    strong_points = Column(JSON)  # 优势知识点列表
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="progress")


class AnalysisHistory(Base):
    """学情分析历史表"""
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_data = Column(Text)  # base64编码的试卷图片
    mistakes = Column(JSON)  # 检测到的错题
    analysis = Column(Text)  # 学情分析内容
    summary = Column(String(500))  # 摘要
    mistake_count = Column(Integer)  # 错题数量
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库初始化成功")


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 导出模型和函数
__all__ = [
    "Base",
    "User",
    "Mistake",
    "Practice",
    "Progress",
    "AnalysisHistory",
    "engine",
    "init_db",
    "get_db"
]
