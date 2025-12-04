from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()

class Task(Base):

    """
    Task类，用于表示任务信息，继承自Base类。
    对应数据库中的tasks表。
    """
    __tablename__ = 'tasks'  # 指定该类对应的数据库表名为'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, unique=True)
    webapp_id = Column(String)
    node_info_list = Column(Text)
    file_url = Column(String)
    file_type = Column(String)
    task_cost_time = Column(String)
    status = Column(String, default='PENDING')
    created_at = Column(DateTime, server_default=text("(datetime('now', '+8 hours'))"))

# 创建数据库引擎
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'tasks.db')
engine = create_engine(f'sqlite:///{db_path}', echo=False)

# 创建表
Base.metadata.create_all(engine)

# 创建会话工厂
SessionLocal = sessionmaker(bind=engine)