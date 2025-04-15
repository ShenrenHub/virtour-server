import os
import asyncio
import edge_tts
import requests
from dotenv import load_dotenv
from pydub import AudioSegment
from io import BytesIO
from tts.text_speech_synthesis import get_mp3_audio_download_link
async def generate_speech_xunfei(prompt_text):
    download_link = get_mp3_audio_download_link(prompt_text)
    # 转换为wav并且return二进制文件
    f = requests.get(download_link)
    audio_data = BytesIO(f.content)
    audio = AudioSegment.from_mp3(audio_data)
    wav_data = BytesIO()
    audio.export(wav_data, format="wav")
    # todo 测试代码 保存wav文件==============
    with open("test.wav", "wb") as wav_file:
        wav_file.write(wav_data.getvalue())
    # todo ===============================
    return wav_data.getvalue()
# 基本功能测试：文本生成语音
async def generate_speech_microsoft(prompt_text):
    # 创建 Communicate 对象
    communicate = edge_tts.Communicate(text=prompt_text, voice="zh-CN-YunxiNeural")
    # 生成语音流

    # 收集音频数据
    audio_data = BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.write(chunk["data"])
    # todo =====================
    audio_data = open("test2.mp3", "rb")
    audio_data = BytesIO(audio_data.read())
    # todo =====================
    # 将 BytesIO 的指针重置到开始
    audio_data.seek(0)

    # 使用 pydub 将 MP3 转换为 WAV
    audio = AudioSegment.from_mp3(audio_data)
    wav_data = BytesIO()
    audio.export(wav_data, format="wav")

    # 返回 WAV 格式的二进制数据
    return wav_data.getvalue()

if __name__ == "__main__":
    audio_binary = asyncio.run(generate_speech_xunfei("你好哇！"))
    print(audio_binary)
