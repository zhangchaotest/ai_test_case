#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
测试用例服务层
负责处理测试用例相关的业务逻辑，包括：
1. 调用 Agent 生成测试用例 (支持流式输出)
2. 测试用例的增删改查
3. 批量操作和导出
"""

import json
import traceback
import threading
import queue
import asyncio
import time

from typing import List, Dict, Any

# 引入 Agent 和数据库操作
from backend.agents.case_agent import run_case_generation_stream, run_batch_functional_generation_stream
from backend.database.case_db import (
    CaseDB, get_existing_case_titles
)
from backend.utils.stream_utils import format_sse

# 实例化数据库操作对象
case_db = CaseDB()


class CaseService:
    """
    测试用例服务类
    封装了测试用例生成和管理的核心业务逻辑
    """
    
    def __init__(self):
        """初始化服务"""
        pass
    
    def generate_cases(self, req_id: int, feature_name: str, desc: str, 
                          target_count: int = 5, mode: str = "new", domain: str = "base", prompt_id: int = None):
        """
        生成测试用例 (流式响应)
        
        采用 "线程 + 队列 + 异步" 的模式：
        1. 主线程创建一个 Queue
        2. 启动一个后台线程运行 asyncio 事件循环
        3. 后台线程调用 Agent 生成用例，将 SSE 消息放入 Queue
        4. 主线程通过 yield 从 Queue 中取出消息返回给前端
        
        这种方式解决了 FastAPI StreamingResponse 与同步/异步代码混合调用时的兼容性问题。
        
        :param req_id: 关联的需求ID
        :param feature_name: 功能点名称
        :param desc: 功能点描述
        :param target_count: 目标生成数量
        :param mode: 生成模式 ('new': 全量生成, 'append': 增量生成)
        :param domain: 测试领域 ('base', 'web', 'api')
        :param prompt_id: 自定义提示词ID (可选)
        :return: 生成器，逐条 yield SSE 格式的字符串
        """
        # 创建队列用于线程间通信
        result_queue = queue.Queue()
        
        def worker():
            """后台工作线程：运行异步 Agent 任务"""
            try:
                async def process_async():
                    """异步处理包装函数"""
                    # 调用 Agent 的流式生成方法
                    async for sse in run_case_generation_stream(
                        req_id, feature_name, desc, target_count, mode, domain, prompt_id
                    ):
                        result_queue.put(sse)
                    # 标记处理完成 (放入 None 作为结束信号)
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
                # 非阻塞获取，避免完全阻塞主线程 (虽然 yield 本身会暂停)
                # 使用 sleep 稍微让出 CPU
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
    
    def batch_generate_cases(self, ids: List[int], target_count_per_item: int = 5):
        """
        批量生成测试用例 (流式响应)
        原理同 generate_cases，只是调用了 Agent 的批量生成方法
        
        :param ids: 功能点ID列表
        :param target_count_per_item: 每个功能点的目标生成数量
        :return: 生成器
        """
        # 创建队列用于线程间通信
        result_queue = queue.Queue()
        
        def worker():
            """后台工作线程"""
            try:
                async def process_async():
                    """异步处理函数"""
                    async for sse in run_batch_functional_generation_stream(ids, target_count_per_item):
                        result_queue.put(sse)
                    result_queue.put(None)
                
                asyncio.run(process_async())
            except Exception as e:
                traceback.print_exc()
                error_msg = format_sse("message",
                                     json.dumps({"type": "log", "source": "系统错误", "content": str(e)}, ensure_ascii=False))
                result_queue.put(error_msg)
                result_queue.put(None)
        
        # 启动后台线程
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
        
        # 从队列中获取结果并yield
        while True:
            try:
                time.sleep(0.05)
                if not result_queue.empty():
                    sse = result_queue.get()
                    if sse is None:
                        break
                    yield sse
            except Exception as e:
                print(f"Error in queue processing: {e}")
                break
    
    def get_existing_case_titles(self, req_id: int) -> List[str]:
        """
        获取指定需求下已存在的用例标题
        用于去重检查
        
        :param req_id: 需求ID
        :return: 标题列表
        """
        return case_db.get_existing_case_titles(req_id)
    
    def save_case(self, case_data: dict) -> str:
        """
        保存单条测试用例
        
        :param case_data: 用例数据字典
        :return: 保存结果 (ID 或 错误信息)
        """
        return case_db.save_case(case_data)
    
    def get_cases(self, page: int = 1, size: int = 10, req_id: int = None, title: str = None, status: str = None):
        """
        分页查询测试用例
        
        :param page: 页码
        :param size: 每页大小
        :param req_id: 需求ID过滤
        :param title: 标题模糊查询
        :param status: 状态过滤
        :return: 分页结果
        """
        return case_db.get_cases_page(page, size, req_id=req_id, title=title, status=status)
    
    def batch_update_case_status(self, ids: List[int], status: str) -> bool:
        """
        批量更新测试用例状态
        
        :param ids: 用例ID列表
        :param status: 新状态
        :return: 是否成功
        """
        return case_db.batch_update("test_cases", ids, "status", status)
    
    def get_cases_for_export(self, req_id: int = None, status: str = None) -> List[Dict]:
        """
        获取用于导出的全量测试用例数据
        
        :param req_id: 需求ID过滤
        :param status: 状态过滤
        :return: 用例列表
        """
        # 这里需要实现一个不分页的查询方法，或者复用分页查询但设置很大的 size
        # 暂时复用 get_cases_page，设置 size=10000
        result = case_db.get_cases_page(page=1, size=10000, req_id=req_id, status=status)
        return result['items']
