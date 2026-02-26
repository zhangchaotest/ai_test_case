#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：llm_factory.py
@Author  ：张超
@Date    ：2025/12/17 16:14
@Desc    ：
"""

import os
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def get_gemini_client(model_name: str = "gemini-3-pro-preview", temperature: float = 0.7):
    """
    工厂函数：创建一个配置好连接 Google Gemini 的 ModelClient。
    """
    """
        返回配置好的 Gemini 客户端
        """
    # 获取 Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ [LLM Factory] 警告: 未找到 GEMINI_API_KEY")

    print(f"🔌 [LLM Factory] 正在初始化模型: {model_name}...")

    try:
        # 创建客户端
        client = OpenAIChatCompletionClient(
            model=model_name,
            api_key=api_key,
            # 指向 Google 的 OpenAI 兼容接口
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",

            # 🔥 2. 必须包含 model_info (防止报错 model_info is required)
            model_info={
                "vision": True,
                "function_calling": True,
                "json_output": True,
                "structured_output": True,  # 🔥 加上这个由 False 改为 True 或加上，消除 Warning
                "family": "gemini"
            },

            temperature=temperature,
            # 防止网络波动导致断连
            timeout=120
        )
        return client
    except Exception as e:
        print(f"❌ [LLM Factory] 初始化失败: {e}")
        raise e


if __name__ == "__main__":
    pass
