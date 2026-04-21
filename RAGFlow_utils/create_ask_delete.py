#!/usr/bin/env python
"""
创建会话、提问并删除会话的工具模块

该模块提供了一个简单的函数，用于创建临时会话、提问并获取回答后删除会话。
主要用于单次查询RAGFlow知识库的场景，避免创建大量持久会话。
"""

import os
import sys
import logging
import requests
import time  # 添加time模块导入
from ragflow_sdk import RAGFlow
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_ask_delete(assistant_name: str, question: str) -> str:
    """
    创建一个新会话，提问一次，然后删除该会话，并返回答案。提供给外部进行调用
    Args:
        assistant_name (str): 助手的名称.
        question (str): 要问的问题.
    Returns:
        str: 助手的回答.
        Raises: Exception: 如果操作过程中发生错误，将抛出异常.
    """
    logger.info(f"开始处理单次查询 - 助手: '{assistant_name}', 问题: '{question[:50]}...'")

    load_dotenv()
    api_key = os.getenv("RAGFLOW_API_KEY")
    base_url = os.getenv("RAGFLOW_API_URL")

    logger.info(f"使用API URL: {base_url}")
    logger.info(f"API密钥: {api_key[:10]}...")  # 只记录前10个字符，保护密钥安全

    try:
        # 测试API连接
        logger.info("测试API连接...")
        test_response = requests.get(f"{base_url}/health", timeout=5)
        logger.info(f"API健康检查响应: 状态码={test_response.status_code}")
        if test_response.status_code != 200:
            logger.error(f"API健康检查失败: {test_response.text}")
    except requests.RequestException as e:
        logger.error(f"无法连接到RAGFlow API: {str(e)}")
        return f"连接RAGFlow服务失败: {str(e)}"

    try:
        logger.info("创建RAGFlow客户端...")
        rag_object = RAGFlow(api_key=api_key, base_url=base_url)

        logger.info(f"获取助手列表: {assistant_name}")
        assistants = rag_object.list_chats(name=assistant_name)
        logger.info(f"获取到 {len(assistants) if assistants else 0} 个匹配的助手")

        if not assistants:
            error_msg = f"未找到名为 '{assistant_name}' 的助手。"
            logger.error(error_msg)
            return error_msg

        assistant = assistants[0]
        logger.info(f"选择助手: {assistant.name}")

        session = None
        try:
            logger.info("创建临时会话...")
            session = assistant.create_session(name="temp_session_for_single_ask")
            logger.info(f"会话创建成功, ID: {session.id if hasattr(session, 'id') else 'unknown'}")

            logger.info(f"发送问题: '{question[:50]}...'")
            response_generator = session.ask(question, stream=True)
            logger.info("开始接收流式响应...")

            full_answer = ""
            for part in response_generator:
                if hasattr(part, 'content') and part.content:
                    full_answer = part.content

            answer = full_answer
            logger.info(f"获取到完整回答, 长度: {len(answer)}")

            # 等待5秒钟，确保响应被完全处理
            logger.info("等待5秒钟，确保响应被完全处理后再删除会话...")
            time.sleep(5)

        finally:
            # 确保删除会话，即使提问失败
            if session and hasattr(session, 'id'):
                logger.info(f"删除临时会话: {session.id}")
                try:
                    assistant.delete_sessions(ids=[session.id])
                    logger.info("会话删除成功")
                except Exception as e:
                    logger.error(f"删除会话失败: {str(e)}")

        return answer

    except requests.exceptions.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {str(e)}")
        logger.error(f"可能的原因: API返回了非JSON格式的响应，这通常表示API端点配置错误或服务器返回了HTML错误页面")
        return f"RAGFlow API返回了无效的JSON响应: {str(e)}"
    except Exception as e:
        logger.error(f"处理过程中发生错误: {str(e)}", exc_info=True)
        return f"处理查询时出错: {str(e)}"


if __name__ == "__main__":
    # 功能测试
    assistant = "文学知识助手"  # 替换为你的默认助手名称
    question_text = "请问瓦尔登湖在哪里"
    print(create_ask_delete(assistant, question_text))