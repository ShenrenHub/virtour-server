import base64
import io
import json
import os
import subprocess
import wave

import av
import ffmpeg
from dotenv import load_dotenv
from pydub import AudioSegment
from vosk import KaldiRecognizer, Model


# 如果要从init运行,请将src/替换为../
# MODEL_PATH = "model/vosk-model-cn-0.22"
# model = Model(MODEL_PATH)


def webm_to_wav_pyav(webm_data: bytes) -> bytes:
    """
    用 PyAV 将内存中的 WebM（通常是 Opus/Vorbis 音轨）解码并写入 WAV。
    """
    # 1) 打开输入
    in_buf = io.BytesIO(webm_data)
    container = av.open(in_buf, mode='r', format='webm')
    in_stream = container.streams.audio[0]

    # 2) 创建输出 WAV 容器
    out_buf = io.BytesIO()
    out_container = av.open(out_buf, mode='w', format='wav')
    # PCM 16-bit LE 编码
    out_stream = out_container.add_stream('pcm_s16le', rate=in_stream.rate)
    out_stream.channels = in_stream.channels
    out_stream.layout = in_stream.layout

    # 3) 解码 + 编码 + Mux
    for packet in container.demux(in_stream):
        for frame in packet.decode():
            # 清掉时间戳（让编码器重新分配）
            frame.pts = None
            for pkt in out_stream.encode(frame):
                out_container.mux(pkt)

    # flush 编码器
    for pkt in out_stream.encode():
        out_container.mux(pkt)

    # 4) 收尾，取出 bytes
    out_container.close()
    return out_buf.getvalue()


# deprecated
def webm_to_wav(webm_data: bytes) -> bytes:
    # 如果前端传的是 data URI，先去掉前缀并 base64 解码
    if isinstance(webm_data, str) and webm_data.startswith("data:"):
        _, b64 = webm_data.split(",", 1)
        webm_data = base64.b64decode(b64)

    # 指定格式为 'ogg'，因为实际是 OggS 容器
    audio = AudioSegment.from_file(io.BytesIO(webm_data), format="ogg")
    # audio = AudioSegment.from_file(io.BytesIO(webm_data), format="ogg")
    # 转成单声道 16kHz、16bit
    audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
    # 导出 WAV 到内存
    buf = io.BytesIO()
    audio.export(buf, format="wav")
    return buf.getvalue()


def convert_webm_bytes_to_wav_bytes(webm_bytes: bytes) -> bytes:
    """
    将 webm 音频二进制转换为 wav 格式（单声道、16kHz、16bit）的音频二进制
    """
    process = subprocess.Popen(
        [
            'ffmpeg',
            '-i', 'pipe:0',  # 输入来自 stdin
            '-ac', '1',  # 单声道（1 channel）
            '-ar', '16000',  # 采样率 16kHz
            '-sample_fmt', 's16',  # 16-bit PCM
            '-f', 'wav',  # 输出格式为 wav
            'pipe:1'  # 输出到 stdout
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    wav_bytes, error = process.communicate(input=webm_bytes)

    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg 转换失败: {error.decode()}")

    return wav_bytes


def speech_to_text_vosk(wav_data: bytes) -> str:
    """使用 Vosk 将 WAV 音频转换为文字"""
    recognizer = KaldiRecognizer(model, 16000)

    # 打开 WAV 数据
    wf = wave.open(io.BytesIO(wav_data), "rb")
    text = ""
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text += result.get("text", "") + " "

    # 获取最终结果
    final_result = json.loads(recognizer.FinalResult())
    text += final_result.get("text", "")
    print("识别结果:", text)
    return text.strip()


def speech_to_text_baidu(wav_data: bytes) -> str:
    import requests
    url = "https://vop.baidu.com/server_api"

    payload = json.dumps({
        "format": "pcm",
        "rate": 16000,
        "channel": 1,
        "cuid": "HXNHUGUYiQqnD7D4RdOZYDqfWu03uEIx",
        "token": get_baidu_access_token(),
        "speech": base64.b64encode(wav_data).decode('utf-8'),
        "len": len(wav_data),
    }, ensure_ascii=False)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload.encode("utf-8"))

    print("百度识别完成", response.text)
    if response.status_code != 200:
        print("百度语音识别失败:", response.text)
        return "文字识别失败"
    # 解析返回的 JSON 数据
    result = response.json()
    final_text = result["result"][0]
    return final_text


def get_baidu_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    import requests
    load_dotenv()
    url = "https://aip.baidubce.com/oauth/2.0/token"
    baidu_api_key = os.getenv("BAIDU_API_KEY")
    baidu_app_secret = os.getenv("BAIDU_SECRET_KEY")
    print("baidu_api_key:", baidu_api_key)
    print("baidu_app_secret:", baidu_app_secret)
    params = {"grant_type": "client_credentials", "client_id": baidu_api_key,
              "client_secret": baidu_app_secret}
    return str(requests.post(url, params=params).json().get("access_token"))


if __name__ == "__main__":
    # 测试代码
    # 从本地读取microsoft.wav
    test_wav = open("/home/apricityx/Desktop/Workspace/VirtualTour-Back/src/microsoft.wav", "rb").read()
    text = speech_to_text_baidu(test_wav)
    print("识别结果:", text)
    pass
