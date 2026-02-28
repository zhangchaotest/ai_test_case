# 项目配置文件
import os
from dotenv import load_dotenv

# 加载环境变量（明确指定.env文件路径）
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# LLM 模型配置
LLM_CONFIG = {
    "default_model": "gemini",  # 选择使用的默认模型：gemini, openai, claude
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

# Dify 知识库配置
DIFY_CONFIG = {
    "api_key": os.getenv("DIFY_API_KEY", "app-g1VTEWzy7anvxjnm0lvmlVFq"),
    "endpoint": os.getenv("DIFY_ENDPOINT", "https://dify-test.lbxdrugs.com"),
    "retrieve_limit": int(os.getenv("DIFY_RETRIEVE_LIMIT", "3"))
}

# 系统配置
SYSTEM_CONFIG = {
    "debug_mode": True,  # 是否开启调试模式
    "max_case_count": 50,  # 最大生成用例数量
    "max_turns": 10  # 智能体最大交互轮次
}
