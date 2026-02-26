#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
上下文管理模块
"""

from backend.database.case_db import get_existing_case_titles

class ContextManager:
    """上下文管理器"""
    
    def __init__(self):
        """初始化"""
        pass
    
    def get_context(self, req_id, req):
        """
        获取上下文信息
        :param req_id: 需求ID
        :param req: 需求对象
        :return: 上下文信息
        """
        # 获取现有用例标题
        existing_titles = get_existing_case_titles(req_id)
        
        # 提取测试模式
        test_patterns = self.extract_test_patterns(existing_titles)
        
        # 识别覆盖盲区
        coverage_gaps = self.identify_coverage_gaps(req, existing_titles)
        
        return {
            'existing_cases': existing_titles,
            'test_patterns': test_patterns,
            'coverage_gaps': coverage_gaps
        }
    
    def extract_test_patterns(self, existing_titles):
        """
        提取测试模式
        :param existing_titles: 现有用例标题列表
        :return: 测试模式列表
        """
        patterns = []
        
        # 分析现有用例标题，提取模式
        for title in existing_titles:
            if '成功' in title:
                patterns.append('成功场景')
            elif '失败' in title:
                patterns.append('失败场景')
            elif '边界' in title:
                patterns.append('边界值测试')
            elif '异常' in title:
                patterns.append('异常场景')
            elif '安全' in title:
                patterns.append('安全测试')
            elif '性能' in title:
                patterns.append('性能测试')
        
        # 去重并返回
        return list(set(patterns))
    
    def identify_coverage_gaps(self, req, existing_titles):
        """
        识别覆盖盲区
        :param req: 需求对象
        :param existing_titles: 现有用例标题列表
        :return: 覆盖盲区列表
        """
        gaps = []
        
        # 基础测试类型
        base_types = ['成功场景', '失败场景', '边界值测试', '异常场景']
        
        # 分析现有用例，识别缺失的测试类型
        existing_types = []
        for title in existing_titles:
            if '成功' in title:
                existing_types.append('成功场景')
            elif '失败' in title:
                existing_types.append('失败场景')
            elif '边界' in title:
                existing_types.append('边界值测试')
            elif '异常' in title:
                existing_types.append('异常场景')
        
        # 识别缺失的测试类型
        for test_type in base_types:
            if test_type not in existing_types:
                gaps.append(test_type)
        
        # 根据需求描述添加特定的覆盖盲区
        desc = req.get('description', '').lower()
        if 'login' in desc and '安全测试' not in existing_types:
            gaps.append('安全测试')
        if 'api' in desc and '边界值测试' not in existing_types:
            gaps.append('边界值测试')
        
        return gaps
