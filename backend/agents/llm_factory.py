#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：llm_factory.py
@Author  ：张超
@Date    ：2025/12/17 16:14
@Desc    ：
"""
# llm_factory.py
import os
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_gemini_client(model_name: str = "gemini-3-pro-preview", temperature: float = 0.7):
    """
    工厂函数：创建一个配置好连接 Google Gemini 的 ModelClient。
    """
    # 1. 获取 Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("❌ 未找到环境变量 GEMINI_API_KEY，请检查 .env 文件")

    # 2. 创建并返回客户端
    # 这里封装了所有连接 Google 所需的特殊配置
    return OpenAIChatCompletionClient(
        model=model_name,
        api_key=api_key,
        # 关键：指向 Google 的 OpenAI 兼容接口
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        model_info={
            "vision": True,
            "function_calling": True,
            "json_output": True,
            "family": "gemini"
        },
        temperature=temperature,
    )