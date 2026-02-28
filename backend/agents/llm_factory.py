#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
LLM 工厂模块
负责创建和配置大语言模型客户端 (如 Google Gemini, OpenAI 等)。
"""

import os
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def get_gemini_client(model_name: str = "gemini-3-pro-preview", temperature: float = 0.7):
    """
    工厂函数：创建一个配置好连接 Google Gemini 的 ModelClient。
    
    :param model_name: 模型名称，默认为 "gemini-3-pro-preview"
    :param temperature: 温度参数，控制生成的随机性 (0.0 - 1.0)
    :return: 配置好的 OpenAIChatCompletionClient 实例
    """
    # 获取 API Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ [LLM Factory] 警告: 未找到 GEMINI_API_KEY")

    print(f"🔌 [LLM Factory] 正在初始化模型: {model_name}...")

    try:
        # 创建客户端
        # 使用 OpenAIChatCompletionClient 适配 Gemini 的 OpenAI 兼容接口
        client = OpenAIChatCompletionClient(
            model=model_name,
            api_key=api_key,
            # 指向 Google 的 OpenAI 兼容接口
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",

            # 🔥 必须包含 model_info，否则 AutoGen 可能报错或无法正确识别模型能力
            model_info={
                "vision": True,             # 支持视觉能力
                "function_calling": True,   # 支持函数调用
                "json_output": True,        # 支持 JSON 输出模式
                "structured_output": True,  # 支持结构化输出
                "family": "gemini"          # 模型家族标识
            },

            temperature=temperature,
            # 设置超时时间，防止网络波动导致断连
            timeout=120
        )
        return client
    except Exception as e:
        print(f"❌ [LLM Factory] 初始化失败: {e}")
        raise e


if __name__ == "__main__":
    pass
