"""
配置文件，管理MongoDB等外部服务的连接参数
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# MongoDB配置
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "conversation_db")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "chat_history")

# 其他配置参数
DEFAULT_SESSION_ID = "default"
SESSION_TTL_DAYS = 30  # 会话过期天数 