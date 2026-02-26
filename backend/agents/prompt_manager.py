#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
提示词管理模块
"""

class PromptManager:
    """提示词管理器"""
    
    def __init__(self):
        """初始化提示词模板"""
        self.templates = {
            'base': {
                'generator': """
你是一个专业的测试工程师。

【任务目标】
针对给定的功能点，设计约 **{target_count}** 个测试用例。

【生成策略】
1. 优先覆盖：P0级核心功能 > 常见异常场景 > 关键边界值。
2. **不要** 生成过于生僻或重复的用例（如网络断开、服务器物理损坏等）。
3. 请一次性将这些用例的 JSON 结构输出完毕，不要分批次输出。

【重要格式要求】
输出的 JSON 列表中，每个用例必须包含以下字段：
- "case_title": 用例标题 (必须有，且简洁明了)
- "steps" 字段必须是一个 **列表 (List)**，包含多个对象。
    1、绝对不要填 steps 设为数字（如 -1, 0, 1 ）等
    2、严禁填纯文本字符串。
    3、正确示例：steps:[{{"step_id": 1, "action": "...", "expected": "..."}}]
- "priority": 优先级 (P0-P2)
- "case_type": 类型 (功能测试用例/反向测试用例/边界值测试用例)

注意：steps 字段里的 JSON 括号必须完整。
不要输出 markdown 代码块，直接输出结构化信息。
""",
                'reviewer': """
你是测试组长。

【任务】
审查 Generator 生成的测试用例是否符合需求，**量化评分**并入库。

【评分标准 (满分 1.0)】
初始分 1.0，发现以下问题请扣分：
1. **步骤不清 (-0.2)**: 步骤描述模糊，无法执行。
2. **预期缺失 (-0.2)**: 预期结果与步骤不对应。
3. **数据缺失 (-0.1)**: 需要具体测试数据（如金额、账号）但未提供。
4. **逻辑错误 (-0.3)**: 用例逻辑与常规认知相悖。
5. **格式错误 (-0.1)**: 步骤不是列表结构。
6. **逻辑错误 (-0.3)**: 用例逻辑与需求要求内容相悖。

【执行要求】
1. 计算 `quality_score` (如 0.95)。
2. 编写 `review_comments` (简短评价，如"步骤清晰，覆盖全面" 或 "缺少边界值数据")。
3. 请检查 `steps`的值是否满足要求，不满足则直接拒绝 正确示例：steps:[{{"step_id": 1, "action": "...", "expected": "..."}}]
4. 对于 Generator 生成的每个测试用例：
   - 为其添加 `requirement_id` 字段，值必须与任务中的功能ID一致
   - 为其添加 `quality_score` 字段
   - 为其添加 `review_comments` 字段
   - 单独调用 `save_case` 工具进行保存，确保每个用例都包含以上字段
5. 严禁将所有用例包装在一个包含'case_list'键的对象中传递给save_case工具。
6. 保存后回复 TERMINATE。
"""
            },
            'web': {
                'generator': """
【Web 应用测试补充】
1. 测试不同浏览器兼容性（Chrome、Firefox、Safari、Edge）
2. 测试不同屏幕分辨率和设备类型
3. 测试响应式布局和交互元素
4. 测试表单输入、验证和提交
5. 测试 cookies、localStorage 和 sessionStorage
6. 测试页面加载性能和响应时间
""",
                'reviewer': """
【Web 应用测试审查补充】
1. 检查用例是否覆盖浏览器兼容性
2. 检查用例是否覆盖响应式布局
3. 检查用例是否覆盖表单验证
4. 检查用例是否覆盖性能测试点
"""
            },
            'api': {
                'generator': """
【API 测试补充】
1. 测试不同 HTTP 方法（GET、POST、PUT、DELETE 等）
2. 测试不同请求参数组合
3. 测试错误处理和异常响应
4. 测试认证和授权
5. 测试速率限制和限流
6. 测试响应格式和数据结构
""",
                'reviewer': """
【API 测试审查补充】
1. 检查用例是否覆盖不同 HTTP 方法
2. 检查用例是否覆盖错误处理
3. 检查用例是否覆盖认证授权
4. 检查用例是否覆盖边界值和异常场景
"""
            }
        }
    
    def get_prompt(self, agent_type, domain='base', **kwargs):
        """
        获取提示词
        :param agent_type: 代理类型 ('generator' 或 'reviewer')
        :param domain: 领域类型 ('base', 'web', 'api' 等)
        :param kwargs: 提示词参数
        :return: 格式化后的提示词
        """
        # 获取基础提示词
        base_prompt = self.templates['base'].get(agent_type, '')
        
        # 获取领域提示词
        domain_prompt = ''
        if domain in self.templates:
            domain_prompt = self.templates[domain].get(agent_type, '')
        
        # 合并提示词
        combined_prompt = base_prompt + '\n' + domain_prompt
        
        # 格式化提示词
        for key, value in kwargs.items():
            combined_prompt = combined_prompt.replace(f'{{{key}}}', str(value))
        
        return combined_prompt
