import os
import json
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
from typing import Any
from torch.onnx import export

async def get_mcp_response(query: str) -> str:
    """
    Get response from the DeepSeek API using OpenAI library with tool calling capability.
    """

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        position_path = os.path.join(current_dir, '../assets/positions.json')

        tools = []
        # 定义工具列表，JSON格式，可以用文件定义
        with open(position_path, 'r', encoding='utf-8') as file:
            positions = json.load(file)
        for position in positions:
            tools.append(
                {"type": "function",
                 "function": {"name": position["id"],
                              "description": position["mcp_description"]}}
            )
        # API调用
        # response = client.chat.completions.create(
        #     model="deepseek-chat",#chat对应V3，reasoner对应R1
        #     messages=[{"role": "user", "content": query}],
        #     tools=tools,
        #     tool_choice="auto",
        #     stream=False,
        #     max_tokens=2048,
        # )

        # OPENAI
        # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # response = client.chat.completions.create(
        #     model="gpt-4o-mini",  # chat对应V3，reasoner对应R1
        #     messages=[{"role": "user", "content": query}],
        #     tools=tools,
        #     tool_choice="auto",
        #     stream=False,
        #     max_tokens=2048,
        # )

        # Qwen
        api_key = os.getenv("QWEN_API_KEY")
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": query}],
            tools=tools,
            tool_choice="auto",
            stream=False,
            max_tokens=2048,
        )

        # 处理响应
        choice = response.choices[0]
        print(choice)
        if choice.message.tool_calls:
            tool_call = choice.message.tool_calls[0]
            function_name = tool_call.function.name
            print("尝试调用工具：", function_name)
            return function_name
        return "None"

    except Exception as e:
        return f"Error: An unexpected error occurred - {str(e)}"

async def get_suggestion(query: str) -> str:
    response = await get_mcp_response(query)  # 可以使用不同的接口
    return response


if __name__ == "__main__":
    load_dotenv()
