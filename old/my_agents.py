#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：my_agents.py
@Author  ：张超
@Date    ：2025/12/17 10:24
@Desc    ：Autogen访问gemini大模型的适配器
"""
# my_agents.py
from autogen_agentchat.agents import AssistantAgent
from llm_factory import get_gemini_client
from old.db_tools import save_functional_point, save_verified_test_case  # 导入工具

# 1. 先获取统一的 Gemini 客户端配置
# 你也可以在这里为不同的 agent 获取不同的配置（例如 model 变了）
gemini_client = get_gemini_client()


def create_coder_agent():
    """创建一个负责写代码的 Agent"""
    return AssistantAgent(
        name="coder",
        model_client=gemini_client,
        system_message="你是一个高级 Python 工程师。请编写高效、整洁的代码。只输出代码块。"
    )


def create_reviewer_agent():
    """创建一个负责代码审查的 Agent"""
    return AssistantAgent(
        name="reviewer",
        model_client=gemini_client,
        system_message="你是一个代码审查专家。请检查代码的潜在 bug 和安全问题，并用中文给出修改建议。"
    )


def create_requirement_analyst():
    """创建一个具备数据库访问能力的需求分析师"""

    return AssistantAgent(
        name="requirement_analyst",
        model_client=gemini_client,

        # 🔥 核心：在这里把工具交给 Agent
        tools=[save_functional_point],

        # System Message 需要引导 Agent 使用工具
        system_message="""
        你是一个资深产品经理和需求分析师。
        你的任务是阅读用户的原始需求文档，将其拆解为细粒度的“功能点”。

        对于拆解出来的每一个功能点，你**必须**调用工具 `save_functional_point` 将其保存到数据库。
        不要只在对话中列出功能，**必须执行保存操作**。

        请分析全面，不要遗漏细节。
        """
    )


def create_test_generator():
    return AssistantAgent(
        name="test_generator",
        model_client=gemini_client,
        system_message="""
        你是一个专业的测试工程师。
        
        编写用例时，除了步骤外，请务必分析以下属性：
        1. **优先级 (priority)**: 
           - 核心业务流程 (如登录、支付) 设为 P0
           - 重要功能设为 P1
           - 异常/边界测试设为 P2
        
        2. **用例类型 (case_type)**:
           - 正常操作标记为 'Functional'
           - 报错/异常流程标记为 'Negative'
           - 边界值测试标记为 'Boundary'
           
        3. **测试数据 (test_data)**:
           - 如果步骤中涉及具体输入，请将其提取为 JSON 对象。
           - 例如: {"amount": 100, "currency": "CNY"}
           
        请以结构化的方式提供这些信息给评审员。
        """
    )


def create_test_reviewer():
    """测试用例评审专家 (有权限存库)"""
    return AssistantAgent(
        name="test_reviewer",
        model_client=gemini_client,
        # 🔥 关键：只有评审员有保存工具
        tools=[save_verified_test_case],
        system_message="""
        你是一个严格的测试组长。
        你的任务是审查 `test_generator` 生成的用例。

        审查标准：
        1. 覆盖率是否足够？
        2. 步骤是否清晰？
        3. 预期结果是否明确？

        执行逻辑：
        - 如果用例写得不好：请直接指出问题，要求生成者重写。
        - 如果用例通过评审：**必须**调用工具 `save_verified_test_case` 将其保存到数据库。
        - 当所有用例都保存完毕后，回复 "TERMINATE" 结束任务。
        """
    )
