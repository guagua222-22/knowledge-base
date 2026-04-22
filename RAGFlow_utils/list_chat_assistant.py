import os

from ragflow_sdk import RAGFlow
from dotenv import load_dotenv

import logging

logger = logging.getLogger(__name__)


def get_assistant_list():
    """
    获取RAGFlow中的所有聊天助手信息，并返回组合后的字符串

    Returns:
        str: 包含所有助手信息的字符串，每个助手一行
    """
    # 加载环境变量（从.env文件）
    load_dotenv()

    # 获取环境变量并检查有效性
    base_url = os.getenv("RAGFLOW_API_URL")
    api_key = os.getenv("RAGFLOW_API_KEY")

    # 检查环境变量是否缺失
    if not base_url or not api_key:
        error_msg = "环境变量RAGFLOW_API_URL或RAGFLOW_API_KEY未设置"
        logger.error(error_msg)
        return error_msg

    # 用列表收集结果（比字符串拼接更高效）
    result_lines = []

    try:
        # 初始化RAGFlow实例
        rag_flow = RAGFlow(api_key=api_key, base_url=base_url)

        # 遍历所有助手信息并格式化
        for assistant in rag_flow.list_chats():
            kb_names = [
                dataset['name']
                for dataset in assistant.datasets
                if isinstance(dataset, dict) and isinstance(assistant.datasets, list) and 'name' in dataset
            ] if hasattr(assistant, 'datasets') else []
            # 格式化知识库名称（无则显示"无"）
            kb_names_str = "、".join(kb_names) if kb_names else "无"

            # 检查助手是否有name和description属性（避免属性不存在报错）
            assistant_name = getattr(assistant, 'name', '未知名称')
            assistant_desc = getattr(assistant, 'description', '无描述')

            # 添加到结果列表
            result_lines.append(f"助手名称：{assistant_name}； 功能介绍：{assistant_desc}； 知识库：{kb_names_str}")

        # 用换行符连接所有行（若为空则返回空字符串）
        return "\n".join(result_lines)
    # 异常信息
    except Exception as e:
        error_msg = f"获取助手列表时出错: {str(e)}"
        logger.error(error_msg, exc_info=True)  # 记录详细异常堆栈
        return error_msg


# 如果直接运行此脚本，则打印结果
if __name__ == "__main__":
    assistants_info = get_assistant_list()
    print(assistants_info)
