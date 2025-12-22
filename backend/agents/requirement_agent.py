#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：requirement_agent.py
@Author  ：张超
@Date    ：2025/12/22 09:19
@Desc    ：
"""
# backend/agents/requirement_agent.py

import json
import traceback

from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.agents import AssistantAgent

# 导入项目模块
from backend.agents.llm_factory import get_gemini_client
from backend.database.requirement_db import save_analyzed_point
from backend.utils.stream_utils import AutoGenStreamProcessor, format_sse

# -------------------------------------------------------------------------
# 配置区域
# -------------------------------------------------------------------------

gemini_client = get_gemini_client()

# Agent 显示名称映射
AGENT_NAMES_MAP = {
    "req_analyst": "🧐 需求分析师",
    "req_reviewer": "✅ 流程确认"
}

# 工具显示名称映射
TOOL_NAMES_MAP = {
    "save_analyzed_point": "📝 功能点拆解入库"
}


# -------------------------------------------------------------------------
# Agent 定义区域
# -------------------------------------------------------------------------

def create_requirement_analyst():
    """
    创建需求分析师 Agent
    拥有功能点入库权限
    """
    return AssistantAgent(
        name="req_analyst",
        model_client=gemini_client,
        tools=[save_analyzed_point],  # 绑定需求保存工具
        system_message="""
        你是一个资深产品经理和需求分析师。

        【任务目标】
        读取用户的原始需求文本（可能包含补充指令），将其拆解为细粒度的“功能点”。

        【执行步骤】
        1. 分析用户输入的原始需求。
        2. 将大段文本拆解为独立的、可测试的功能点 (Feature)。
        3. 对每个功能点，调用工具 `save_analyzed_point` 进行保存。

        【工具参数要求】
        - project_id: (从任务中获取)
        - module_name: 根据功能归类 (如：用户中心、订单模块)
        - feature_name: 功能名称 (简练)
        - description: 详细描述和验收标准
        - priority: P0/P1/P2
        - source_content: (填入用户输入的原始需求片段，用于追溯)

        【结束】
        所有功能点拆解并保存完毕后，回复 TERMINATE。
        """
    )


# -------------------------------------------------------------------------
# 主业务流程 (Requirement Analysis)
# -------------------------------------------------------------------------

async def run_requirement_analysis_stream(project_id: int, raw_req: str, instruction: str = ""):
    """
    需求分析流式任务入口

    :param project_id: 项目ID
    :param raw_req: 原始需求文本
    :param instruction: 用户补充指令
    """
    print(f"🚀 [Analysis Stream] Project: {project_id}")

    # 发送开场白
    yield format_sse("message", json.dumps({
        "type": "log", "source": "系统", "content": "正在启动需求分析引擎..."
    }, ensure_ascii=False))

    try:
        # --- 1. 创建 Agent ---
        analyst = create_requirement_analyst()

        # 创建一个简单的 Reviewer，只负责确认结束，不执行具体工作
        # 也可以使用 UserProxy，但在流式输出中 AssistantAgent 表现更可控
        reviewer = AssistantAgent(
            name="req_reviewer",
            model_client=gemini_client,
            system_message="你负责确认分析师是否已完成所有拆解。如果完成，回复 TERMINATE。"
        )

        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat(
            [analyst, reviewer],
            termination_condition=termination,
            max_turns=10
        )

        # --- 2. 构建 Prompt ---
        task_prompt = f"""
        【需求分析任务】
        项目ID: {project_id}

        【原始需求内容】
        {raw_req}

        【补充指令】
        {instruction}

        请开始拆解功能点并入库。
        注意：调用 save_analyzed_point 时，务必将 project_id={project_id} 和 source_content (原始需求摘要) 填入。
        """

        # --- 3. 初始化通用流式处理器 ---
        processor = AutoGenStreamProcessor(
            agent_names=AGENT_NAMES_MAP,
            tool_names=TOOL_NAMES_MAP
        )

        # --- 4. 启动流并移交处理 ---
        async for sse in processor.process_stream(team.run_stream(task=task_prompt)):
            yield sse

        print("✅ [DEBUG] run_requirement_analysis_stream 执行完毕")

    except Exception as e:
        traceback.print_exc()
        print(f"❌ [FATAL ERROR] 需求分析崩溃: {e}")

        err_json = json.dumps({
            "type": "log", "source": "后端崩溃", "content": f"系统错误: {str(e)}"
        }, ensure_ascii=False)
        yield format_sse("message", err_json)
        yield format_sse("finish", "{}")