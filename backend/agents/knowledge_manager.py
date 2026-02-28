#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
知识管理模块
负责与 Dify 知识库进行交互，检索与当前任务相关的知识，
并将检索结果提供给 Agent，以增强生成的准确性和专业性。
"""

import requests
import json
from backend.config import DIFY_CONFIG

class KnowledgeManager:
    """
    知识库管理器
    封装了 Dify API 的调用逻辑
    """
    
    def __init__(self, api_key=None, endpoint=None):
        """
        初始化知识管理器
        
        :param api_key: Dify API Key (可选，默认从配置读取)
        :param endpoint: Dify API 端点 (可选，默认从配置读取)
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
        
        :param query: 查询语句 (通常是功能点名称或描述)
        :param limit: 返回结果数量限制
        :return: 知识检索结果列表 List[Dict]
        """
        try:
            print(f"📚 [知识库] 开始检索知识，查询语句: {query}")
            # 构建聊天请求 URL (Dify 的知识检索通常通过对话接口实现)
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
            # 打印请求详情便于调试
            # print(f"📚 [知识库] 请求参数: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            response = requests.post(
                chat_url,
                headers=self.headers,
                json=data,
                timeout=20  # 设置超时时间
            )
            
            if response.status_code == 200:
                print(f"📚 [知识库] 调用成功，状态码: {response.status_code}")
                result = response.json()
                # 提取核心知识内容
                knowledge_list = self._extract_knowledge(result)
                print(f"📚 [知识库] 提取知识数量: {len(knowledge_list)}")
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
        从 Dify API 响应中提取知识内容
        Dify 的响应结构可能包含直接回答 (answer) 或引用的知识片段 (retriever_resources)
        
        :param response: API 响应字典
        :return: 提取的知识列表
        """
        knowledge_list = []
        
        # 检查响应结构
        if isinstance(response, dict):
            # 1. 从 answer 字段提取知识 (如果是结构化回答)
            if 'answer' in response:
                answer = response['answer']
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
                    # 只有当 answer 有实质内容时才添加
                    if answer and len(answer.strip()) > 10:
                        knowledge_list.append({
                            'content': answer,
                            'metadata': {'source': 'Dify Answer'}
                        })
            
            # 2. 从 metadata.retriever_resources 提取引用的知识片段 (这是最准确的来源)
            if 'metadata' in response and 'retriever_resources' in response['metadata']:
                for resource in response['metadata']['retriever_resources']:
                    knowledge_list.append(resource)
        
        return knowledge_list

# 工厂函数
def get_knowledge_manager():
    return KnowledgeManager()
