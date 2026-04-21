"""
统一处理器模块

集成记忆、意图识别和处理链，提供完整的处理流程
"""

import logging
from typing import Callable, Dict, Any, Optional
from .memory import create_memory, format_chat_history
from .intent import detect_intent
from .chains import create_knowledge_chain, create_general_chain
from RAGFlow_utils.query_enhancer import enhance_query
from .config import DEFAULT_SESSION_ID
from langchain.schema import AIMessage, HumanMessage


def create_unified_processor(
    system_prompt: str = "你是一个智能助手，可以根据需要查询知识库或直接回答用户问题。",
    session_id: str = DEFAULT_SESSION_ID
) -> Callable[[str], AsyncGenerator[Dict[str, Any], None]]:
    """
    创建统一处理器
    
    Args:
        system_prompt: 系统提示词
        session_id: 会话ID，用于MongoDB存储
        
    Returns:
        Callable: 处理函数，接受问题并返回包含回答和元数据的字典
    """


    async def processor(question: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理用户问题

        Args:
            question: 用户问题

        Returns:
            Dict: 包含回答和元信息的字典
        """

    
    # 添加实用函数
    def get_stats() -> Dict[str, int]:
        """获取处理统计信息"""

    
    def clear_memory() -> None:
        """清除对话记忆"""

    
