import os
import json
import asyncio
from openai import OpenAI
from typing import Any
from torch.onnx import export
from mcp.server.fastmcp import FastMCP

# DeepSeek API 配置
DEEPSEEK_API_KEY = "sk-...."
DEEPSEEK_API_BASE = "https://api.deepseek.com"

# 初始化 OpenAI 客户端
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_API_BASE)

mcp = FastMCP("deepseek-v3-interface-demo")
async def get_deepseek_response(query: str) -> str:
    """
    Get response from the DeepSeek API using OpenAI library with tool calling capability.
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, 'tools.json')
        # 定义工具列表，JSON格式，可以用文件定义
        with open(json_path, 'r', encoding='utf-8') as file:
            tools = json.load(file)
        # API调用
        response = client.chat.completions.create(
            model="deepseek-chat",#chat对应V3，reasoner对应R1
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
                result = await globals()[function_name]({})
                return f"Tool {function_name} called: {result}"
            return f"Unknown tool: {function_name}"
        return choice.message.content

    except Exception as e:
        return f"Error: An unexpected error occurred - {str(e)}"


# 接口定义
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
