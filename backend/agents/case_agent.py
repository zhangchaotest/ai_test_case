#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：case_agent.py
@Author  ：张超
@Date    ：2025/12/22 09:20
@Desc    ：
"""
# backend/agents/case_agent.py

import json
import re
import traceback

from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.agents import AssistantAgent

# 导入项目模块
from backend.agents.llm_factory import get_gemini_client
from backend.database.case_db import save_case, get_existing_case_titles
from backend.utils.stream_utils import AutoGenStreamProcessor, format_sse

# 🔥 1. 确保头部导入了这两个 DB 方法
from backend.database.requirement_db import get_batch_functional_points
from backend.database.requirement_db import get_batch_breakdown_items  # 如果之前有针对拆解表的批量逻辑
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
    "save_case": "💾 数据库入库"
}


# -------------------------------------------------------------------------
# Agent 定义区域
# -------------------------------------------------------------------------

def create_test_generator(target_count: int = 5):
    """
    创建用例生成 Agent (Generator)
    :param target_count: 目标生成数量
    """
    print(f"🔍 [DEBUG] 正在创建 Generator Agent, 目标数量: {target_count}")

    return AssistantAgent(
        name="test_generator",
        model_client=gemini_client,
        system_message=f"""
        你是一个专业的测试工程师。

        【任务目标】
        针对给定的功能点，设计约 **{target_count}** 个测试用例。

        【生成策略】
        1. 优先覆盖：P0级核心功能 > 常见异常场景 > 关键边界值。
        2. **不要** 生成过于生僻或重复的用例（如网络断开、服务器物理损坏等）。
        3. 请一次性将这些用例的 JSON 结构输出完毕，不要分批次输出。

        【重要格式要求】
        输出的 JSON 列表中，每个用例必须包含以下字段：
        - "case_title": 用例标题 (必须有，且简洁明了)
        - "steps" 字段必须是一个 **列表 (List)**，包含多个对象。
            1、绝对不要填 steps 设为数字（如 -1, 0, 1 ）等
            2、严禁填纯文本字符串。
            3、正确示例：steps:[{{"step_id": 1, "action": "...", "expected": "..."}}]
        - "priority": 优先级 (P0-P2)
        - "case_type": 类型 (功能测试用例/反向测试用例/边界值测试用例)

        注意：steps 字段里的 JSON 括号必须完整。
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
        tools=[save_case],  # 绑定用例保存工具
        system_message="""
        你是测试组长。
        
        【任务】
        审查 Generator 生成的测试用例是否符合需求，**量化评分**并入库。
        
        【评分标准 (满分 1.0)】
        初始分 1.0，发现以下问题请扣分：
        1. **步骤不清 (-0.2)**: 步骤描述模糊，无法执行。
        2. **预期缺失 (-0.2)**: 预期结果与步骤不对应。
        3. **数据缺失 (-0.1)**: 需要具体测试数据（如金额、账号）但未提供。
        4. **逻辑错误 (-0.3)**: 用例逻辑与常规认知相悖。
        5. **格式错误 (-0.1)**: 步骤不是列表结构。
        6. **逻辑错误 (-0.3)**: 用例逻辑与需求要求内容相悖。

      【执行要求】
        1. 计算 `quality_score` (如 0.95)。
        2. 编写 `review_comments` (简短评价，如"步骤清晰，覆盖全面" 或 "缺少边界值数据")。
        3. 请检查 `steps`的值是否满足要求，不满足则直接拒绝 正确示例：steps:[{{"step_id": 1, "action": "...", "expected": "..."}}]
        4. 对于 Generator 生成的每个测试用例：
           - 为其添加 `requirement_id` 字段，值必须与任务中的功能ID一致
           - 为其添加 `quality_score` 字段
           - 为其添加 `review_comments` 字段
           - 单独调用 `save_case` 工具进行保存，确保每个用例都包含以上字段
        5. 严禁将所有用例包装在一个包含'case_list'键的对象中传递给save_case工具。
        6. 保存后回复 TERMINATE。
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


# -------------------------------------------------------------------------
# 主业务流程 (Case Generation)
# -------------------------------------------------------------------------

async def run_case_generation_stream(req_id: int, feature_name: str, desc: str, target_count: int = 5,
                                     mode: str = "new"):
    """
    用例生成流式任务入口

    :param req_id: 需求ID
    :param feature_name: 需求名称
    :param desc: 需求描述
    :param target_count: 目标生成数量
    :param mode: 'new' (全新生成) 或 'append' (追加生成)
    """
    print(f"🚀 [Case Stream] 开始处理 ID: {req_id}, Mode: {mode}")

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
            # 注意：这里的 get_existing_case_titles 来自 backend.database.case_db
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
        1. Generator 生成的用例必须是 JSON 格式的列表，每个用例包含：
           - case_title: 用例标题
           - steps: 测试步骤列表
           - priority: 优先级
           - case_type: 用例类型
        2. Reviewer 审查后，需要为每个用例添加：
           - requirement_id: 功能ID，必须为 {req_id}
           - quality_score: 质量评分
           - review_comments: 评审意见
        3. Reviewer 调用 save_case 工具时，必须为每个用例单独调用，确保每个用例都包含 requirement_id 字段。
        4. 严禁将所有用例包装在一个包含'case_list'键的对象中传递给save_case工具。
        5. 如果数量较多，你可以分多次（多轮对话）生成，每次生成 5 条，直到凑够数量。

        【重要执行指令】
        Generator，请立即开始工作！
        请先回复一句：“收到，正在为 [ID:{req_id}] 生成测试用例...”，然后紧接着输出 JSON 数据。
        **不要保持沉默！**
        """


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

        print("✅ [DEBUG] run_case_generation_stream 执行完毕")

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




# -------------------------------------------------------------------------
async def run_batch_functional_generation_stream(ids: list[int], target_count_per_item: int = 5):
    """
    批量生成测试用例 (数据源：functional_points 表)
    """
    print(f"🚀 [Batch Functional Stream] IDs={ids}")

    # 1. 获取数据
    items = get_batch_functional_points(ids)
    total = len(items)

    yield format_sse("message", json.dumps({
        "type": "log", "source": "系统通知",
        "content": f"📦 收到批量任务，共 {total} 个正式需求点待处理..."
    }, ensure_ascii=False))

    success_count = 0

    # 2. 循环处理
    for index, item in enumerate(items):
        current_num = index + 1
        req_id = item['id']
        feature_name = item['feature_name']
        # 兼容不同字段名
        desc = item.get('description', '') or item.get('feature_name', '')

        yield format_sse("message", json.dumps({
            "type": "log", "source": "系统调度",
            "content": f"\n🔄 [进度 {current_num}/{total}] 正在处理：{feature_name}..."
        }, ensure_ascii=False))

        try:
            # 复用单条生成逻辑
            async for sse_event in run_case_generation_stream(
                    req_id=req_id,
                    feature_name=feature_name,
                    desc=desc,
                    target_count=target_count_per_item,
                    mode="new"
            ):
                # 过滤掉单条任务的结束信号
                if "event: finish" not in sse_event:
                    yield sse_event

            success_count += 1

        except Exception as e:
            traceback.print_exc()
            yield format_sse("message", json.dumps({
                "type": "log", "source": "系统错误", "content": f"ID {req_id} 处理失败: {str(e)}"
            }, ensure_ascii=False))

    # 3. 结束
    yield format_sse("finish", json.dumps({"batch_total": total, "success": success_count}, ensure_ascii=False))