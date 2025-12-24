# backend/agents/requirement_agent.py

import json
import traceback

from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.agents import AssistantAgent

# 导入项目模块
from backend.agents.llm_factory import get_gemini_client
from backend.database.requirement_db import save_breakdown_item
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

# 🔥 更新工具映射，对应 save_breakdown_item
TOOL_NAMES_MAP = {
    "save_breakdown_item": "📝 需求拆解入库"
}


# -------------------------------------------------------------------------
# Agent 定义区域
# -------------------------------------------------------------------------

def create_requirement_analyst():
    """
    创建需求分析师 Agent
    不需要任何工具 (tools=[])，它只负责思考和输出 JSON
    """
    return AssistantAgent(
        name="req_analyst",
        model_client=gemini_client,
        # tools=[], # 显式移除工具，防止它越权保存
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
            - "source_content": 【重要！！！】必须摘录原文。
                - 请从用户的原始需求中，复制出与该功能点直接相关的【原文句子】。
                - 如果是推导出来的需求，请填入推导依据。
                - **绝对不允许为空字符串！**

            请确保拆解粒度适中，不要太粗也不要太细。
            请以 JSON 代码块格式输出，例如：
            ```json
            [
              {
                "module_name": "...",
                "source_content": "原文：用户可以通过微信登录...",
                ...
              }
            ]
            ```
            【注意事项】
            输出完 JSON 后，你的任务就结束了。
            请等待 Reviewer 进行评审和入库操作。
            
            【🚨 绝对禁令】
            **输出完 JSON 后，你的任务就彻底结束了。**
            **严禁** 回复类似“收到ID”、“任务完成”、“请提供下一个”之类的废话。
            **严禁** 在 Reviewer 操作完成后再次发言。
            如果不知道说什么，就保持沉默或输出 TERMINATE。
        """
    )


# --- 2. 创建 Agent (Reviewer) ---
def create_requirement_reviewer():
    return AssistantAgent(
        name="req_reviewer",
        model_client=gemini_client,
        tools=[save_breakdown_item],  # 🔥 只有 Reviewer 拥有入库到拆解表的权限
        system_message="""
            你是一个严格的需求质量评审员。

            【工作流】
            1. 接收 Analyst 发来的 JSON 数据。
            2. 检查数据质量（完整性、source_content 是否存在）。
            3. 调用工具 `save_breakdown_item` 将数据存入【需求拆解表】。

            【🚨 终止条件 - 优先级最高】
            **一旦你看到工具返回了包含 "ID:" 的结果：**
            **必须立刻、马上回复单词：TERMINATE**
            
            不要解释，不要总结，不要说“已入库”，直接说 TERMINATE。
            阻止 Analyst 继续发言。
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
            max_turns=5
        )

        task_prompt = f"""
        【需求分析任务】
        项目ID: {project_id}

        【原始需求内容】
        {raw_req}

        【补充指令】
        {instruction}

        请 Analyst 先拆解，然后 Reviewer 进行评审并入库。
        注意：调用 save_breakdown_item 时，务必将 project_id={project_id} 和 source_content (原始需求摘要) 填入。
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