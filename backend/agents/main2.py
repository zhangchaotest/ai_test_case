#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：main2.py
@Author  ：张超
@Date    ：2025/12/17 17:57
@Desc    ：
"""
# main.py
import asyncio
import sys
import os

# 1. 导入工厂和 Agent 定义
from my_agents import create_coder_agent, create_reviewer_agent
# 2. 导入团队协作组件
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.ui import Console

# --- 解决中文编码问题 ---
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


# --- 配置代理 (如果需要) ---
# os.environ["http_proxy"] = "http://127.0.0.1:7890"
# os.environ["https_proxy"] = "http://127.0.0.1:7890"

# async def main():
#     # 1. 创建不同的 Agent
#     coder = create_coder_agent()
#     reviewer = create_reviewer_agent()
#
#     # 2. 定义终止条件 (当某人说 "TERMINATE" 时停止对话)
#     # 或者设置 max_turns 来限制对话轮数
#     termination = TextMentionTermination("TERMINATE")
#
#     # 3. 创建轮询团队 (RoundRobinGroupChat)
#     # participants: 参与者列表，他们会按顺序发言
#     # termination_condition: 什么时候停止对话
#     team = RoundRobinGroupChat(
#         participants=[coder, reviewer],
#         termination_condition=termination
#     )
#
#     print("--- 🚀 团队协作开始 ---")
#
#     # 4. 运行团队任务
#     # 任务描述：要求 Coder 写代码，然后 Reviewer 审查，直到 Reviewer 觉得没问题
#     task = """
#     请编写一个 Python 函数来检查一个字符串是否是回文。
#     写完后请 Reviewer 进行审查。如果代码没问题，Reviewer 请在回复的最后加上 'TERMINATE'。
#     """
#
#     # 使用 Console 运行，可以看到完整的对话流
#     await Console(team.run_stream(task=task))