"""
处理链模块

提供不同类型的处理链：
1. 知识库查询链 - 使用知识库回答问题
2. 一般对话链 - 使用模型直接回答问题
"""

from typing import Dict, Any, Callable, AsyncGenerator
import os
import sys
import logging
from dotenv import load_dotenv
from openai import OpenAI
from langchain.schema import AIMessage, SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# 导入RAGFlow_mcp模块
from RAGFlow_mcp.chat import RAGFlow_chat

# 导入查询增强模块
from RAGFlow_utils.query_enhancer import enhance_query

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()


# AsyncGenerator是 Python中的异步生成器类型，用于逐步产生数据而不是一次性返回全部数据，实现流式处理
# AsyncGenerator[str, None] 第一个参数为每次产生的值的类型，第二个值为每次接收的值类型。因为此函数只产生不接收，所以为None
# async def 表示异步函数，可以使用yield产生异步流式输出。
async def call_llm(question: str, prompt: str) -> AsyncGenerator[str, None]:
    """
    调用大模型进行回答

    Args:
        question: 用户问题
        prompt: 完整提示词

    Yields:
        str: 模型回答的字符串片段，逐步产生
    """
    logger.info(f"调用LLM处理问题: {question[:50]}...")

    try:
        # 模型信息配置
        api_key = os.getenv("DASHSCOPE_API_KEY")
        model = os.getenv("LLM_MODEL", "qwen2.5-14b-instruct")
        base_url = os.getenv("DASHSCOPE_BASE_URL")

        # 创建LangChain的ChatOpenAI模型
        llm = ChatOpenAI(
            model=model,
            # openai_api_key=api_key,
            # openai_api_base=base_url,
            base_url=base_url,
            api_key=api_key,
            streaming=True  # 启用流式输出
        )

        # 创建提示模板
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", prompt),
            ("human", question)
        ])

        # 构建Runnable链
        chain = chat_prompt | llm

        # 使用astream进行异步流式调用
        async for chunk in chain.astream({}):
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk.content

    except Exception as e:
        error_msg = f"调用LLM出错: {str(e)}"
        logger.error(error_msg)
        yield f"回答生成失败: {str(e)}"


# 参数中的两个str代表process_with_knowledge中参数的两个str，AsyncGenerator[str, None]代表函数的返回值类型
# 初始化链;
def create_knowledge_chain(system_prompt: str = "你是一个有用的助手，能够利用知识库回答用户问题。") -> Callable[
    [str, str], AsyncGenerator[str, None]]:
    """
    创建知识库查询链

    Args:
        system_prompt: 系统提示词

    Returns:
        Callable: 处理函数，接受问题和历史记录，返回异步生成器产生回答字符串片段
    """

    async def process_with_knowledge(question: str, history: str) -> AsyncGenerator[str, None]:
        """使用知识库处理问题"""
        logger.info(f"使用知识库处理问题: {question[:50]}...")

        # 使用查询增强处理原始问题
        enhanced_question = enhance_query(question, history)
        logger.info(f"查询增强: '{question}' -> '{enhanced_question}'")

        # 使用增强后的问题调用RAGFlow
        rag_answer = RAGFlow_chat(enhanced_question)
        logger.info(f"RAGFlow返回结果长度: {len(rag_answer)}")

        # 构建完整提示，使用原始问题
        prompt = system_prompt + "\n\n"

        if history:
            prompt += f"以下是你和用户之前的对话记录，请参考这些记录：\n{history}\n\n"

        prompt += f"用户问题: {question}\n\n"

        prompt += f"以下是从知识库中检索到的相关信息：\n{rag_answer}\n\n"
        prompt += "请基于上述知识库信息和对话历史回答用户问题，如果知识库中没有相关信息，请说明并尽可能用你自己的知识回答。\n\n"
        prompt += f"用户问题: {question}"

        # 调用LLM
        async for chunk in call_llm(question, prompt):
            yield chunk

    return process_with_knowledge


def create_general_chain(system_prompt: str = "你是一个有用的助手，能够回答各种问题。") -> Callable[
    [str, str], AsyncGenerator[str, None]]:
    """
    创建一般对话链

    Args:
        system_prompt: 系统提示词

    Returns:
        Callable: 处理函数，接受问题和历史记录，返回异步生成器产生回答字符串片段
    """

    async def process_general_chat(question: str, history: str) -> AsyncGenerator[str, None]:
        """一般对话处理问题"""
        logger.info(f"使用一般对话处理问题: {question[:50]}...")

        # 构建提示
        prompt = system_prompt + "\n\n"

        if history:
            prompt += f"以下是你和用户之前的对话记录，请参考这些记录：\n{history}\n\n"

        prompt += f"用户问题: {question}"

        # 流式调用LLM并转发输出
        async for chunk in call_llm(question, prompt):
            yield chunk

    return process_general_chat


if __name__ == "__main__":
    import asyncio
    import os
    import sys

    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, PROJECT_ROOT)


    async def streaming():
        """测试流式输出效果"""
        print("[测试] 知识库查询链流式功能...")
        knowledge_chain = create_knowledge_chain()
        question1 = "那它的风景怎么样？"
        history1 = "用户: 瓦尔登湖在哪里\n助手: 瓦尔登湖在美国。"

        print(f"问题: {question1}")
        print(f"历史: {history1}")
        print("流式回答: ", end="", flush=True)

        full_answer = ""
        async for chunk in knowledge_chain(question1, history1):
            print(chunk, end="", flush=True)  # 实时打印每个片段
            full_answer += chunk

        print(f"\n完整回答: {full_answer}\n")

        print("[测试] 一般对话链流式功能...")
        general_chain = create_general_chain()
        question2 = "那你如何看待它？"
        history2 = "用户: 你了解人工智能吗？\n助手: 当然，人工智能是我工作的基础。"

        print(f"问题: {question2}")
        print(f"历史: {history2}")
        print("流式回答: ", end="", flush=True)

        full_answer = ""
        async for chunk in general_chain(question2, history2):
            print(chunk, end="", flush=True)  # 实时打印每个片段
            full_answer += chunk

        print(f"\n完整回答: {full_answer}\n")


    # 运行异步测试
    asyncio.run(streaming())