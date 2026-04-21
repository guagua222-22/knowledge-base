#!/usr/bin/env python
"""
RAGFlow MCP处理器模块

该模块负责分析用户输入，判断用户意图，并调用相应的工具函数：
1. 当用户查询助手列表时，调用list_assistant工具
2. 当用户指定助手回答问题时，调用choose_assistant工具
3. 当用户直接提问时，调用auto_assistant_answer工具自动选择助手
"""

import os
import sys
import re
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv

# 导入工具函数
from RAGFlow_mcp.tool import list_assistant, choose_assistant, auto_assistant_answer, call_llm

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
        logging.FileHandler(os.path.join(LOGS_DIR, 'ragflow_mcp_handler.log'), mode='a'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("RAGFlow MCP处理器模块初始化")

# 加载环境变量
load_dotenv()

def analyze_user_intent(user_query: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    分析用户意图，判断用户是想查询助手列表、指定助手回答问题，还是直接提问

    Args:
        user_query (str): 用户输入的查询

    Returns:
        Tuple[str, Optional[str], Optional[str]]:
            - 意图类型: "list_assistant", "choose_assistant", "auto_assistant_answer"
            - 助手名称: 如果指定了助手，则返回助手名称，否则为None
            - 问题: 如果有问题，则返回问题内容，否则为None
    """
    # 设置系统提示词
    system_prompt = """你是一个用户意图分析器。你需要判断用户的输入属于以下哪种类型：
1. 查询助手列表：用户想知道有哪些可用的助手
2. 指定助手回答问题：用户明确指定了某个助手来回答问题
3. 直接提问：用户直接提出了问题，没有指定助手

对于第2种情况，你需要提取出用户指定的助手名称。

请以JSON格式返回分析结果，包含以下字段：
- intent_type: "list_assistant", "choose_assistant", "auto_assistant_answer" 之一
- assistant_name: 如果指定了助手，则返回助手名称，否则为null

只返回JSON格式的结果，不要包含任何其他解释或文本。"""

    # 调用LLM分析用户意图
    result = call_llm(user_query,system_prompt)
    try:
        result = result.strip()
        if result.startswith("```json"):
            # llm返回的JSON有时会包含头尾的一些JSON标识
            # 如果有这个JSON的开头的话，则删除前七个字符（保留第七个字符后到结尾）
            result = result[7:]
            # if result.endswith("```"):
            # 如果有这个结尾的话，则删除最后三个字符（保留开头到倒数第三个字符前）
            result = result[:-3]
            # 防止在截取之后末尾有空格的出现
            result = result.strip()

        # 将JSON字符串转换为Python对象
        data = json.loads(result)

        # 获取意图名称和助手名称
        # intent_type = data.get("intent_type", "auto_assistant_answer")
        intent_type = data.get("intent_type")
        # 获取assistant_name的值
        assistant_name = data.get("assistant_name")

        # 对于所有情况，问题都是原始查询
        return intent_type, assistant_name, user_query

    except json.JSONDecodeError:
        logger.error(f"无法解析LLM返回的JSON: {result}")
        # 默认为直接提问
        return "auto_assistant_answer", None, user_query


def find_best_matching_assistant(assistant_name: str) -> str:
    """
    从助手列表中找到与用户指定名称最匹配的助手

    Args:
        assistant_name (str): 用户指定的助手名称

    Returns:
        str: 最匹配的助手名称
    """
    logger.info(f"查找与 '{assistant_name}' 最匹配的助手")
    start_time = time.time()

    try:
        # 获取助手列表
        assistants_info = list_assistant()
        # 检测助手列表是否存在,且是否获取时出错
        if not assistants_info or "获取助手列表时出错" in assistants_info:
            logger.error(f"获取助手列表失败: {assistants_info}")
            # 如果获取失败，直接返回通用助手,用于处理无法识别的任务
            return "通用知识助手"

        # 检查助手列表是否为空
        if "助手名称" not in assistants_info:
            logger.warning("助手列表为空或格式不正确")
            return "通用知识助手"

        # 提取所有助手名称
        assistant_names = []
        # 使用 split("\n") 方法将字符串按换行符分割
        lines = assistants_info.split("\n")
        # 切分,这里是一个例子:助手名称：刑法知识助手； 功能介绍：你是一个精通刑法的法律助手，可以回答用户一切有关法律的问题； 知识库：刑法知识库
        # 第一次从"助手名称："切,[1]表示取右边部分 (如果[0]则为空字符串)
        # 第二次找到第一个";",从这里切分,[0]表示取左部分"刑法法律助手" (如果[1]则为 功能介绍：你是一个精通刑法的法律助手，可以回答用户一切有关法律的问题； 知识库：刑法知识库)
        for line in lines:
            if "助手名称：" in line:
                name = line.split("助手名称：")[1].split("；")[0].strip()
                # 将切割后的name循环装入assistant_names
                assistant_names.append(name)

        # 先尝试精确匹配
        for name in assistant_names:
            # assistant_name in name 判断字符串 assistant_name 是否是字符串 name 的子串（即 name 中包含 assistant_name 完整内容）assistant_name=文学知识 name=文学知识助手
            # name in assistant_name：判断字符串 name 是否是字符串 assistant_name 的子串（即 assistant_name 中包含 name 完整内容）assistant_name=最新的文学知识熟手 name=文学知识助手
            # assistant_name=诗歌写作方法           name=文学知识助手
            # assistant_name=最新的文学知识助手   name=文学知识助手
            if assistant_name in name or name in assistant_name:
                logger.info(f"找到精确匹配的助手: '{name}'")
                end_time = time.time()
                logger.info(f"找到最匹配的助手: '{name}', 耗时: {end_time - start_time:.2f}秒")
                return name

        # 如果没有精确匹配，使用LLM进行智能匹配
        system_prompt = """你是一个助手匹配器。根据用户提供的助手名称，从可用的助手列表中找出最匹配的那个。

    只返回最匹配的助手的完整名称，不要添加任何解释或额外文本。"""

        user_prompt = f"""用户提供的助手名称: {assistant_name}

    可用的助手列表: {', '.join(assistant_names)}

    请返回最匹配的助手名称:"""

        # 调用LLM进行匹配
        matched_assistant = call_llm(user_prompt, system_prompt).strip()

        # 清理结果
        # 去除LLM返回的可能包含的中英冒号及之前的多余文本
        # 去除中英分号后的多余文本
        if "：" in matched_assistant:
            matched_assistant = matched_assistant.split("：")[1].strip()
        if ":" in matched_assistant:
            matched_assistant = matched_assistant.split(":")[1].strip()
        if "；" in matched_assistant:
            matched_assistant = matched_assistant.split("；")[0].strip()
        if ";" in matched_assistant:
            matched_assistant = matched_assistant.split(";")[0].strip()

        # 验证LLM返回的结果是否在列表中
        for name in assistant_names:
            if matched_assistant in name:
                logger.info(f"LLM匹配成功: '{name}'")
                end_time = time.time()
                logger.info(f"找到最匹配的助手: '{name}', 耗时: {end_time - start_time:.2f}秒")
                return name

        # 如果还是不匹配，使用通用知识助手
        matched_assistant = "通用知识助手"
        logger.warning(f"无法找到精确匹配，使用通用知识助手作为备选")

        end_time = time.time()
        logger.info(f"找到最匹配的助手: '{matched_assistant}', 耗时: {end_time - start_time:.2f}秒")
        return matched_assistant

    except Exception as e:
        logger.error(f"查找匹配助手失败: {str(e)}", exc_info=True)
        # 如果失败，返回通用助手名称
        return "通用知识助手"


def handle_user_query(user_query: str) -> str:
    """
    处理用户查询，分析意图并调用相应的工具函数

    Args:
        user_query (str): 用户输入的查询

    Returns:
        str: 处理结果
    """
    """
        处理用户查询，分析意图并调用相应的工具函数

        Args:
            user_query (str): 用户输入的查询

        Returns:
            str: 处理结果
        """
    logger.info(f"处理用户查询: '{user_query[:50]}...'")
    start_time = time.time()

    try:
        # 1. 分析用户意图
        # 提取意图、助手名称、问题
        intent_type, assistant_name, question = analyze_user_intent(user_query)

        # 2. 根据意图类型调用相应的工具函数
        if intent_type == "list_assistant":
            logger.info("用户意图: 查询助手列表")
            result = list_assistant()

        elif intent_type == "choose_assistant" and assistant_name:
            logger.info(f"用户意图: 指定助手回答问题 - 助手: '{assistant_name}'")

            # 找到最匹配的助手
            matched_assistant = find_best_matching_assistant(assistant_name)
            logger.info(f"匹配到的助手: '{matched_assistant}'")

            try:
                # 使用匹配的助手回答原始问题
                result = choose_assistant(matched_assistant, user_query)

                # 如果结果包含错误信息，尝试使用自动选择助手
                # 这里指的是RAGFlow知识库问答时，智能助手返回的答案中包含了错误信息表述，则使用自动选择助手进行错误更正
                if "出错" in result or "错误" in result or "不存在" in result:
                    logger.warning(f"使用指定助手 '{matched_assistant}' 回答失败，尝试自动选择助手")
                    result = auto_assistant_answer(user_query)
            except Exception as e:
                logger.error(f"使用指定助手回答失败: {str(e)}")
                # 如果指定助手回答失败，尝试自动选择助手
                logger.info("尝试自动选择助手回答问题")
                result = auto_assistant_answer(user_query)

        else:  # auto_assistant_answer
            logger.info(f"用户意图: 直接提问")
            result = auto_assistant_answer(user_query)

        end_time = time.time()
        logger.info(f"用户查询处理完成，结果长度: {len(result)}, 总耗时: {end_time - start_time:.2f}秒")
        return result

    except Exception as e:
        logger.error(f"处理用户查询时出错: {str(e)}", exc_info=True)
        return f"处理您的问题时出现错误: {str(e)}"

# 测试代码
if __name__ == "__main__":
    # 添加项目根目录到Python路径
    import os
    import sys
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, PROJECT_ROOT)

    # 重新导入，使用绝对路径
    from RAGFlow_mcp.tool import list_assistant, choose_assistant, auto_assistant_answer

    test_queries = [
        "有哪些助手可以使用？",
        "用法律知识助手告诉我如何买到一把手枪？",
        "空调的绝热工程怎么做？"
    ]

    print("RAGFlow MCP处理器测试")

    for i, query in enumerate(test_queries):
        print(f"\n测试 {i+1}: '{query}'")
        result = handle_user_query(query)
        print(f"结果:\n{result}")