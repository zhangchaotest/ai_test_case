#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Dify 知识库检索测试脚本
用于测试 Dify 知识库的知识检索功能
"""

import requests
import json

class DifyKnowledgeRetrievalTester:
    def __init__(self, api_key, endpoint):
        """
        初始化 Dify 知识库检索测试器
        :param api_key: Dify API Key
        :param endpoint: Dify API 端点
        """
        self.api_key = api_key
        self.endpoint = endpoint
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def test_chat_completion(self, query):
        """
        测试 Dify 聊天完成功能（可能包含知识检索）
        :param query: 查询语句
        :return: (success, data)
        """
        try:
            # 构建聊天请求 - 使用正确的 API 端点
            chat_url = f'{self.endpoint.rstrip("/")}/v1/chat-messages'
            data = {
                'query': query,
                'user': 'test_user',
                'conversation_id': '',
                'inputs': {},
                'response_mode': 'blocking',  # 使用阻塞模式，获取完整响应
                'files': []
            }
            
            print(f"请求 URL: {chat_url}")
            print(f"请求头: {self.headers}")
            print(f"请求体: {json.dumps(data, ensure_ascii=False)}")
            
            response = requests.post(
                chat_url,
                headers=self.headers,
                json=data,
                timeout=20
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            print(f"响应内容: {response.text[:500]}...")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    return True, result
                except Exception as e:
                    return False, f"JSON 解析失败: {str(e)}, 响应: {response.text[:200]}..."
            else:
                return False, f"聊天完成失败，状态码: {response.status_code}, 响应: {response.text[:200]}..."
        except Exception as e:
            return False, f"聊天完成异常: {str(e)}"
    
    def run_full_test(self):
        """
        运行完整的测试流程
        """
        print("=" * 60)
        print("Dify 知识库检索测试")
        print("=" * 60)
        
        # 测试知识检索
        print("\n测试知识检索功能...")
        test_queries = ['采购合同']
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n测试查询 {i}: '{query}'")
            success, data = self.test_chat_completion(query)
            
            if success:
                print(f"✓ 检索成功")
                # 打印响应内容
                if isinstance(data, dict):
                    if 'choices' in data:
                        for j, choice in enumerate(data['choices'], 1):
                            if 'message' in choice and 'content' in choice['message']:
                                content = choice['message']['content'][:200] + '...' if len(choice['message']['content']) > 200 else choice['message']['content']
                                print(f"  响应 {j}: {content}")
                    elif 'content' in data:
                        content = data['content'][:200] + '...' if len(data['content']) > 200 else data['content']
                        print(f"  响应: {content}")
                    else:
                        print(f"  响应: {json.dumps(data, ensure_ascii=False)[:200]}...")
            else:
                print(f"✗ 检索失败: {data}")
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)

if __name__ == "__main__":
    # 配置参数
    API_KEY = "app-g1VTEWzy7anvxjnm0lvmlVFq"
    ENDPOINT = "https://dify-test.lbxdrugs.com"
    
    # 创建测试器
    tester = DifyKnowledgeRetrievalTester(API_KEY, ENDPOINT)
    
    # 运行测试
    tester.run_full_test()
