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
from backend.database.prompt_db import get_prompt_by_id
from backend.utils.stream_utils import AutoGenStreamProcessor, format_sse

# 导入新增模块
from backend.agents.prompt_manager import PromptManager
from backend.agents.test_dimension import TestDimensionManager
from backend.agents.context_manager import ContextManager

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

# 初始化新增管理器
prompt_manager = PromptManager()
dimension_manager = TestDimensionManager()
context_manager = ContextManager()


# -------------------------------------------------------------------------
# Agent 定义区域
# -------------------------------------------------------------------------

def create_test_generator(target_count: int = 5, domain='base', prompt_id: int = None):
    """
    创建用例生成 Agent (Generator)
    :param target_count: 目标生成数量
    :param domain: 领域类型
    :param prompt_id: 提示词ID
    """
    print(f"🔍 [DEBUG] 正在创建 Generator Agent, 目标数量: {target_count}")

    # 获取提示词
    if prompt_id:
        prompt = get_prompt_by_id(prompt_id)
        if prompt:
            system_message = prompt['content'].replace('{target_count}', str(target_count))
            print(f"📝 使用自定义提示词: {prompt['name']}")
        else:
            system_message = prompt_manager.get_prompt('generator', domain, target_count=target_count)
            print("⚠️  提示词ID不存在，使用默认提示词")
    else:
        system_message = prompt_manager.get_prompt('generator', domain, target_count=target_count)

    return AssistantAgent(
        name="test_generator",
        model_client=gemini_client,
        system_message=system_message
    )


def create_test_reviewer(domain='base', prompt_id: int = None):
    """
    创建用例评审 Agent (Reviewer)
    拥有入库工具权限
    :param domain: 领域类型
    :param prompt_id: 提示词ID
    """
    # 获取提示词
    if prompt_id:
        prompt = get_prompt_by_id(prompt_id)
        if prompt:
            system_message = prompt['content']
            print(f"📝 使用自定义评审提示词: {prompt['name']}")
        else:
            system_message = prompt_manager.get_prompt('reviewer', domain)
            print("⚠️  提示词ID不存在，使用默认评审提示词")
    else:
        system_message = prompt_manager.get_prompt('reviewer', domain)

    return AssistantAgent(
        name="test_reviewer",
        model_client=gemini_client,
        tools=[save_case],  # 绑定用例保存工具
        system_message=system_message
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
                                     mode: str = "new", domain='base', prompt_id: int = None):
    """
    用例生成流式任务入口

    :param req_id: 需求ID
    :param feature_name: 需求名称
    :param desc: 需求描述
    :param target_count: 目标生成数量
    :param mode: 'new' (全新生成) 或 'append' (追加生成)
    :param domain: 领域类型 ('base', 'web', 'api' 等)
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

        # --- 4. 生成测试维度矩阵 --- 
        req = {'feature_name': feature_name, 'description': desc}
        test_matrix = dimension_manager.generate_test_matrix(req)
        
        # --- 5. 获取上下文信息 --- 
        context = context_manager.get_context(req_id, req)
        
        # --- 6. 构建测试维度和上下文信息 --- 
        dimension_info = "\n\n【测试维度】\n"
        for dim in test_matrix:
            dimension_info += f"- {dim['name']}: {dim['description']} (优先级: {dim['priority']})\n"
        
        context_info = ""
        if context['existing_cases']:
            context_info += "\n\n【已存在用例】\n"
            for title in context['existing_cases'][:5]:  # 只显示前5个
                context_info += f"- {title}\n"
            if len(context['existing_cases']) > 5:
                context_info += f"... 等 {len(context['existing_cases'])} 个用例\n"
        
        if context['coverage_gaps']:
            context_info += "\n【覆盖盲区】\n"
            for gap in context['coverage_gaps']:
                context_info += f"- {gap}\n"

        # --- 7. 组装 AutoGen Team ---
        generator = create_test_generator(target_count, domain, prompt_id)
        reviewer = create_test_reviewer(domain, prompt_id)
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
        {dimension_info}
        {context_info}

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
                    mode="new",
                    domain='base'
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