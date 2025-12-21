#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：stream_utils.py
@Author  ：张超
@Date    ：2025/12/19 14:56
@Desc    ：
"""
import json
import re
from typing import AsyncGenerator, Dict, Callable
from autogen_agentchat.messages import TextMessage, ToolCallRequestEvent, ToolCallExecutionEvent


def format_sse(event: str, data: str) -> str:
    """
    辅助函数：将数据格式化为 SSE (Server-Sent Events) 标准字符串。
    需要将换行符替换为 \\n 以避免破坏 SSE 协议格式。
    """
    clean_data = data.replace("\n", "\\n")
    return f"event: {event}\ndata: {clean_data}\n\n"


class AutoGenStreamProcessor:
    """
    通用 AutoGen 流式处理器
    功能：
    1. 接收 AutoGen 的原始流 (run_stream)。
    2. 解析复杂的事件对象 (Text, ToolCall, ToolResult)。
    3. 提取关键信息 (如用例标题、数据库ID)。
    4. 转换为前端友好的 SSE 格式。
    5. 自动统计生成数量和入库数量。
    """

    def __init__(
            self,
            agent_names: Dict[str, str] = None,
            tool_names: Dict[str, str] = None,
            custom_text_parsers: Dict[str, Callable[[str], str]] = None
    ):
        # 映射字典：将英文名转换为中文友好名称
        self.agent_names = agent_names or {}
        self.tool_names = tool_names or {}
        # 自定义解析器：用于特定 Agent 的文本美化
        self.custom_text_parsers = custom_text_parsers or {}

        # 初始化统计数据
        self.stats = {"generated": 0, "saved": 0}

    async def process_stream(self, stream_iterator) -> AsyncGenerator[str, None]:
        """
        核心处理循环：遍历流迭代器并生成 SSE 事件
        """
        try:
            async for message in stream_iterator:
                output_data = None

                # ---------------------------------------------------------
                # 0. 预处理：兼容性转换
                # AutoGen 对象转字典，兼容 Pydantic v1/v2 及普通对象
                # ---------------------------------------------------------
                msg_dict = message.model_dump() if hasattr(message, 'model_dump') else message.__dict__

                # ---------------------------------------------------------
                # 1. 处理文本消息 (Agent 思考与对话)
                # ---------------------------------------------------------
                if isinstance(message, TextMessage):
                    # 过滤掉终止信号和用户指令，不展示给前端
                    if "TERMINATE" in message.content: continue
                    if message.source == "user": continue

                    # 获取中文名称
                    source_display = self.agent_names.get(message.source, message.source)

                    # 尝试使用自定义解析器 (例如提取 "正在构思 xxx 用例")
                    parser = self.custom_text_parsers.get(message.source)
                    if parser:
                        content_display = parser(message.content)
                    else:
                        # 默认处理：如果内容太长且没有特定格式，简化显示
                        content_display = message.content
                        if len(content_display) > 100: content_display = "正在思考..."

                    output_data = {
                        "type": "log",
                        "source": source_display,
                        "content": content_display
                    }

                # ---------------------------------------------------------
                # 2. 处理工具调用请求 (🔥 核心逻辑：统计生成数 & 列表展示)
                # ---------------------------------------------------------
                elif isinstance(message, ToolCallRequestEvent):
                    calls = []
                    if msg_dict.get('tool_calls'):
                        calls = msg_dict['tool_calls']
                    elif isinstance(msg_dict.get('content'), list):
                        calls = msg_dict['content']

                    if calls:
                        tool_display_names = []
                        generated_titles = []

                        for call in calls:
                            # 1. 准备数据
                            raw_name = "Unknown"
                            arguments_str = '{}'

                            if isinstance(call, dict):
                                raw_name = call.get('name') or call.get('function', {}).get('name')
                                arguments_str = call.get('arguments', '{}')
                            elif hasattr(call, 'function'):
                                raw_name = call.function.name
                                arguments_str = call.function.arguments

                            tool_display_names.append(self.tool_names.get(raw_name, raw_name))

                            # 2. 🔥 智能提取标题 (修复点)
                            try:
                                args = json.loads(arguments_str)
                                title = None
                                # 尝试直接获取
                                title = args.get('case_title') or args.get('title')
                                # 尝试从 data 嵌套获取
                                if not title and isinstance(args.get('data'), dict):
                                    title = args['data'].get('case_title') or args['data'].get('title')

                                if title:
                                    generated_titles.append(title)
                            except:
                                pass

                        # --- C. 构造展示 ---
                        self.stats["generated"] += len(generated_titles)  # 只有提取到标题才算生成成功

                        unique_names = list(set(tool_display_names))
                        display_text = f"正在调用: {','.join(unique_names)}"

                        if generated_titles:
                            display_text += "\n📦 包含用例列表:"
                            for idx, title in enumerate(generated_titles):
                                display_text += f"\n{idx + 1}、{title}"
                        elif len(calls) > 1:
                            display_text += f" (批量处理 {len(calls)} 项)"

                        output_data = {
                            "type": "tool_call",
                            "source": "系统调用",
                            "content": display_text
                        }

                # ---------------------------------------------------------
                # 3. 处理工具执行结果 (统计入库成功数)
                # ---------------------------------------------------------
                elif isinstance(message, ToolCallExecutionEvent):
                    # 获取结果列表
                    results = msg_dict.get('tool_call_results') or []
                    if not results and isinstance(msg_dict.get('content'), list):
                        results = msg_dict.get('content')

                    success_count = 0
                    ids = []

                    print(results)

                    for res in results:
                        # 兼容处理结果内容
                        res_content = str(res.get('content', '')) if isinstance(res, dict) else str(
                            getattr(res, 'content', ''))

                        # 判断是否入库成功 (根据业务约定的返回格式 "ID: xxx")
                        # 情况 A: 标准格式 "ID: 100"
                        if "ID:" in res_content:
                            success_count += 1
                            match = re.search(r'ID:\s*(\d+)', res_content)
                            if match: ids.append(match.group(1))
                        # 情况 B: 纯数字格式 "100" (save_case 返回的就是这个)
                        elif res_content.strip().isdigit():
                            success_count += 1
                            ids.append(res_content.strip())

                    # 更新统计
                    self.stats["saved"] += success_count

                    if success_count > 0:
                        output_data = {
                            "type": "tool_result",
                            "source": "数据库",
                            "content": f"✅ 成功入库 {success_count} 条 (ID: {','.join(ids)})"
                        }
                    else:
                        # 如果全部失败，显示第一条错误信息
                        first_err = str(results[0]) if results else "无数据"
                        output_data = {
                            "type": "tool_result",
                            "source": "数据库",
                            "content": f"⚠️ 反馈: {first_err[:50]}..."
                        }

                # ---------------------------------------------------------
                # 4. 发送单条 SSE 事件
                # ---------------------------------------------------------
                if output_data:
                    yield format_sse("message", json.dumps(output_data, ensure_ascii=False))

        except Exception as e:
            # 异常捕获与前端通知
            print(f"Stream Error: {e}")
            yield format_sse("message", json.dumps({
                "type": "log", "source": "系统错误", "content": str(e)
            }, ensure_ascii=False))

        # ---------------------------------------------------------
        # 5. 循环结束，发送最终统计报表 (Finish 事件)
        # ---------------------------------------------------------
        yield format_sse("finish", json.dumps(self.stats, ensure_ascii=False))

