import base64
import json
import os
from pathlib import Path

import torch
from openai import OpenAI
from typing import List, Dict, Any, AsyncGenerator, Generator
from langchain_community.vectorstores import FAISS
from langchain.embeddings.base import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer, AutoModel
from tts.tts_service import generate_speech_xunfei, VoiceTimbre
from tts.tts_service import generate_speech_microsoft
from langchain_huggingface import HuggingFaceEmbeddings

# 构造提示信息
def prepare_prompt_template(question: str, context: str, location: str) -> List[Dict[str, str]]:
    system_instruction_template = """
    请你作为一名专业的{location}导游，带领用户游览相应的地点。你的回复文字不要分点，用连贯、清晰的段落进行描述。

    此外，你有能力带游客去{location}的某个地方，如果游客询问，直接进行相应的肯定回复即可，并附上这个地方的介绍。

    你可以引导游客询问以下的景点：{suggested_spots}。

    如果游客的询问毫无意义，请你回答：
    “对不起，但是您的问题好像和本景点无关，也有可能是我没听清，您能重复一遍吗？”
    """
    location = ''
    current_file_path = Path(__file__).parent.resolve()
    config_path = current_file_path.parent / "assets" / "config.json"
    position_path = current_file_path.parent / "assets" / "positions.json"
    with open(config_path, "r", encoding="utf-8") as file:
        data = json.load(file)
        location = data["location"]
    with open(position_path, "r", encoding="utf-8") as file:
        data = json.load(file)
        spots = [item["name"] for item in data]
        suggested_spots = "、".join(spots)
        system_instruction = system_instruction_template.format(
            location=location,
            suggested_spots=suggested_spots
        )
    result = [
        {"role": "system", "content": system_instruction.strip()},
        {"role": "system", "content": f"上下文: {context}"},
        {"role": "user", "content": question},
    ]
    print("Prompt加载完成", result)
    return result

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
faiss_index_path = Path(__file__).parent.parent / "rag" / "faiss_index"
db = FAISS.load_local(str(faiss_index_path), embeddings, allow_dangerous_deserialization=True)

def get_model_answer(query: str,voice_timbre: VoiceTimbre) -> AsyncGenerator[str, Any]:
    print("开始向大模型发送问题")
    # 知识库文本路径
    question = query
    docs = db.similarity_search(query, k=3)
    context = "\n".join([doc.page_content for doc in docs])
    # 检索上下文并获取回答
    prompt = prepare_prompt_template(question=question, context=context, location="颐和园")
    print("Prompt加载完成")

    # Qwen
    api_key = os.getenv("QWEN_API_KEY")
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model="qwen-plus", messages=prompt, temperature=0, stream=True
    )

    # # DEEPSEEK
    # api_key = os.getenv("DEEPSEEK_API_KEY")
    # client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    #
    # response = client.chat.completions.create(
    #     model="deepseek-chat", messages=prompt, temperature=0, stream=True
    # )

    # # OPENAI
    # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    # response = client.chat.completions.create(
    #     model="gpt-4o-mini", messages=prompt, temperature=0.3, stream=True
    # )

    async def event_generator():
        print("开始流式传输")
        buffer = ""
        chunk_id = 0
        # 流式输出消息
        for chunk in response:
            if chunk.choices[0].delta.content:
                chunk_message = chunk.choices[0].delta.content
                # print("chunk_message", chunk_message)
                # 拦截获取的信息，直到形成一句话，再调用tts api,将音频合并进去发送
                buffer += chunk_message
                # Buffer中如果有句号，则从句号截断
                for i in ["。", "？", "！"]:
                    if i in buffer:
                        chunk_id += 1
                        sentence, buffer = buffer.split(i, 1)
                        sentence += i
                        print("sentence截断，开始生成音频", sentence)
                        audio_binary = await generate_speech_microsoft(sentence, voice_timbre)
                        # 临时测试: 直接使用本地音频test.wav todo
                        # audio_binary = open("test.wav", "rb").read()
                        # print("音频生成完成", audio_binary)
                        yield json.dumps(
                            {"chunk_id": chunk_id, "text": sentence,
                             "audio": base64.b64encode(audio_binary).decode('utf-8')}) + "\n"

    return event_generator()