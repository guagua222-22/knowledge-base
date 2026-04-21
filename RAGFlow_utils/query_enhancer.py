#!/usr/bin/env python
"""
查询增强处理模块 - 简化版

解决代词指代和上下文依赖问题，提高RAG检索效果
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser


def enhance_query(query: str, history: str = "") -> str:
    """
    增强用户查询

    Args:
        query: 原始查询
        history: 对话历史

    Returns:
        增强后的查询
    """
    # 如果没有历史记录，直接返回原查询
    if not history:
        return query

    try:
        # 加载环境变量
        load_dotenv()

        # 创建提示词模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你的任务是将用户的问题转换为更适合知识库检索的查询语句。

分析对话历史和当前问题，解决代词指代问题：
- 将"他"、"她"、"它"、"这个"、"那个"等代词替换为具体指代的实体
- 整合必要的上下文信息
- 保持查询简洁明确

请直接返回增强后的查询语句，不要添加任何解释。"""),
            ("human", "对话历史：{history}\n\n原始问题：{query}\n\n增强查询：")
        ])

        # 创建LLM
        llm = ChatOpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            model=os.getenv("LLM_QWEN2.5"),
            base_url=os.getenv("DASHSCOPE_BASE_URL"),
            temperature=0.1
        )

        # 创建处理链 Runnable
        chain = prompt | llm | StrOutputParser()

        # 执行查询增强
        result = chain.invoke({"query": query, "history": history})
        return result.strip()

    except:
        return query


# 测试代码
if __name__ == "__main__":
    test_cases = [
        ("他是谁？", "用户: 张三是公司的CTO吗？\n助手: 是的，张三是我们公司的首席技术官。"),
        ("它的功能是什么？", "用户: 智能客服系统上线了\n助手: 是的，智能客服系统已上线。"),
        ("今天天气怎么样？", "")
    ]

    for query, history in test_cases:
        result = enhance_query(query, history)
        print(f"原始: {query}")
        print(f"增强: {result}")
        print("-" * 30) 