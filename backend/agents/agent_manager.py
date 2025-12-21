import json
import re
import traceback

from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console

# 导入项目模块
from backend.agents.llm_factory import get_gemini_client
from backend.utils.stream_utils import AutoGenStreamProcessor, format_sse
from backend.database.case_db import save_case,get_existing_case_titles
from backend.database.requirement_db import save_analyzed_point


# -------------------------------------------------------------------------
# 配置区域
# -------------------------------------------------------------------------

# 初始化 LLM 客户端
gemini_client = get_gemini_client()

# Agent 显示名称映射（用于前端展示中文名）
AGENT_NAMES_MAP = {
    "test_generator": "✍️ 用例设计专家",
    "test_reviewer": "🧐 质量评审组长",
    "user": "用户指令"
}

# 工具显示名称映射
TOOL_NAMES_MAP = {
    "save_case": "💾 数据库入库",
    "save_analyzed_point": "📝 功能点拆解入库" # 新增
}

# -------------------------------------------------------------------------
# Agent 定义区域
# -------------------------------------------------------------------------

def create_test_generator(target_count: int = 5):
    """
    创建用例生成 Agent (Generator)
    :param target_count: 目标生成数量
    :return:
    """
    print(f"🔍 [DEBUG] 正在创建 Generator Agent, 目标数量: {target_count}")  # <--- 埋点 1

    return AssistantAgent(
        name="test_generator",
        model_client=gemini_client,
        system_message=f"""
        你是一个专业的测试工程师。
        
        【任务目标】
        针对给定的功能点，计约 **{target_count}** 个测试用例。
        
        【生成策略】
        1. 优先覆盖：P0级核心功能 > 常见异常场景 > 关键边界值。
        2. **不要** 生成过于生僻或重复的用例（如网络断开、服务器物理损坏等）。
        3. 请一次性将这些用例的 JSON 结构输出完毕，不要分批次输出。
        
        【格式要求】
        输出标准 JSON 格式的步骤 (step_id, action, expected)。
        - "case_title": 用例标题 (必须有，且简洁明了)
        - "steps": 步骤列表 [{{"step_id": 1, "action": "...", "expected": "..."}}]
        - "priority": 优先级 (P0-P2)
        - "case_type": 类型 (功能测试用例/反向测试用例/边界值测试用例)

        不要输出 markdown 代码块，直接输出结构化信息。
        """
    )


def create_test_reviewer():
    """
    创建用例评审 Agent (Reviewer)
    拥有入库工具权限
    """

    return AssistantAgent(
        name="test_reviewer",
        model_client=gemini_client,
        tools=[save_case],  # 工具需要引入 db_tools
        system_message=f"""
        你是测试组长。
        
        【执行流程】
        1. 审查 Generator 生成的用例。
        2. 如果用例有效，**立即调用工具** `save_verified_test_case` 进行入库。
        3. **重要：** 当本批次用例全部保存完毕后，**必须** 立即回复关键词 "TERMINATE" 来结束任务。
        4. 不要在这个时候让 Generator 继续生成新的用例，直接结束。
        """
    )

# -------------------------------------------------------------------------
# 辅助解析函数
# -------------------------------------------------------------------------

def parse_generator_output(content: str):
    """
    [业务解析器] 专门解析 'test_generator' 的文本输出
    用于在前端日志中展示“正在构思xxx用例”
    """
    # 尝试提取 case_title 或 title 字段
    # 兼容 "case_title": "xxx" 和 "title": "xxx"
    titles = re.findall(r'["\'](case_)?title["\']\s*:\s*["\'](.*?)["\']', content, re.IGNORECASE)

    # re.findall 返回的是元组列表 [('case_', '标题1'), ('', '标题2')]，需要提取第二个元素
    clean_titles = [t[1] for t in titles]

    if clean_titles:
        count = len(clean_titles)
        title_str = "、".join(clean_titles[:2])
        if count > 2: title_str += f" 等 {count} 个"
        return f"正在构思用例：【{title_str}】"

    if len(content) > 50:
        return "正在解析需求并构建 JSON 数据..."

    return "正在构思测试场景..."

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

async def run_stream_task(req_id: int, feature_name: str, desc: str, target_count: int = 5, mode: str = "new"):
    """
    业务入口函数：组装 Team -> 启动流 -> 移交处理器

    :param req_id: 需求ID
    :param feature_name: 需求名称
    :param desc: 需求描述
    :param target_count: 目标生成数量
    :param mode: 'new' (全新生成) 或 'append' (追加生成)
    """
    print(f"🚀 [DEBUG] 进入 run_stream_task. ID={req_id}, Count={target_count}, Mode={mode}")

    # --- 1. 发送初始化系统通知 (SSE) ---
    start_info = {
        "type": "log",
        "source": "系统通知",
        "content": f"✅ 获取需求成功\n📌 需求标题：{feature_name}\n🎯 目标数量：{target_count} 条 ({'增量模式' if mode == 'append' else '全量模式'})"
    }
    yield format_sse("message", json.dumps(start_info, ensure_ascii=False))

    prepare_info = {
        "type": "log",
        "source": "系统通知",
        "content": "🚀 正在初始化智能体团队 (Generator & Reviewer)..."
    }
    yield format_sse("message", json.dumps(prepare_info, ensure_ascii=False))

    try:
        # --- 2. 根据模式构建 Prompt 上下文 ---
        existing_context = ""
        focus_instruction = "优先覆盖核心业务流程、P0级功能。"

        if mode == "append":
            # 增量模式：查出已有用例，防止重复
            existing_titles = get_existing_case_titles(req_id)
            existing_json = json.dumps(existing_titles, ensure_ascii=False)

            existing_context = f"""
            【已存在用例列表】
            数据库中已经有了以下用例，请**绝对不要重复**：
             {existing_json}
             """

            focus_instruction = """
             请专注于 **查漏补缺**：
             1. 重点补充：**异常场景**、**边界值**、**安全性**、**性能压力** 相关的用例。
             2. 避开已有的正常流程。
             """

        # --- 3. 动态配置轮次 ---
        # 假设每轮能生成 3-5 条，计算需要的最大轮次，防止截断
        dynamic_turns = max(6, int(target_count / 3) + 4)
        print(f"⚙️ [DEBUG] Team 组装完成，最大轮次: {dynamic_turns}")

        # --- 4. 组装 AutoGen Team ---
        generator = create_test_generator(target_count)
        reviewer = create_test_reviewer()
        termination = TextMentionTermination("TERMINATE")

        team = RoundRobinGroupChat(
            [generator, reviewer],
            termination_condition=termination,
            max_turns=dynamic_turns
        )

        task_prompt = f"""
        【任务】为功能点编写测试用例并入库。
        功能ID: {req_id}
        功能名称: {feature_name}
        描述: {desc}
        
        【当前模式】：{'🔥 增量补充模式' if mode == 'append' else '🚀 全新生成模式'}
        目标生成数量：**{target_count} 条左右**。
        
        {existing_context}
        
        【生成策略】
        {focus_instruction}
        
        【执行要求】
        1. 保存时 requirement_id 必须为 {req_id}。
        2. 目标生成数量：**{target_count} 条左右**。。
        3. 如果数量较多，你可以分多次（多轮对话）生成，每次生成 5 条，直到凑够数量。
        
        【重要执行指令】
        Generator，请立即开始工作！
        请先回复一句：“收到，正在为 [ID:{req_id}] 生成测试用例...”，然后紧接着输出 JSON 数据。
        **不要保持沉默！**

        """

        print(f"🚀 [Stream] 开始处理 ID: {req_id}")

        # --- 5. 初始化通用流式处理器 ---
        processor = AutoGenStreamProcessor(
            agent_names=AGENT_NAMES_MAP,
            tool_names=TOOL_NAMES_MAP,
            # 注册特定的解析逻辑
            custom_text_parsers={
                "test_generator": parse_generator_output
            }
        )
        # --- 6. 启动流并移交处理 ---
        # team.run_stream 返回的是原始迭代器，直接传给 processor 进行标准化处理
        raw_stream = team.run_stream(task=task_prompt)

        async for sse_event in processor.process_stream(raw_stream):
            yield sse_event

        print("✅ [DEBUG] run_stream_task 执行完毕")


    except Exception as e:
        # --- 7. 全局异常捕获 ---
        traceback.print_exc()
        print(f"❌ [FATAL ERROR] 业务逻辑层崩溃: {e}")

        # 发送错误消息给前端
        err_json = json.dumps({
            "type": "log",
            "source": "后端崩溃",
            "content": f"系统错误: {str(e)}"
        }, ensure_ascii=False)
        yield format_sse("message", err_json)

        # 发送空的结束信号，避免前端无限等待
        yield format_sse("finish", "{}")


# 定义需求分析 Agent
def create_requirement_analyst():
    return AssistantAgent(
        name="req_analyst",
        model_client=gemini_client,
        tools=[save_analyzed_point],  # 绑定新工具
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


# 2. 定义需求分析流式任务
async def run_requirement_analysis_stream(project_id: int, raw_req: str, instruction: str = ""):
    print(f"🚀 [Analysis Stream] Project: {project_id}")

    # 初始化
    analyst = create_requirement_analyst()
    # 这里不需要 Reviewer，分析师自己拆解即可，或者你可以加一个 Reviewer 来审核拆解质量
    # 为了简化，这里用单人模式或者自言自语模式，但 RoundRobin 需要至少2人，
    # 我们复用之前的 UserProxy 思想，或者创建一个 dummy user。
    # 为了方便，我们复用 Reviewer 但不给它工具，只让它负责结束。
    reviewer = AssistantAgent(
        name="req_reviewer",
        model_client=gemini_client,
        system_message="你负责确认分析师是否已完成所有拆解。如果完成，回复 TERMINATE。"
    )

    termination = TextMentionTermination("TERMINATE")
    team = RoundRobinGroupChat([analyst, reviewer], termination_condition=termination, max_turns=10)

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

    # ... (使用与 run_stream_task 相同的 processor 逻辑) ...
    # 我们可以复用 AutoGenStreamProcessor，只需要注册新的解析器即可

    processor = AutoGenStreamProcessor(
        agent_names={"req_analyst": "🧐 需求分析师", "req_reviewer": "✅ 流程确认"},
        tool_names=TOOL_NAMES_MAP
    )

    # 发送开场白
    yield format_sse("message", json.dumps({
        "type": "log", "source": "系统", "content": "正在启动需求分析引擎..."
    }, ensure_ascii=False))

    async for sse in processor.process_stream(team.run_stream(task=task_prompt)):
        yield sse