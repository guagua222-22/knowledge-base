#!/usr/bin/env python
"""
RAGFlow MCP工具模块

该模块提供了三种主要工具功能：
1. 列出所有可用的助手列表
2. 使用指定的助手回答问题
3. 自动分析并选择合适的助手回答问题

通过调用RAGutils中的函数实现核心功能。
"""

import os
import sys
import json
import logging
import time
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
from langchain_core.runnables import RunnablePassthrough, Runnable
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# 导入RAGutils中的函数
from RAGFlow_utils.create_ask_delete import create_ask_delete
from RAGFlow_utils.list_chat_assistant import get_assistant_list

# 获取项目根目录的绝对路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')

# 确保日志目录存在
os.makedirs(LOGS_DIR, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'ragflow_mcp_tools.log'), mode='a'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("RAGFlow MCP工具模块初始化")

# 加载环境变量
load_dotenv()

def list_assistant() -> str:
    """
    列出所有可用的助手
    
    Returns:
        str: 助手列表信息
    """
    return get_assistant_list()


def choose_assistant(assistant_name: str, question: str) -> str:
    """
    使用指定的助手回答问题
    
    Args:
        assistant_name (str): 助手名称
        question (str): 用户问题
        
    Returns:
        str: 助手的回答
    """
    logger.info(f"使用指定助手 '{assistant_name}' 回答问题: '{question[:50]}...'")
    start_time = time.time()
    
    try:
        # 调用create_ask_delete并保存返回值
        answer = create_ask_delete(assistant_name, question)

        end_time = time.time()
        logger.info(f"助手 '{assistant_name}' 回答完成，回答长度: {len(answer) if answer else 0}, 耗时: {end_time - start_time:.2f}秒")
        
        return answer
        
    except Exception as e:
        logger.error(f"使用助手 '{assistant_name}' 回答问题时出错: {str(e)}", exc_info=True)
        return f"使用助手回答问题失败: {str(e)}"
# 使用llm处理
def call_llm(prompt: str, instruction: str) -> str:
    """
    调用大模型进行分析

    Args:
        prompt (str): 用户提示
        instruction (str): 系统指令

    Returns:
        str: 大模型的回复
    """
    logger.info(f"调用LLM处理: '{prompt[:50]}...'")

    try:
        # 初始化大语言模型
        api_key = os.getenv("DASHSCOPE_API_KEY")
        model = os.getenv("LLM_QWEN2.5")
        base_url = os.getenv("DASHSCOPE_BASE_URL")

        llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model
        )

        # 创建提示词模板
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "{instruction}"),
                ("human", "{prompt}")
            ]
        )

        # 构建链
        llm_chain: Runnable = prompt_template | llm

        # 执行
        reponse = llm_chain.invoke(
            {
                "instruction": instruction,
                "prompt": prompt
            }
        )
        result = reponse.content
        return result

    except Exception as e:
        logger.error(f"LLM调用失败: {str(e)}", exc_info=True)
        return f"调用LLM时发生错误: {str(e)}"


# 3 自动选择合适的助手回答问题
def auto_assistant_answer(question: str) -> str:
    """
    自动选择合适的助手回答问题

    Args:
        question (str): 用户问题

    Returns:
        str: 助手的回答
    """
    # 获取所有聊天助手
    assistants_info = get_assistant_list()
    # 判断是否获取所有聊天助手成功
    if not assistants_info or assistants_info.startswith("获取助手列表时出错"):
        return "无法获取助手列表，自动选择助手失败"

    # 2. 构建提示词，让LLM分析选择合适的助手
    system_prompt = """你是一个助手选择器。你需要根据用户的问题和提供的助手列表，选择最适合回答该问题的助手。
分析每个助手的功能介绍和关联的知识库，选择最匹配用户问题主题的助手。
请只返回选择的助手名称，不要添加任何解释或额外文本。"""

    user_prompt = f"""用户问题: {question}

    可用的助手列表:
    {assistants_info}

    请选择最合适的助手来回答这个问题:"""

    # 调用方法选择合适助手
    selected_assistant = call_llm(user_prompt, system_prompt).strip()

    # 使用指定助手回答问题
    answer = create_ask_delete(selected_assistant, question)
    return answer

# 测试代码
if __name__ == "__main__":
    print("RAGFlow MCP工具测试")
    
    try:
        # 测试列出助手
        print("\n1. 测试列出助手:")
        assistants = list_assistant()
        print(f"助手列表:\n{assistants}\n")
        
        # 测试自动选择助手回答问题
        print("\n2. 测试自动选择助手:")
        question = "瓦尔登湖在哪里？"
        print(f"问题: {question}")
        answer = auto_assistant_answer(question)
        print(f"回答:\n{answer}\n")
        
        # 测试指定助手回答问题
        print("\n3. 测试指定助手:")
        assistant_name = "刑法法律助手"  # 替换为实际存在的助手名称
        question = "刑法的准则是什么？"
        print(f"助手: {assistant_name}")
        print(f"问题: {question}")
        answer = choose_assistant(assistant_name, question)
        print(f"回答:\n{answer}\n")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}") 