import asyncio
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
# 导入你之前的定义
from backend.agents.llm_factory import get_gemini_client
from backend.models.db_tools import save_verified_test_case
from autogen_agentchat.ui import Console  # <--- 1. 引入这个

# 这里复用你之前写的 create_test_generator 和 create_test_reviewer
# 为了代码简洁，我假设它们定义在这个文件里或从 my_agents 导入
from autogen_agentchat.agents import AssistantAgent

gemini_client = get_gemini_client()


def create_test_generator():
    # ... (复制你之前的 Generator 定义) ...
    return AssistantAgent(
        name="test_generator",
        model_client=gemini_client,
        system_message="""
        你是一个测试专家。请生成 JSON 格式的步骤 (step_id, action, expected)。
        同时必须设定 priority (P0-P2) 和 case_type (Functional/Negative/Boundary)。
        不要输出 markdown 代码块，直接输出结构化信息。
        """
    )


def create_test_reviewer():
    # ... (复制你之前的 Reviewer 定义) ...
    return AssistantAgent(
        name="test_reviewer",
        model_client=gemini_client,
        tools=[save_verified_test_case],  # 工具需要引入 db_tools
        system_message="""
        你是测试组长。审查用例。
        如果通过，调用 save_verified_test_case 保存。
        保存完回复 TERMINATE。
        """
    )


async def run_generation_task(req_id: int, feature_name: str, desc: str):
    """触发 AutoGen 流程"""
    generator = create_test_generator()
    reviewer = create_test_reviewer()

    termination = TextMentionTermination("TERMINATE")
    team = RoundRobinGroupChat([generator, reviewer], termination_condition=termination, max_turns=8)

    task_prompt = f"""
    【任务】为功能点编写测试用例并入库。
    功能ID: {req_id}
    功能名称: {feature_name}
    描述: {feature_name}

    注意：保存时 requirement_id 必须为 {req_id}。
    """

    # 运行
    await Console(team.run_stream(task=task_prompt))
    print(f"--- 处理结束 ---")

    return True