import base64
import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from mcp_server.mcp_server import get_suggestion
from rag.rag import get_model_answer
from tts.speech_to_text import webm_to_wav, speech_to_text, convert_webm_bytes_to_wav_bytes

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
    # print(data)
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
    suggestion = await get_suggestion(query)
    print("返回:", {"suggestion": suggestion})
    return {"suggestion": suggestion}


@app.post("/voice_suggest")
async def get_suggest_from_voice(request: Request):
    data = await request.json()
    # print("data =", data)
    base64_file = data.get("recording")
    if base64_file.startswith("data:"):
        base64_file = base64_file.split(",")[1]
    webm_data = base64.b64decode(base64_file)
    with open("recording2.webm", "wb") as f:
        f.write(webm_data)
    wav_data = convert_webm_bytes_to_wav_bytes(webm_data)
    text = speech_to_text(wav_data)
    query = text
    if not query:
        return {"suggestion": "None"}
    # 使用 StreamingResponse 流式传输 NDJSON 格式数据
    suggestion = await get_suggestion(query)
    print("语音建议:", {"suggestion": suggestion})
    return {"suggestion": suggestion}


@app.post("/voice_ask")
async def get_answer_stream_from_voice(request: Request):
    data = await request.json()
    # print("data =", data)
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
    wav_data = convert_webm_bytes_to_wav_bytes(webm_data)
    # wav保存到本地
    # with open("recording.wav", "wb") as f:
    #     f.write(wav_data)
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
    # 检查vosk模型是否存在
    if not os.path.exists("model/vosk-model-cn-0.22"):
        print("请下载Vosk模型到model/vosk-model, 具体请见README")
        exit(1)
    load_dotenv()
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True,
                ssl_keyfile="/home/apricityx/Desktop/Workspace/VirtualTour-Back/privkey.pem",
                ssl_certfile="/home/apricityx/Desktop/Workspace/VirtualTour-Back/cert.pem")
