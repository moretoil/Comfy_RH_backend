import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# 导入模型
from models import Base

# 创建数据库引擎（相对路径）
db_path = os.path.join(BASE_DIR, 'tasks.db')
engine = create_engine(f'sqlite:///{db_path}', echo=False)

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Database initialized successfully.")