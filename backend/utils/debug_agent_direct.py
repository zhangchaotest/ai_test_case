# backend/debug_agent_direct.py
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from backend.agents.llm_factory import get_gemini_client


async def test_single_agent():
    print("1. 获取 Client...")
    # 使用 flash 模型，速度快
    client = get_gemini_client()

    print("2. 创建 Agent...")
    agent = AssistantAgent(
        name="test_bot",
        model_client=client,
        system_message="你是一个测试助手。请只回复 'Agent 存活确认' 这几个字。"
    )

    print("3. 发送消息...")
    try:
        # 直接运行 run，不走流式，看结果
        result = await agent.run(task="听得到吗？")
        print("-" * 30)
        print(f"🤖 Agent 回复:\n{result.messages[-1].content}")
        print("-" * 30)

        if not result.messages[-1].content:
            print("❌ Agent 回复为空！")
        else:
            print("✅ Agent 正常工作！")

    except Exception as e:
        print(f"❌ 报错: {e}")


if __name__ == "__main__":
    asyncio.run(test_single_agent())