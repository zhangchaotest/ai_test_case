#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
测试维度管理模块
"""

class TestDimensionManager:
    """测试维度管理器"""
    
    def __init__(self):
        """初始化测试维度"""
        self.dimensions = {
            'functional': {
                'name': '功能测试',
                'description': '验证核心业务功能是否正常工作',
                'priority': 'high'
            },
            'boundary': {
                'name': '边界测试',
                'description': '测试输入输出的边界值',
                'priority': 'medium'
            },
            'exception': {
                'name': '异常测试',
                'description': '测试错误处理和异常场景',
                'priority': 'medium'
            },
            'security': {
                'name': '安全测试',
                'description': '测试权限、数据安全等',
                'priority': 'medium'
            },
            'performance': {
                'name': '性能测试',
                'description': '测试响应时间、并发处理等',
                'priority': 'low'
            },
            'compatibility': {
                'name': '兼容性测试',
                'description': '测试不同环境、设备等',
                'priority': 'low'
            }
        }
    
    def get_relevant_dimensions(self, req):
        """
        获取与需求相关的测试维度
        :param req: 需求对象
        :return: 相关测试维度列表
        """
        relevant_dims = []
        
        # 分析需求，确定相关维度
        desc = req.get('description', '').lower()
        
        # 功能测试是基础，始终包含
        relevant_dims.append('functional')
        
        # 根据需求描述判断其他维度
        if any(keyword in desc for keyword in ['user', 'login', 'auth', 'permission']):
            relevant_dims.append('security')
        
        if any(keyword in desc for keyword in ['api', 'request', 'response', 'parameter']):
            relevant_dims.append('boundary')
            relevant_dims.append('exception')
        
        if any(keyword in desc for keyword in ['performance', 'speed', 'response time', 'load']):
            relevant_dims.append('performance')
        
        if any(keyword in desc for keyword in ['browser', 'device', 'platform', 'compatible']):
            relevant_dims.append('compatibility')
        
        # 去重
        return list(set(relevant_dims))
    
    def generate_test_matrix(self, req):
        """
        生成测试维度矩阵
        :param req: 需求对象
        :return: 测试维度矩阵
        """
        relevant_dims = self.get_relevant_dimensions(req)
        matrix = []
        
        for dim in relevant_dims:
            dim_info = self.dimensions[dim]
            matrix.append({
                'dimension': dim,
                'name': dim_info['name'],
                'description': dim_info['description'],
                'priority': dim_info['priority']
            })
        
        return matrix
