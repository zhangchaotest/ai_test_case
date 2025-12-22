# main.py
import asyncio
import sys
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination

# 导入我们的组件
from my_agents import create_test_generator, create_test_reviewer
from old.db_tools import get_all_requirements

# 编码修复
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


async def process_single_requirement(requirement):
    """处理单个需求点的子任务"""

    # 1. 准备数据
    req_id = requirement['id']
    req_desc = f"""
    【当前任务】请为以下功能点编写测试用例，并保存到数据库。
    功能ID: {req_id}
    功能名称: {requirement['feature_name']}
    功能描述: {requirement['description']}

    注意：在调用保存工具时，requirement_id 参数请填 {req_id}。
    """

    print(f"\n🔵 开始处理需求: {requirement['feature_name']} ...")

    # 2. 创建临时团队 (每次处理一个需求都用新实例，保持上下文干净)
    generator = create_test_generator()
    reviewer = create_test_reviewer()

    # 3. 设定终止条件
    termination = TextMentionTermination("TERMINATE")

    # 4. 组队
    team = RoundRobinGroupChat(
        participants=[generator, reviewer],
        termination_condition=termination,
        max_turns=10  # 防止死循环，最多对话10轮
    )

    # 5. 运行
    await team.run(task=req_desc)
    print(f"🟢 需求 [{requirement['feature_name']}] 处理完成。\n")


async def main():
    # 1. 从数据库获取所有待处理的需求
    requirements = get_all_requirements()

    if not requirements:
        print("数据库中没有需求点，请先运行上一步的需求分析。")
        return

    print(f"共发现 {len(requirements)} 个需求点，准备开始生成用例...\n")

    # 2. 循环处理每一个需求
    for req in requirements:
        try:
            await process_single_requirement(req)
        except Exception as e:
            print(f"❌ 处理需求 {req['feature_name']} 时出错: {e}")


if __name__ == "__main__":
    asyncio.run(main())