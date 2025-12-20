# backend/utils/test_gemini_connection.py
import os
import asyncio
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import UserMessage
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
# # --- 1. 配置代理 (根据实际情况调整端口) ---
# os.environ["http_proxy"] = "http://127.0.0.1:7890"
# os.environ["https_proxy"] = "http://127.0.0.1:7890"


async def test_gemini():
    print("1. 正在初始化客户端...")

    # 自动读取环境变量，或者在这里填入
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ 错误: 找不到 GEMINI_API_KEY")
        return

    try:
        # 初始化
        client = OpenAIChatCompletionClient(
            model="gemini-3-pro-preview",
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            timeout=30,

            # 🔥🔥🔥 核心修复：必须加上这个 model_info 参数
            # 告诉 AutoGen：“虽然这不是 GPT-4，但它支持这些功能，请放行”
            model_info={
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "family": "unknown"  # 或者 "gemini"
            }
        )

        print("2. 正在发送请求 (打招呼)...")

        response = await client.create([
            UserMessage(content="你好，请回复'连接成功'这四个字。", source="user")
        ])

        print(f"✅ 3. 连接成功！Gemini 回复:\n{response.content}")

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        # 如果是 404，可能是 base_url 不对或者模型名不对


if __name__ == "__main__":
    asyncio.run(test_gemini())