import asyncio
import json

from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
# 导入你之前的定义
from backend.agents.llm_factory import get_gemini_client
from backend.models.db_tools import save_verified_test_case
from autogen_agentchat.ui import Console  # <--- 1. 引入这个
from autogen_agentchat.messages import TextMessage, ToolCallRequestEvent, ToolCallExecutionEvent

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


async def run_stream_task(req_id: int, feature_name: str, desc: str):
    """
    生成器函数：流式返回 AutoGen 的运行日志
    """
    generator = create_test_generator()
    reviewer = create_test_reviewer()

    termination = TextMentionTermination("TERMINATE")
    team = RoundRobinGroupChat([generator, reviewer], termination_condition=termination, max_turns=12)

    task_prompt = f"""
    【任务】为功能点编写测试用例并入库。
    功能ID: {req_id}
    功能名称: {feature_name}
    描述: {desc}
    注意：保存时 requirement_id 必须为 {req_id}。
    """

    print(f"🚀 [Stream Start] 开始处理需求 {req_id}")

    try:
        # 迭代 AutoGen 的流式输出
        async for message in team.run_stream(task=task_prompt):
            output_data = {}

            # -------------------------------------------------
            # 1. 文本消息 (Agent 的思考和对话)
            # -------------------------------------------------
            if isinstance(message, TextMessage):
                print(f"   -> [Text] {message.source}: {message.content[:20]}...")

                # 如果是结束指令，发送 finish 事件
                if "TERMINATE" in message.content:
                    yield format_sse("finish", "生成结束")
                    break  # 退出循环

                output_data = {
                    "type": "log",
                    "source": message.source,
                    "content": message.content
                }

            # -------------------------------------------------
            # 2. 工具调用请求 (Reviewer 决定调用工具)
            # 🔥🔥🔥 修复点：属性名改为了 .tool_calls
            # -------------------------------------------------
            elif isinstance(message, ToolCallRequestEvent):
                print(f"   -> [Tool Call Request] {message.source}")

                # 获取工具名称 (加个 try 防止列表为空)
                try:
                    # 旧版本是 model_client_tool_calls，新版本是 tool_calls
                    tool_name = message.tool_calls[0].function.name
                except (AttributeError, IndexError):
                    tool_name = "Unknown Tool"

                output_data = {
                    "type": "tool_call",
                    "source": message.source,
                    "content": f"正在调用工具: {tool_name}..."
                }

            # -------------------------------------------------
            # 3. 工具执行结果 (数据库操作返回)
            # -------------------------------------------------
            elif isinstance(message, ToolCallExecutionEvent):
                print(f"   -> [Tool Result]")

                # 获取执行结果
                try:
                    result = message.tool_call_results[0].content
                except (AttributeError, IndexError):
                    result = "执行完成 (无返回内容)"

                output_data = {
                    "type": "tool_result",
                    "source": "System",
                    "content": f"执行结果: {str(result)}"
                }

            # -------------------------------------------------
            # 发送 SSE 数据块
            # -------------------------------------------------
            if output_data:
                # 必须转成 json 字符串，并用 utf-8 编码，防止中文乱码问题
                json_str = json.dumps(output_data, ensure_ascii=False)
                yield format_sse("message", json_str)

    except Exception as e:
        print(f"❌ [Stream Error] {e}")
        # 将错误信息发给前端显示
        err_data = json.dumps({
            "type": "log",
            "source": "System Error",
            "content": f"流式生成出错: {str(e)}"
        }, ensure_ascii=False)
        yield format_sse("message", err_data)


def format_sse(event: str, data: str):
    """辅助函数：格式化为 SSE 标准字符串"""
    # 移除换行符，防止破坏 SSE 协议格式
    clean_data = data.replace("\n", "\\n")
    return f"event: {event}\ndata: {clean_data}\n\n"
