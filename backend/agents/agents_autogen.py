#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：AI_XLY
@File    ：agent_demo_01.py
@Author  ：张超
@Date    ：2025/11/18 20:29
@Desc    ：自动化测试用例生成代理
"""
import asyncio
import os
import sys

from old import config_list

# 将项目根目录添加到路径中，以便我们可以从后端导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination, SourceMatchTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console

# 导入DeepSeek而不是Gemini以避免连接问题
# 我们将创建一个包装器使其与autogen_agentchat兼容
from old.llms import gemini_llm



async def get_file_content():
    file_path = f"/Users/zhangchao/code/work/ai_test_case_fast/backend/requirement/xuqiu.md"
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return "文件未找到: " + file_path
    except Exception as e:
        return f"读取文件时发生错误: {str(e)}"


test_case_origin = AssistantAgent(
        name="test_case_origin",
        model_client=gemini_llm,
        tools = [get_file_content],
        system_message="你负责调用 get_file_content 工具获取文档内容，并将完整的内容提供给test_case_writer",
        model_client_stream=True,
    )

requirements_analyst = AssistantAgent(
    name="requirements_analyst",
    llm_config={"config_list": config_list},
    system_message="""

    """
)
# 需求格式化输出
requirements_analyst_format_output = AssistantAgent(
    name="requirements_analyst_format_output",
    llm_config={"config_list": config_list},
    system_message="""
        你现在是一个资深产品经理/业务分析师，熟悉敏捷开发和用户故事拆解方法。你的任务是：
        
        1. 阅读以下完整需求文档，文档可能包含功能描述、业务规则、用户痛点、流程说明和目标。
        2. 将文档内容拆分为若干条 **用户故事 (User Story)**。
        3. 对每个用户故事生成以下字段：
           - story_title: 故事标题，简洁概括功能。
           - user_story: 用户故事描述，格式为 "作为[角色]，我希望[功能]，以便[价值]"。
           - acceptance_criteria: 验收标准，列出 2-5 条具体可验证条件。
           - priority: 优先级，高/中/低。
           - story_points: 故事点，估算范围 1-8（1=简单，8=复杂）。
           - optional_tags: 可选字段，用于标记模块、业务线或功能分类。
        
        4. 拆分规则：
           - 每个独立功能或业务流程拆成一条用户故事。
           - 如果某条功能很复杂，可以拆分成多条子故事。
           - 保留所有关键需求和边界条件。
           - 避免重复和模糊描述。
        
        5. 输出要求：
           - 必须严格按照 **JSON 列表格式** 输出，每条用户故事为一个对象。
           - 不要输出额外解释或文字。
        
        
        
        1. 解析自然语言描述的业务需求。
        2. 提取每条需求的字段，并严格按照以下 Pydantic 模型输出 JSON：
        
        BusinessRequirement:
        - story_title: 故事标题，简洁概括功能。
        - user_story: 用户故事描述，格式为 "作为[角色]，我希望[功能]，以便[价值]"。
        - optional_tags: 可选字段，用于标记模块、业务线或功能分类。
        - parent_requirement: 父级需求，如果没有则为 null
        - requirement_level: 需求层级，如 "高"、"中"、"低"
        - reviewer: 需求审核人
        - estimate_time: 预计完成时间，整数，单位天
        - description: 需求详细描述
        - priority: 优先级，高/中/低。
        - story_points: 故事点，估算范围 1-8（1=简单，8=复杂）。
        - acceptance_criteria: 验收标准，列出 2-5 条具体可验证条件。
        
        BusinessRequirementList:
        - business_requirements: 包含多条 BusinessRequirement 的列表
        
        ⚠️ 输出要求：
        - 严格输出 JSON，字段必须完整，不要输出解释文字
        - 如果有多条需求，用 business_requirements 封装
        - JSON 示例：
        {
          "business_requirements": [
            {
              "BusinessRequirement_name": "用户注册功能",
              "requirement_type": "功能需求",
              "parent_requirement": null,
              "module": "用户模块",
              "requirement_level": "高",
              "reviewer": "张三",
              "estimate_time": 5,
              "description": "必须支持邮箱和手机号注册",
              "accept_criteria": "用户能成功注册并登录"
            }
          ]
        }
   """
)
requirements_analyst_check = AssistantAgent(
    name="requirements_analyst",
    model_client=gemini_llm,
    system_message="""
    你负责检查需求分析结果，并给出修正建议。
    要求：
    1. 输出修正建议，并严格输出 JSON，字段必须完整，不要输出解释文字
    2. 输出格式：
    {
      "fix_suggestion": "修正建议"
    }
    如果你检查通过，则进行下一步，且输出通过，
    如果你检查不通过，则进行上一步，且输出检查不通过和修正建议
    """
)

test_case_writer = AssistantAgent(
    name="test_case_writer",
    model_client=gemini_llm,
    system_message="""
        注意：严格按照用户的指令完成用例数量的编写。
            你是一位高级用例编写工程师，请按照如下规则编写：
            一、考虑使用如下用例设计方法及整合使用
            1、基础设计方法组合应用
            等价类划分：划分有效/无效等价类（如金额范围0.01-200元10）
            边界值分析：覆盖最小值、最大值及±1临界值（如微信红包0.01/200.01边界10）
            因果图与判定表：处理多输入条件组合（如用户登录场景：账号存在+密码正确/错误2）
            场景法：主流程+备选流覆盖（如电商下单：正常购买、库存不足、支付失败10）
            错误推测法：基于历史缺陷库设计异常路径（如输入特殊字符、超长字段2）
            2、高级设计方法补充
            正交试验法：针对多参数组合场景（如API接口参数组合优化测试）
            状态迁移法：适用于状态机驱动的功能（如订单状态流转：待支付→已取消→已退款）
            探索式测试：结合Session-Based Testing动态补充用例（复杂业务流程快速覆盖）
            二、保障测试用例的全面性
            1、多维度覆盖
            功能测试：正向流程+异常分支（如支付成功/余额不足/网络超时）
            性能测试：负载、压力、稳定性（如高并发下单场景8）
            安全测试：SQL注入、XSS、越权访问（垂直/水平权限校验11）
            兼容性测试：多OS（Windows/macOS）、浏览器（Chrome/Firefox）、分辨率适配
            用户体验测试：界面一致性、操作流畅性、提示友好性（如错误信息可读性7）
            2、数据驱动与参数化
            数据分离：外部CSV/Excel管理测试数据（如百种用户角色权限组合6）
            动态参数注入：通过变量实现用例复用（如API请求参数模板化）
            三、用例编写规范
            1、结构化要素
            - **用例编号**：模块_子功能_序列（如PAY_REFUND_001）
            - **前置条件**：明确环境依赖（如数据库版本、第三方服务状态）
            - **测试步骤**：原子化操作（步骤≤7步[7]()）
            - **预期结果**：量化验证点（如响应时间≤2s，数据库记录变更数=1）
            - **优先级**：P0（核心流程）→P3（边缘场景）
            2、是否考虑介入自动化测试
            可脚本化：步骤需支持转化为自动化脚本（如Selenium/Pytest）
            断言精准：包含数据库、日志、UI多维度校验点

            四、用例示例：电商购物车测试用例
            **用例ID**：CART_ADD_ITEM_001
            **标题**：添加商品边界值验证（库存最大值+1）
            **优先级**：P1
            **前置条件**：商品A库存=100
            **步骤**：
            1. 进入商品详情页
            2. 输入购买数量101
            3. 点击"加入购物车"
            **预期结果**：
            - 页面提示"库存不足"
            - 购物车商品数量未更新
            - 后端日志记录库存校验失败事件

            任务完成，输出 FINISHED
        """,
    model_client_stream=True,
)
# 使用输出指定值作为结束条件
text_termination =TextMentionTermination("FINISHED")

# 使用制定方法作为结束条件
source_termination = SourceMatchTermination(sources=['requirements_analyst_format_output'])

team = RoundRobinGroupChat([test_case_origin,requirements_analyst_format_output,requirements_analyst_check], termination_condition=source_termination)



if __name__ == '__main__':
    async def main():
        # result = await get_file_content()
        await Console(team.run_stream(task="帮我进行需求分析，并把需求结果进行格式输出"))
        # print(result)


    asyncio.run(main())