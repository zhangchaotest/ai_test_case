#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
知识管理模块
用于与 Dify 知识库交互，检索相关知识
"""

import requests
import json
from backend.config import DIFY_CONFIG

class KnowledgeManager:
    def __init__(self, api_key=None, endpoint=None):
        """
        初始化知识管理器
        :param api_key: Dify API Key
        :param endpoint: Dify API 端点
        """
        self.api_key = api_key or DIFY_CONFIG["api_key"]
        self.endpoint = endpoint or DIFY_CONFIG["endpoint"]
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def retrieve_knowledge(self, query, limit=3):
        """
        从 Dify 知识库检索相关知识
        :param query: 查询语句
        :param limit: 返回结果数量
        :return: 知识检索结果
        """
        try:
            print(f"📚 [知识库] 开始检索知识，查询语句: {query}")
            # 构建聊天请求
            chat_url = f'{self.endpoint.rstrip("/")}/v1/chat-messages'
            data = {
                'query': query,
                'user': 'test_user',
                'conversation_id': '',
                'inputs': {},
                'response_mode': 'blocking',
                'files': []
            }
            
            print(f"📚 [知识库] 调用API: {chat_url}")
            print(f"📚 [知识库] 请求参数: {json.dumps(data, ensure_ascii=False, indent=2)}")
            print(f"📚 [知识库] 请求头: {json.dumps(dict(self.headers), ensure_ascii=False, indent=2)}")
            response = requests.post(
                chat_url,
                headers=self.headers,
                json=data,
                timeout=20
            )
            
            if response.status_code == 200:
                print(f"📚 [知识库] 调用成功，状态码: {response.status_code}")
                result = response.json()
                print(f"📚 [知识库] 原始响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                knowledge_list = self._extract_knowledge(result)
                print(f"📚 [知识库] 提取知识数量: {len(knowledge_list)}")
                for i, knowledge in enumerate(knowledge_list):
                    print(f"📚 [知识库] 知识 {i+1}: {json.dumps(knowledge, ensure_ascii=False, indent=2)}")
                return knowledge_list
            else:
                print(f"📚 [知识库] 调用失败，状态码: {response.status_code}")
                print(f"📚 [知识库] 错误响应: {response.text}")
                return []
        except Exception as e:
            print(f"📚 [知识库] 调用异常: {str(e)}")
            return []
    
    def _extract_knowledge(self, response):
        """
        从响应中提取知识内容
        :param response: API 响应
        :return: 提取的知识列表
        """
        knowledge_list = []
        
        # 检查响应结构
        if isinstance(response, dict):
            # 从 answer 字段提取知识
            if 'answer' in response:
                answer = response['answer']
                # 尝试解析 answer 字段（可能是字符串或列表）
                try:
                    if isinstance(answer, str):
                        # 尝试解析 JSON 字符串
                        parsed_answer = json.loads(answer)
                        if isinstance(parsed_answer, list):
                            for item in parsed_answer:
                                if isinstance(item, dict) and 'metadata' in item:
                                    knowledge_list.append(item)
                    elif isinstance(answer, list):
                        for item in answer:
                            if isinstance(item, dict) and 'metadata' in item:
                                knowledge_list.append(item)
                except:
                    # 如果解析失败，将 answer 作为纯文本处理
                    knowledge_list.append({
                        'content': answer,
                        'metadata': {'source': 'text'}
                    })
            
            # 从 metadata.retriever_resources 提取知识
            if 'metadata' in response and 'retriever_resources' in response['metadata']:
                for resource in response['metadata']['retriever_resources']:
                    knowledge_list.append(resource)
        
        return knowledge_list

# 初始化知识管理器
def get_knowledge_manager():
    return KnowledgeManager()
