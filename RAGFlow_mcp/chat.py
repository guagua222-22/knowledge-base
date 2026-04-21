#!/usr/bin/env python
"""
RAGFlow MCP聊天模块

该模块是对handler模块的极简封装，提供对外接口。
"""

import os
import sys

# 确保项目根目录在Python路径中
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 直接导入handler中的功能
from RAGFlow_mcp.handler import handle_user_query, list_assistant


def RAGFlow_chat(query: str) -> str:
    """
    处理用户查询，返回回答

    Args:
        query (str): 用户查询

    Returns:
        str: 回答内容
    """
    return handle_user_query(query)


def get_assistants() -> str:
    """
    获取所有可用的助手列表

    Returns:
        str: 助手列表信息
    """
    return list_assistant()


# 测试代码
if __name__ == "__main__":
    # 测试获取助手列表
    print("助手列表:", get_assistants())

    # 测试直接提问
    query = "瓦尔登湖在哪？"
    print(f"问题: {query}")
    print(f"回答: {RAGFlow_chat(query)}")

    # 测试指定助手回答问题
    query = "请企业知识助手告诉我如何报销经费？"
    print(f"问题: {query}")
    print(f"回答: {RAGFlow_chat(query)}")