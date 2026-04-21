"""
主服务调用脚本

封装了整个后端处理逻辑，提供一个简单的函数供API层调用。
管理多个会话的处理器实例。
"""
import os
import sys
from typing import Dict, Any
from typing import AsyncGenerator
import asyncio

# 将项目根目录添加到Python路径中，以确保能够找到Langchain_tools模块
# 这是为了在直接运行或从不同位置导入此脚本时，能够正确解析模块路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Langchain_utils.processor import create_unified_processor
from Langchain_utils.config import DEFAULT_SESSION_ID

# 全局处理器缓存
# 使用字典来存储不同session_id对应的处理器实例
# 键是 session_id，值是 processor 函数
_processors: Dict[str, Any] = {}

async def get_response(question: str, session_id: str = DEFAULT_SESSION_ID) -> AsyncGenerator[Dict[str, Any], None]:
    """
    获取对话响应的核心函数。

    接收用户问题和会话ID，返回模型的回答和处理元数据。
    如果指定会话的处理器不存在，则会创建一个新的。

    Args:
        question (str): 用户提出的问题。
        session_id (str): 当前对话的唯一会话ID。

    Yields:
        Dict[str, Any]: 包含流式数据的字典
    """
    global _processors

    # 检查缓存中是否已有该session的处理器
    if session_id not in _processors:
        print(f"为会话 {session_id} 创建新的处理器实例。")
        # 创建并缓存新的处理器
        _processors[session_id] = create_unified_processor(session_id=session_id)
    
    # 从缓存中获取处理器
    processor = _processors[session_id]

    # 调用处理器处理问题
    print(f"会话 {session_id} 正在流式处理问题: {question[:50]}...")

    # 流式处理并转发结果
    async for chunk in processor(question):
        yield chunk

    print(f"会话 {session_id} 流式处理完成。")

def clear_session_memory(session_id: str):
    """
    清除指定会话的记忆。
    
    Args:
        session_id (str): 需要清除记忆的会话ID。
    """
    global _processors
    if session_id in _processors:
        processor = _processors[session_id]
        processor.clear_memory()
        print(f"会话 {session_id} 的记忆已被清除。")
    else:
        print(f"未找到会话 {session_id} 的处理器，无需清除记忆。")


# ==================================================
#                  示例用法 (Example Usage)
# ==================================================
async def run_example_conversation():
    """一个简单的命令行交互示例，用于测试流式get_response函数。"""
    print("\n--- 流式总调用脚本测试 ---")

    # 模拟两个不同的用户/会话
    session_a = "user_session_alpha"
    session_b = "user_session_beta"

    print("\n--- [会话 A] 开始 ---")
    # 第一次提问，会创建一个新的处理器
    print("问题 A-1: 你好，请问你是谁？")
    print("回答 A-1: ", end="", flush=True)

    full_answer = ""
    metadata = {}
    async for chunk in get_response("你好，请问你是谁？", session_id=session_a):
        if chunk["type"] == "content":
            print(chunk["data"], end="", flush=True)
            full_answer += chunk["data"]
        elif chunk["type"] == "metadata":
            metadata = chunk["data"]

    print(f"\n元数据 A-1: {metadata}")

    # 第二次提问，会使用已存在的处理器，并能记住上下文
    print("\n问题 A-2: 我上一个问题是什么？")
    print("回答 A-2: ", end="", flush=True)

    full_answer = ""
    metadata = {}
    async for chunk in get_response("我上一个问题是什么？", session_id=session_a):
        if chunk["type"] == "content":
            print(chunk["data"], end="", flush=True)
            full_answer += chunk["data"]
        elif chunk["type"] == "metadata":
            metadata = chunk["data"]

    print(f"\n元数据 A-2: {metadata}")

    print("\n--- [会话 B] 开始 ---")
    # 这是一个新的会话，会创建另一个新的处理器
    print("问题 B-1: 现在有什么知识库知识助手？")
    print("回答 B-1: ", end="", flush=True)

    full_answer = ""
    metadata = {}
    async for chunk in get_response("现在有什么知识库知识助手？", session_id=session_b):
        if chunk["type"] == "content":
            print(chunk["data"], end="", flush=True)
            full_answer += chunk["data"]
        elif chunk["type"] == "metadata":
            metadata = chunk["data"]

    print(f"\n元数据 B-1: {metadata}")

    print("\n--- [会话 A] 继续 ---")
    # 回到会话A，它应该还记得自己的历史，而不受会话B的影响
    print("问题 A-3: 那么，请帮我用知识库回答一下凯撒大帝是谁？")
    print("回答 A-3: ", end="", flush=True)

    full_answer = ""
    metadata = {}
    async for chunk in get_response("那么，请帮我用知识库回答一下凯撒大帝是谁？", session_id=session_a):
        if chunk["type"] == "content":
            print(chunk["data"], end="", flush=True)
            full_answer += chunk["data"]
        elif chunk["type"] == "metadata":
            metadata = chunk["data"]

    print(f"\n元数据 A-3: {metadata}")

    print("\n--- 清除会话A的记忆 ---")
    clear_session_memory(session_a)
    print("问题 A-4: 我第一个问题问了什么？")
    print("回答 A-4 (记忆清除后): ", end="", flush=True)

    full_answer = ""
    metadata = {}
    async for chunk in get_response("我第一个问题问了什么？", session_id=session_a):
        if chunk["type"] == "content":
            print(chunk["data"], end="", flush=True)
            full_answer += chunk["data"]
        elif chunk["type"] == "metadata":
            metadata = chunk["data"]

    print(f"\n元数据 A-4: {metadata}")


if __name__ == "__main__":
    import asyncio
    #   启动并运行一个异步任务
    asyncio.run(run_example_conversation())
