# -*- coding: UTF-8 -*-
"""
项目全局配置文件
该文件负责加载环境变量并定义系统的核心配置参数。
主要包括：
1. LLM (大语言模型) 配置：API Key、Endpoint 等
2. Dify 知识库配置：API Key、Endpoint、检索数量限制
3. 系统运行参数：调试模式、最大生成数量等
"""

import os
from dotenv import load_dotenv

# 加载环境变量
# 明确指定 .env 文件的路径，确保在不同目录下运行脚本时都能正确加载
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# =========================================================
# LLM 模型配置
# =========================================================
LLM_CONFIG = {
    # 默认使用的模型类型，可选值：gemini, openai, claude
    "default_model": "gemini",
    
    # 各个模型的具体配置
    "models": {
        "gemini": {
            "api_key": os.getenv("GEMINI_API_KEY"),
            "endpoint": "https://generativelanguage.googleapis.com/v1"
        },
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "endpoint": "https://api.openai.com/v1"
        },
        "claude": {
            "api_key": os.getenv("CLAUDE_API_KEY"),
            "endpoint": "https://api.anthropic.com/v1"
        }
    }
}

# =========================================================
# Dify 知识库配置
# =========================================================
DIFY_CONFIG = {
    # Dify API Key，优先从环境变量获取，否则使用默认值
    "api_key": os.getenv("DIFY_API_KEY", "app-g1VTEWzy7anvxjnm0lvmlVFq"),
    
    # Dify 服务端点
    "endpoint": os.getenv("DIFY_ENDPOINT", "https://dify-test.lbxdrugs.com"),
    
    # 知识检索时的最大返回条数
    "retrieve_limit": int(os.getenv("DIFY_RETRIEVE_LIMIT", "3"))
}

# =========================================================
# 系统运行配置
# =========================================================
SYSTEM_CONFIG = {
    # 是否开启调试模式，开启后会输出更多日志
    "debug_mode": True,
    
    # 单次请求最大生成的测试用例数量限制
    "max_case_count": 50,
    
    # 智能体对话的最大交互轮次，防止死循环
    "max_turns": 10
}
