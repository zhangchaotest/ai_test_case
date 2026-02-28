#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Dify 知识库测试脚本
用于测试 Dify 知识库的连接和知识查询功能
"""

import requests
import json
import time

class DifyKnowledgeTester:
    def __init__(self, api_key, endpoint):
        """
        初始化 Dify 知识库测试器
        :param api_key: Dify API Key
        :param endpoint: Dify API 端点
        """
        self.api_key = api_key
        self.endpoint = endpoint
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def test_server_access(self):
        """
        测试服务器是否可以访问
        :return: (success, message)
        """
        try:
            # 直接测试服务器访问，禁用重定向
            test_url = self.endpoint.rstrip("/")
            response = requests.get(test_url, timeout=10, allow_redirects=False)
            
            return True, f"服务器可访问，状态码: {response.status_code}"
        except Exception as e:
            return False, f"服务器访问失败: {str(e)}"
    
    def test_dify_api(self):
        """
        测试 Dify API 是否可用
        :return: (success, message)
        """
        try:
            # 尝试 Dify 常用的 API 端点
            api_endpoints = [
                '/chat/messages',
                '/completion',
                '/knowledge/bases',
                '/knowledge/documents',
                '/api/chat/messages',
                '/api/completion',
                '/api/knowledge/bases',
                '/api/knowledge/documents',
                '/v1/chat/messages',
                '/v1/completion',
                '/v1/knowledge/bases',
                '/v1/knowledge/documents'
            ]
            
            for endpoint in api_endpoints:
                test_url = f'{self.endpoint.rstrip("/")}{endpoint}'
                try:
                    # 发送一个简单的 POST 请求
                    response = requests.post(
                        test_url,
                        headers=self.headers,
                        json={},  # 空请求体
                        timeout=10,
                        allow_redirects=False
                    )
                    
                    # 即使返回错误，只要服务器响应了，就说明 API 端点存在
                    if response.status_code != 404:
                        return True, f"API 端点可访问: {test_url}, 状态码: {response.status_code}"
                except Exception as e:
                    continue
            
            return False, "未找到可用的 Dify API 端点"
        except Exception as e:
            return False, f"API 测试失败: {str(e)}"
    
    def run_full_test(self):
        """
        运行完整的测试流程
        """
        print("=" * 60)
        print(f"Dify 知识库测试 - {self.endpoint}")
        print("=" * 60)
        
        # 1. 测试服务器访问
        print("\n1. 测试服务器访问...")
        success, message = self.test_server_access()
        print(f"   结果: {'✓ 成功' if success else '✗ 失败'}")
        print(f"   消息: {message}")
        
        # 2. 测试 API 端点
        print("\n2. 测试 API 端点...")
        success, message = self.test_dify_api()
        print(f"   结果: {'✓ 成功' if success else '✗ 失败'}")
        print(f"   消息: {message}")
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)

if __name__ == "__main__":
    # 配置参数
    API_KEY = "app-g1VTEWzy7anvxjnm0lvmlVFq"
    
    # 尝试不同的 URL 格式
    endpoints_to_test = [
        "https://dify-test.lbxdrugs.com",
        "https://dify-test.lbxdrugs.com/v1",
        "https://dify-test.lbxdrugs.com/api",
        "https://dify-test.lbxdrugs.com/api/v1"
    ]
    
    for endpoint in endpoints_to_test:
        # 创建测试器
        tester = DifyKnowledgeTester(API_KEY, endpoint)
        
        # 运行测试
        tester.run_full_test()
        print("\n" + "-" * 60 + "\n")
    
    print("\n建议：")
    print("1. 确认 Dify 服务器 URL 是否正确")
    print("2. 确认 API Key 是否有效")
    print("3. 确认 Dify 服务器是否正常运行")
    print("4. 参考 Dify 官方文档获取正确的 API 端点")
    print("5. 检查网络连接和防火墙设置")
