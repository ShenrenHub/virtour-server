import json
from logging import debug
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
import uvicorn
import asyncio

from openai import BaseModel
from sse_starlette import EventSourceResponse

from mcp_server.mcp import get_suggestion
from rag.rag import get_model_answer, get_fake_model_answer

# from rag.rag import get_model_answer

app = FastAPI()

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源进行访问，或者指定允许的源，例如：['http://localhost:3000']
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有的 HTTP 方法
    allow_headers=["*"],  # 允许所有的请求头
)


@app.get("/ping")
async def ping():
    return {"ping": "pong"}


# @app.post("/ask")
# async def get_answer_stream(request: Request):
#     data = await request.json()
#     query = data.get("query")
#     if not query:
#         return {"error": "Query is required"}
#     return StreamingResponse(get_model_answer(query), media_type="multipart/mixed; boundary=audio-boundary")
# # 模拟生成器函数，用于分段生成 JSON 数据
# async def get_model_answer(query: str):
#     # 假设这是你的模型回答逻辑，这里我们模拟分段输出
#     chunks = [
#         {"chunk_id": 1, "text": "This is the first part", "audio": "b'audio1"},
#         {"chunk_id": 2, "text": "This is the second part", "audio": "b'audio2"},
#         {"chunk_id": 3, "text": "This is the third part", "audio": "b'audio3"},
#     ]
#     for chunk in chunks:
#         # 将每段数据转为 JSON 字符串并添加换行符
#         yield json.dumps(chunk) + "\n"


@app.post("/ask")
async def get_answer_stream(request: Request):
    data = await request.json()
    query = data.get("query")
    if not query:
        return {"error": "Query is required"}
    # 使用 StreamingResponse 流式传输 NDJSON 格式数据
    return StreamingResponse(
        get_model_answer(query),
        media_type="application/x-ndjson"
    )


@app.post("/suggest", )
async def suggest(request: Request):
    data = await request.json()
    query = data.get("query")
    if not query:
        return {"error": "Query is required"}
    suggestions = await get_suggestion(query)
    return {"suggestions": suggestions}


if __name__ == "__main__":
    load_dotenv()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
