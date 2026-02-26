#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
测试用例服务
"""

import json
import traceback
import threading
import queue
import asyncio
import time

from typing import List

from backend.agents.case_agent import run_case_generation_stream, run_batch_functional_generation_stream
from backend.database.case_db import (
    get_existing_case_titles, save_case, get_cases_page, 
    batch_update_status, get_all_cases_for_export
)
from backend.database.requirement_db import get_batch_functional_points
from backend.utils.stream_utils import format_sse


class CaseService:
    """测试用例服务类"""
    
    def __init__(self):
        """初始化服务"""
        # 依赖注入可以在这里实现，目前直接使用默认依赖
        pass
    
    def generate_cases(self, req_id: int, feature_name: str, desc: str, 
                          target_count: int = 5, mode: str = "new", domain: str = "base", prompt_id: int = None):
        """
        生成测试用例（修复版）
        使用线程池和队列处理异步操作，避免 StreamingResponse 兼容性问题
        
        :param req_id: 需求ID
        :param feature_name: 功能名称
        :param desc: 功能描述
        :param target_count: 目标生成数量
        :param mode: 生成模式 ('new' 或 'append')
        :param domain: 领域类型 ('base', 'web', 'api' 等)
        :return: 流式响应生成器
        """
        # 创建队列用于线程间通信
        result_queue = queue.Queue()
        
        def worker():
            """在后台线程中运行异步处理"""
            try:
                async def process_async():
                    """异步处理函数"""
                    async for sse in run_case_generation_stream(
                        req_id, feature_name, desc, target_count, mode, domain, prompt_id
                    ):
                        result_queue.put(sse)
                    # 标记处理完成
                    result_queue.put(None)
                
                # 运行异步处理
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
                # 非阻塞获取，避免阻塞主线程
                time.sleep(0.1)  # 避免过于频繁的轮询
                
                if not result_queue.empty():
                    sse = result_queue.get()
                    if sse is None:
                        # 处理完成
                        break
                    yield sse
            except Exception as e:
                print(f"Error in queue processing: {e}")
                break
    
    def batch_generate_cases(self, ids: List[int], target_count_per_item: int = 5):
        """
        批量生成测试用例（修复版）
        使用线程池和队列处理异步操作，避免 StreamingResponse 兼容性问题
        
        :param ids: 功能点ID列表
        :param target_count_per_item: 每个功能点的目标生成数量
        :return: 流式响应生成器
        """
        import threading
        import queue
        import asyncio
        import time
        
        # 创建队列用于线程间通信
        result_queue = queue.Queue()
        
        def worker():
            """在后台线程中运行异步处理"""
            try:
                async def process_async():
                    """异步处理函数"""
                    async for sse in run_batch_functional_generation_stream(ids, target_count_per_item):
                        result_queue.put(sse)
                    # 标记处理完成
                    result_queue.put(None)
                
                # 运行异步处理
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
                # 非阻塞获取，避免阻塞主线程
                time.sleep(0.1)  # 避免过于频繁的轮询
                
                if not result_queue.empty():
                    sse = result_queue.get()
                    if sse is None:
                        # 处理完成
                        break
                    yield sse
            except Exception as e:
                print(f"Error in queue processing: {e}")
                break
    
    def get_existing_case_titles(self, req_id: int):
        """
        获取已存在的用例标题
        
        :param req_id: 需求ID
        :return: 用例标题列表
        """
        return get_existing_case_titles(req_id)
    
    def save_case(self, case_data: dict):
        """
        保存测试用例
        
        :param case_data: 用例数据
        :return: 保存结果
        """
        return save_case(case_data)
    
    def get_cases(self, page: int = 1, size: int = 10, req_id: int = None, status: str = None):
        """
        获取测试用例列表
        
        :param page: 页码
        :param size: 每页大小
        :param req_id: 需求ID
        :param status: 状态
        :return: 分页结果
        """
        return get_cases_page(page, size, req_id=req_id, title=None, status=status)
    
    def batch_update_case_status(self, ids: List[int], status: str):
        """
        批量更新测试用例状态
        
        :param ids: 用例ID列表
        :param status: 新状态
        :return: 更新结果
        """
        return batch_update_status(ids, status)
    
    def get_cases_for_export(self, req_id: int = None, status: str = None):
        """
        获取用于导出的测试用例
        
        :param req_id: 需求ID
        :param status: 状态
        :return: 用例列表
        """
        return get_all_cases_for_export(req_id=req_id, status=status)
