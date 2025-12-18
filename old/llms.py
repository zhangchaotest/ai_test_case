#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast
@File    ：llms.py
@Author  ：张超
@Date    ：2025/12/15 13:33
@Desc    ：
"""
import sys
import os

os.environ["GRPC_DNS_RESOLVER"] = "native"
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"
os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = ""
os.environ["GRPC_VERBOSITY"] = "ERROR"

os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from llama_index.llms.deepseek import DeepSeek
from llama_index.llms.gemini import Gemini
# from autogen_ext.models.gemini import GeminiChatCompletionClient


deepseek_llm = DeepSeek(
    model="deepseek-reasoner",
    api_key=os.getenv("DEEPSEEK_API_KEY")
)
gemini_llm = Gemini(
    model="gemini-3-pro-preview",
    api_key=os.getenv("GEMINI_API_KEY"),
    transport="rest"
)

# def gemini():
#     client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
#     response = client.models.generate_content(
#         model="gemini-3-pro-preview",
#         contents = '什么是软件测试'
#     )
#     return response


if __name__ == '__main__':
    pass
    # t = gemini()
    # print(t)
