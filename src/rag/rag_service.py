import json
import os
import base64
from openai import OpenAI
from typing import AsyncGenerator, Any
from rag.initializer import embedder, vector_db
from rag.utils import get_retrieved_context, prepare_prompt_template
from tts.tts_service import generate_speech_microsoft

async def get_model_answer(query: str) -> AsyncGenerator[str, Any]:
    if not embedder or not vector_db:
        raise RuntimeError("资源未初始化")

    context = get_retrieved_context(query, vector_db)
    prompt = prepare_prompt_template(query, context)

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
        buffer = ""
        chunk_id = 0
        for chunk in response:
            if chunk.choices[0].delta.content:
                buffer += chunk.choices[0].delta.content
                for sep in ["。", "？", "！"]:
                    if sep in buffer:
                        chunk_id += 1
                        sentence, buffer = buffer.split(sep, 1)
                        sentence += sep
                        audio = await generate_speech_microsoft(sentence)
                        yield json.dumps({
                            "chunk_id": chunk_id,
                            "text": sentence,
                            "audio": base64.b64encode(audio).decode("utf-8")
                        }) + "\n"
    return event_generator()
