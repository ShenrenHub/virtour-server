from typing import Any
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
import asyncio

from torch.onnx import export

# import json

# DeepSeek API 配置
DEEPSEEK_API_KEY = "sk-b1e56df6c0d84ed3baa1f3933c7535d2"
DEEPSEEK_API_BASE = "https://api.deepseek.com"

# 初始化 OpenAI 客户端
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_API_BASE)

mcp = FastMCP("deepseek-v3-interface-demo")


async def get_deepseek_response(query: str) -> str:
    """
    Get response from the DeepSeek API using OpenAI library with tool calling capability.
    """
    try:
        # 定义工具列表
        tools = [
            {"type": "function", "function": {"name": "Never", "description": "Sing 《Never Gonna Give You Up》"}},
            {"type": "function", "function": {"name": "say_goodbye", "description": "Print a goodbye message"}},
            {"type": "function", "function": {"name": "say_something", "description": "Print a custom message"}},
        ]

        # API调用
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": query}],
            tools=tools,
            tool_choice="auto",
            stream=False,
            max_tokens=2048,
        )

        # 处理响应
        choice = response.choices[0]
        if choice.message.tool_calls:
            tool_call = choice.message.tool_calls[0]
            function_name = tool_call.function.name
            if function_name in globals():
                # 异步调用对应的工具函数
                result = await globals()[function_name]({})
                return f"Tool {function_name} called: {result}"
            return f"Unknown tool: {function_name}"
        return choice.message.content

    except Exception as e:
        return f"Error: An unexpected error occurred - {str(e)}"


# 这里我定义了三个简单的示例接口，可以换
@mcp.tool()
async def Never(query: dict) -> str:
    return "Never Gonna Give U Up!!!"


@mcp.tool()
async def say_goodbye(query: dict) -> str:
    """Print a goodbye message."""
    return "Goodbye from the second interface!"


@mcp.tool()
async def say_something(query: dict) -> str:
    """Print a custom message."""
    return "This is a message from the third interface!"


async def MCP_test():
    query = "请唱一下never gonna give you up"
    print(f"我的query是：{query}")

    response = await get_deepseek_response(query)
    print(response)

    query = "请帮我调用say goodbye接口"
    print(f"我的query是：{query}")

    response = await get_deepseek_response(query)
    print(response)

    query = "请帮我调用say something接口"
    print(f"我的query是：{query}")

    response = await get_deepseek_response(query)
    print(response)


async def get_suggestion(query: str) -> str:
    response = await get_deepseek_response(query)
    return response


if __name__ == "__main__":
    asyncio.run(MCP_test())
