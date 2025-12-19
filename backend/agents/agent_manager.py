import asyncio
import json
import re

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


AGENT_NAMES = {
    "test_generator": "✍️ 用例设计专家",
    "test_reviewer": "🧐 质量评审组长",
    "user": "用户指令"
}

TOOL_NAMES = {
    "save_verified_test_case": "💾 数据库入库"
}


async def run_stream_task(req_id: int, feature_name: str, desc: str):
    generator = create_test_generator()
    reviewer = create_test_reviewer()
    termination = TextMentionTermination("TERMINATE")

    # 增加轮次，防止截断
    team = RoundRobinGroupChat([generator, reviewer], termination_condition=termination, max_turns=20)

    task_prompt = f"""
    【任务】为功能点编写测试用例并入库。
    功能ID: {req_id}
    功能名称: {feature_name}
    描述: {desc}
    注意：保存时 requirement_id 必须为 {req_id}。
    """

    print(f"🚀 [Stream] 开始处理 ID: {req_id}")

    count_generated = 0
    count_saved = 0

    try:
        async for message in team.run_stream(task=task_prompt):
            output_data = None

            # 转为字典，方便统一处理
            msg_dict = message.model_dump()

            # -------------------------------------------------
            # 场景 1: Agent 文本消息
            # -------------------------------------------------
            if isinstance(message, TextMessage):
                if "TERMINATE" in message.content or message.source == "user":
                    continue

                source_name = AGENT_NAMES.get(message.source, message.source)
                content_display = "正在思考..."

                # 如果文本里包含标题，也可以作为补充显示
                if message.source == "test_generator":
                    titles = re.findall(r'["\']case_title["\']\s*:\s*["\'](.*?)["\']', message.content, re.IGNORECASE)
                    if titles:
                        content_display = f"正在构思用例: {titles[0]} 等..."
                    else:
                        content_display = "正在解析需求并构建 JSON..."

                output_data = {"type": "log", "source": source_name, "content": content_display}

            # -------------------------------------------------
            # 场景 2: 工具调用请求 (🔥 针对你的日志结构重写)
            # -------------------------------------------------
            elif isinstance(message, ToolCallRequestEvent):
                # 1. 获取工具调用列表
                # 根据你的日志，数据在 'content' 字段里，且是列表
                calls = []

                # 优先检查 tool_calls (新版标准)
                if msg_dict.get('tool_calls'):
                    calls = msg_dict['tool_calls']
                # 其次检查 content (你的日志结构)
                elif isinstance(msg_dict.get('content'), list):
                    calls = msg_dict['content']

                if calls:
                    tool_names = []
                    generated_titles = []

                    for call in calls:
                        # --- A. 提取工具名 ---
                        # 你的日志里是 {'name': 'save_verified_test_case', ...}
                        # 标准版可能是 {'function': {'name': ...}}
                        raw_name = "Unknown"
                        if isinstance(call, dict):
                            raw_name = call.get('name') or call.get('function', {}).get('name')
                        elif hasattr(call, 'function'):
                            raw_name = call.function.name

                        friendly_name = TOOL_NAMES.get(raw_name, raw_name)
                        tool_names.append(friendly_name)

                        # --- B. 提取参数中的标题 (用于统计生成数) ---
                        # 参数通常在 'arguments' 字段，是 JSON 字符串
                        try:
                            args_str = call.get('arguments', '{}')
                            args = json.loads(args_str)
                            if 'case_title' in args:
                                generated_titles.append(args['case_title'])
                        except:
                            pass

                    # 更新统计
                    batch_count = len(generated_titles)
                    count_generated += batch_count

                    # 构造显示文本
                    unique_names = list(set(tool_names))
                    display_text = f"正在调用: {','.join(unique_names)}"
                    if batch_count > 0:
                        # 如果提取到了标题，显示出来
                        title_preview = "、".join(generated_titles[:2])
                        if batch_count > 2: title_preview += f" 等 {batch_count} 个"
                        display_text += f"\n📦 包含用例: {title_preview}"

                    output_data = {
                        "type": "tool_call",
                        "source": "系统调用",
                        "content": display_text
                    }
                else:
                    print(f"⚠️ [DEBUG] 未能解析工具列表: {msg_dict}")

            # -------------------------------------------------
            # 场景 3: 工具执行结果 (统计入库数)
            # -------------------------------------------------
            elif isinstance(message, ToolCallExecutionEvent):
                # 获取结果列表
                results = msg_dict.get('tool_call_results') or []

                # 你的日志里没有展示这部分的详细结构，通常是在 tool_call_results 或者是 content
                if not results and isinstance(msg_dict.get('content'), list):
                    results = msg_dict.get('content')

                success_ids = []

                for res in results:
                    # 结果内容可能在 content 字段
                    if isinstance(res, dict):
                        res_content = str(res.get('content', ''))
                    else:
                        res_content = str(getattr(res, 'content', ''))

                    if "ID:" in res_content:
                        # 提取 ID
                        match = re.search(r'ID:\s*(\d+)', res_content)
                        if match:
                            success_ids.append(match.group(1))

                success_count = len(success_ids)
                count_saved += success_count

                if success_count > 0:
                    id_str = ",".join(success_ids)
                    output_data = {
                        "type": "tool_result",
                        "source": "数据库",
                        "content": f"✅ 成功入库 {success_count} 条 (ID: {id_str})"
                    }
                else:
                    # 如果没找到 ID，打印一下原始返回方便调试
                    first_res = str(results[0]) if results else "无数据"
                    output_data = {
                        "type": "tool_result",
                        "source": "数据库",
                        "content": f"⚠️ 执行完成 (未检测到ID返回)"
                    }

            if output_data:
                yield format_sse("message", json.dumps(output_data, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Error: {e}")
        yield format_sse("message", json.dumps({
            "type": "log", "source": "系统错误", "content": str(e)
        }, ensure_ascii=False))

    # --- 📊 最终报表 ---
    summary_data = json.dumps({
        "generated": count_generated,
        "saved": count_saved
    }, ensure_ascii=False)

    yield format_sse("finish", summary_data)


def format_sse(event: str, data: str):
    """辅助函数：格式化为 SSE 标准字符串"""
    # 移除换行符，防止破坏 SSE 协议格式
    clean_data = data.replace("\n", "\\n")
    return f"event: {event}\ndata: {clean_data}\n\n"

