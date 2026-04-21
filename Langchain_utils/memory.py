"""
记忆管理模块

负责对话历史的存储和格式化，提供：
1. 创建记忆对象（支持MongoDB存储）
2. 格式化对话历史
"""

from typing import List, Any
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from langchain_mongodb import MongoDBChatMessageHistory
import logging

# 导入配置
try:
    from .config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION, DEFAULT_SESSION_ID
except ImportError:
    from Langchain_utils.config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION, DEFAULT_SESSION_ID
# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_memory(session_id: str = DEFAULT_SESSION_ID) -> ConversationBufferMemory:
    """
    创建对话记忆对象，使用MongoDB存储
    Args:
        session_id: 会话ID，用于区分不同的对话

    Returns:
        ConversationBufferMemory: 对话记忆对象
    """

    connection_string = f"{MONGODB_URI.rstrip('/')}/{MONGODB_DB}"

    # 创建基于MongoDB的消息历史
    # # 将对话内容持久化存储到MongoDB数据库中
    message_history = MongoDBChatMessageHistory(
        connection_string=connection_string,
        collection_name=MONGODB_COLLECTION,
        database_name=MONGODB_DB,
        session_id=session_id,
    )

    # 创建聊天记忆存储对象，设置mongodb持久化
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        chat_memory=message_history,
        input_key="question",
        output_key="answer",
        return_messages=True
    )

    return memory

def format_chat_history(messages: List[Any]) -> str:
    """
    将消息列表格式化为文本

    Args:
        messages: 消息对象列表

    Returns:
        str: 格式化后的对话历史文本
    """
    formatted = ""
    for msg in messages:
        # ininstance用于检查一个对象是否属于指定的类型或类型元组
        # 第一个参数是检查的对象,第二个参数是类型或类型元组
        # 返回 True和False
        if isinstance(msg, HumanMessage):
            formatted += f"用户: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            formatted += f"助手: {msg.content}\n"
    return formatted

if __name__ == "__main__":
    import os
    import sys
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, PROJECT_ROOT)

    # 只在测试区用绝对导入
    from Langchain_utils.config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION, DEFAULT_SESSION_ID

    print("[测试] 创建记忆对象...")
    memory = create_memory("test_session")

    # 向记忆中添加几条对话
    memory.save_context({"question": "你好，AI！"}, {"answer": "你好，有什么可以帮您？"})
    memory.save_context({"question": "今天天气怎么样？"}, {"answer": "今天天气晴朗，适合出行。"})

    # 获取历史消息
    messages = memory.chat_memory.messages
    print("[测试] 格式化对话历史：")
    print(format_chat_history(messages))