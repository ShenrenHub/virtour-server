import json
from logging import debug
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse
import uvicorn
import asyncio

from openai import BaseModel
from sse_starlette import EventSourceResponse

from mcp_server.mcp import get_suggestion
from rag.rag import get_model_answer, get_fake_model_answer
from tts.speech_to_text import webm_to_wav, speech_to_text, webm_to_wav_pyav
import base64

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


@app.post("/ask")
async def get_answer_stream(request: Request):
    data = await request.json()
    print(data)
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


@app.post("/voice_ask")
async def get_answer_stream_from_voice(request: Request):
    data = await request.json()
    print("data =", data)
    # 1. 获取音频文件
    base64_file = data.get("recording")
    # 移除前缀（如果有的话）
    if base64_file.startswith("data:"):
        base64_file = base64_file.split(",")[1]

    # 解码 base64 数据
    webm_data = base64.b64decode(base64_file)
    # 文件保存到本地
    with open("recording2.webm", "wb") as f:
        f.write(webm_data)
    # 转换为 WAV
    wav_data = webm_to_wav(webm_data)
    # wav保存到本地
    with open("recording.wav", "wb") as f:
        f.write(wav_data)
    # 2. 音频转换为文本
    text = speech_to_text(wav_data)

    query = text
    if not query:
        return {"message": "error"}
    # 使用 StreamingResponse 流式传输 NDJSON 格式数据
    return StreamingResponse(
        get_model_answer(query),
        media_type="application/x-ndjson"
    )


if __name__ == "__main__":
    load_dotenv()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
