#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
需求分析服务
"""

import threading
import queue
import asyncio
import time

from typing import List, Dict, Any

from backend.agents.requirement_agent import run_requirement_analysis_stream
from backend.database.requirement_db import (
    get_requirements_page, get_requirement_by_id, save_analyzed_point,
    save_breakdown_item, get_breakdown_page, update_breakdown_item,
    update_breakdown_status, get_batch_breakdown_items, get_batch_functional_points
)


class RequirementService:
    """需求分析服务类"""
    
    def __init__(self):
        """初始化服务"""
        # 依赖注入可以在这里实现，目前直接使用默认依赖
        pass
    
    def analyze_requirement(self, project_id: int, raw_req: str, instruction: str = ""):
        """
        分析需求
        使用线程池和队列处理异步操作，避免 StreamingResponse 兼容性问题
        
        :param project_id: 项目ID
        :param raw_req: 原始需求内容
        :param instruction: 额外指令
        :return: 流式响应生成器
        """
        # 创建队列用于线程间通信
        result_queue = queue.Queue()
        
        def worker():
            """在后台线程中运行异步处理"""
            try:
                async def process_async():
                    """异步处理函数"""
                    for sse in run_requirement_analysis_stream(project_id, raw_req, instruction):
                        result_queue.put(sse)
                    # 标记处理完成
                    result_queue.put(None)
                
                # 运行异步处理
                asyncio.run(process_async())
            except Exception as e:
                import traceback
                traceback.print_exc()
                from backend.utils.stream_utils import format_sse
                import json
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
    
    def get_requirements(self, page: int = 1, size: int = 10, feature_name: str = None, priority: str = None):
        """
        获取功能点列表
        
        :param page: 页码
        :param size: 每页大小
        :param feature_name: 功能名称
        :param priority: 优先级
        :return: 分页结果
        """
        return get_requirements_page(page, size, feature_name, priority)
    
    def get_requirement_by_id(self, req_id: int):
        """
        根据ID获取功能点
        
        :param req_id: 功能点ID
        :return: 功能点信息
        """
        return get_requirement_by_id(req_id)
    
    def save_analyzed_point(self, data: Dict[str, Any]) -> str:
        """
        保存分析出的功能点
        
        :param data: 功能点数据
        :return: 保存结果
        """
        return save_analyzed_point(data)
    
    def save_breakdown_item(self, data: Dict[str, Any]) -> str:
        """
        保存需求拆解项
        
        :param data: 拆解项数据
        :return: 保存结果
        """
        return save_breakdown_item(data)
    
    def get_breakdowns(self, page: int = 1, size: int = 10, project_id: int = None, 
                      feature_name: str = None, status: str = None):
        """
        获取需求拆解列表
        
        :param page: 页码
        :param size: 每页大小
        :param project_id: 项目ID
        :param feature_name: 功能名称
        :param status: 状态
        :return: 分页结果
        """
        return get_breakdown_page(page, size, project_id, feature_name, status)
    
    def update_breakdown(self, item_id: int, data: Dict[str, Any]):
        """
        更新需求拆解项
        
        :param item_id: 拆解项ID
        :param data: 更新数据
        :return: 更新结果
        """
        return update_breakdown_item(item_id, data)
    
    def update_breakdown_status(self, item_id: int, new_status: str):
        """
        更新需求拆解状态
        
        :param item_id: 拆解项ID
        :param new_status: 新状态
        :return: 更新结果
        """
        return update_breakdown_status(item_id, new_status)
    
    def get_batch_breakdown_items(self, ids: List[int]) -> List[Dict]:
        """
        批量获取需求拆解项
        
        :param ids: 拆解项ID列表
        :return: 拆解项列表
        """
        return get_batch_breakdown_items(ids)
    
    def get_batch_functional_points(self, ids: List[int]) -> List[Dict]:
        """
        批量获取功能点
        
        :param ids: 功能点ID列表
        :return: 功能点列表
        """
        return get_batch_functional_points(ids)
