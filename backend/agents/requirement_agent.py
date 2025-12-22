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
from backend.database.requirement_db import save_analyzed_point,save_breakdown_item
from backend.utils.stream_utils import AutoGenStreamProcessor, format_sse

# -------------------------------------------------------------------------
# 配置区域
# -------------------------------------------------------------------------

gemini_client = get_gemini_client()

# Agent 显示名称映射
AGENT_NAMES_MAP = {
    "req_analyst": "🧐 需求分析师",
    "req_reviewer": "⚖️ 质量评审员"
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
            你是一个资深产品经理。
            
            【任务】
            阅读用户的原始需求，将其拆解为独立的、可开发测试的功能点。
            
            【输出要求】
            请输出一个 JSON 列表，包含以下字段：
            - module_name: 所属模块
            - feature_name: 功能名称
            - description: 功能详细描述
            - acceptance_criteria: 验收标准 (最重要的字段，列出1,2,3点)
            - requirement_type: 新增/优化/Bug
            - priority: P0/P1/P2
            - source_snippet: 对应的原始需求片段
            
            请确保拆解粒度适中，不要太粗也不要太细。
            请以 JSON 代码块格式输出，例如：
            ```json
            [ ... ]
            ```
        """
    )


# --- 2. 创建 Agent (Reviewer) ---
def create_requirement_reviewer():
    return AssistantAgent(
        name="req_reviewer",
        model_client=gemini_client,
        tools=[save_breakdown_item],  # 🔥 只有 Reviewer 有权限入库
        system_message="""
        你是一个严格的需求质量评审员。

        【流程】
        1. 接收 Analyst 输出的功能点列表。
        2. 逐条评估每个功能点：
           - 描述是否清晰？
           - 验收标准是否可测？
           - 拆分是否合理？
        3. 为每个功能点打分 (confidence_score, 0.0-1.0)。

        4. **调用工具** `save_breakdown_item` 将评估通过（或需人工确认）的功能点存入数据库。
           - 调用 `save_breakdown_item` 保存。
           - **注意**：你不需要设置 review_status，系统会默认设为 'Pending' 等待人工审批。
           - 请务必填好 confidence_score 和 review_comments（你的评审意见）。

        5. 全部处理完毕后，回复 TERMINATE。
        """
    )

# -------------------------------------------------------------------------
# 主业务流程 (Requirement Analysis)
# -------------------------------------------------------------------------

# --- 3. 流式任务入口 ---
async def run_requirement_analysis_stream(project_id: int, raw_req: str, instruction: str = ""):
    print(f"🚀 [Req Analysis] Project={project_id}")

    yield format_sse("message", json.dumps({
        "type": "log", "source": "系统", "content": "正在初始化双智能体分析流程 (Analyst -> Reviewer)..."
    }, ensure_ascii=False))

    try:
        analyst = create_requirement_analyst()
        reviewer = create_requirement_reviewer()

        # 两人协作，轮流发言
        team = RoundRobinGroupChat(
            [analyst, reviewer],
            termination_condition=TextMentionTermination("TERMINATE"),
            max_turns=12
        )

        task_prompt = f"""
        【需求分析任务】
        项目ID: {project_id}

        【原始需求内容】
        {raw_req}

        【补充指令】
        {instruction}

        请 Analyst 先拆解，然后 Reviewer 进行评审并入库。
        注意：入库时必须带上 project_id={project_id}。
        """

        processor = AutoGenStreamProcessor(
            agent_names=AGENT_NAMES_MAP,
            tool_names=TOOL_NAMES_MAP
        )

        raw_stream = team.run_stream(task=task_prompt)
        async for sse in processor.process_stream(raw_stream):
            yield sse

    except Exception as e:
        traceback.print_exc()
        yield format_sse("message",
                         json.dumps({"type": "log", "source": "系统错误", "content": str(e)}, ensure_ascii=False))
        yield format_sse("finish", "{}")