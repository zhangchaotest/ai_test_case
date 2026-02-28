#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
需求分析服务层
负责处理需求分析相关的业务逻辑，包括：
1. 调用 Agent 进行需求分析和拆解 (支持流式输出)
2. 需求功能点和拆解项的增删改查
3. 状态流转管理
"""

import threading
import queue
import asyncio
import time
import json
import traceback

from typing import List, Dict, Any

# 引入 Agent 和数据库操作
from backend.agents.requirement_agent import run_requirement_analysis_stream
from backend.database.requirement_db import (
    get_requirements_page, get_requirement_by_id, save_analyzed_point,
    save_breakdown_item, get_breakdown_page, update_breakdown_item,
    update_breakdown_status, get_batch_breakdown_items, get_batch_functional_points
)
from backend.utils.stream_utils import format_sse


class RequirementService:
    """
    需求分析服务类
    封装了需求分析、拆解和管理的核心业务逻辑
    """
    
    def __init__(self):
        """初始化服务"""
        pass
    
    def analyze_requirement(self, project_id: int, raw_req: str, instruction: str = ""):
        """
        分析需求 (流式响应)
        
        采用 "线程 + 队列 + 异步" 的模式：
        1. 主线程创建一个 Queue
        2. 启动一个后台线程运行 asyncio 事件循环
        3. 后台线程调用 Agent 进行需求分析，将 SSE 消息放入 Queue
        4. 主线程通过 yield 从 Queue 中取出消息返回给前端
        
        :param project_id: 项目ID
        :param raw_req: 原始需求文本
        :param instruction: 额外的分析指令
        :return: 生成器，逐条 yield SSE 格式的字符串
        """
        # 创建队列用于线程间通信
        result_queue = queue.Queue()
        
        def worker():
            """后台工作线程：运行异步 Agent 任务"""
            try:
                async def process_async():
                    """异步处理包装函数"""
                    # 调用 Agent 的流式分析方法
                    async for sse in run_requirement_analysis_stream(project_id, raw_req, instruction):
                        result_queue.put(sse)
                    # 标记处理完成
                    result_queue.put(None)
                
                # 在新线程中运行 asyncio 事件循环
                asyncio.run(process_async())
            except Exception as e:
                # 捕获异常并发送给前端
                traceback.print_exc()
                error_msg = format_sse("message",
                                     json.dumps({"type": "log", "source": "系统错误", "content": str(e)}, ensure_ascii=False))
                result_queue.put(error_msg)
                result_queue.put(None)
        
        # 启动后台守护线程
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
        
        # 主线程：从队列中获取结果并 yield
        while True:
            try:
                # 非阻塞获取，避免完全阻塞主线程
                time.sleep(0.05)
                
                if not result_queue.empty():
                    sse = result_queue.get()
                    if sse is None:
                        # 收到结束信号，退出循环
                        break
                    yield sse
            except Exception as e:
                print(f"Error in queue processing: {e}")
                break
    
    def get_requirements(self, page: int = 1, size: int = 10, feature_name: str = None, priority: str = None):
        """
        分页获取功能点列表 (Functional Points)
        
        :param page: 页码
        :param size: 每页大小
        :param feature_name: 功能名称模糊查询
        :param priority: 优先级过滤
        :return: 分页结果
        """
        return get_requirements_page(page, size, feature_name, priority)
    
    def get_requirement_by_id(self, req_id: int):
        """
        根据 ID 获取功能点详情
        
        :param req_id: 功能点 ID
        :return: 功能点详情
        """
        return get_requirement_by_id(req_id)
    
    def save_analyzed_point(self, data: Dict[str, Any]) -> str:
        """
        保存分析出的功能点 (通常由 Agent 调用)
        
        :param data: 功能点数据
        :return: 保存结果 (ID 或 错误信息)
        """
        return save_analyzed_point(data)
    
    def save_breakdown_item(self, data: Dict[str, Any]) -> str:
        """
        保存需求拆解项 (Requirement Breakdown)
        
        :param data: 拆解项数据
        :return: 保存结果 (ID 或 错误信息)
        """
        return save_breakdown_item(data)
    
    def get_breakdowns(self, page: int = 1, size: int = 10, project_id: int = None, 
                      feature_name: str = None, status: str = None):
        """
        分页获取需求拆解项列表
        
        :param page: 页码
        :param size: 每页大小
        :param project_id: 项目ID过滤
        :param feature_name: 功能名称模糊查询
        :param status: 评审状态过滤
        :return: 分页结果
        """
        return get_breakdown_page(page, size, project_id, feature_name, status)
    
    def update_breakdown(self, item_id: int, data: Dict[str, Any]):
        """
        更新需求拆解项 (人工编辑)
        
        :param item_id: 拆解项 ID
        :param data: 更新数据
        :return: 是否成功
        """
        return update_breakdown_item(item_id, data)
    
    def update_breakdown_status(self, item_id: int, new_status: str):
        """
        更新需求拆解项的评审状态
        如果状态变为 'Pass'，会自动同步到功能点库
        
        :param item_id: 拆解项 ID
        :param new_status: 新状态 (Pass/Reject/Discard)
        :return: 是否成功
        """
        return update_breakdown_status(item_id, new_status)
    
    def get_batch_breakdown_items(self, ids: List[int]) -> List[Dict]:
        """
        批量获取需求拆解项
        
        :param ids: ID 列表
        :return: 拆解项列表
        """
        return get_batch_breakdown_items(ids)
    
    def get_batch_functional_points(self, ids: List[int]) -> List[Dict]:
        """
        批量获取功能点
        
        :param ids: ID 列表
        :return: 功能点列表
        """
        return get_batch_functional_points(ids)
