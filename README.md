# virtour-server

<p align="center">
 <img src="https://img.shields.io/github/issues/shenrenhub/virtour-server" />
 <img src="https://img.shields.io/github/forks/shenrenhub/virtour-server" />
 <img src="https://img.shields.io/github/stars/shenrenhub/virtour-server" />
 <img src="https://img.shields.io/github/contributors/shenrenhub/virtour-server" /> 
</p>


这是2025年第十八届中国大学生计算机设计大赛虚拟文旅项目的后端代码库，代码的使用方法请参考本文档。

## 🛠️环境安装

Python Version: 3.10

### 🔧使用Python虚拟环境

---
Linux

```shell
pip -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---
Windows

```cmd
pip -m venv .venv
venv\Scripts\activate
pip install -r requirements.txt
```
Windows下会出现安装FaissGPU报错，可以适当更换其他包。

---

### 🔧使用Anaconda

```shell
conda create -n vitour python=3.10
conda activate vitour
pip install -r requirements.txt
```

## 📌API_KEY配置

`.env` 文件包含了所有的**API_KEY**，请自行在 `/src` 目录创建并按照以下格式填写：

```shell
DEEPSEEK_API_KEY=sk-xxxxxx
XUNFEI_APP_ID=xxxxxx
XUNFEI_API_KEY=xxxxxxx
XUNFEI_API_SECRET=MDJiOWQzxxxxxxxxxx
QWEN_API_KEY=sk-xxxxx
OPENAI_API_KEY=sk-xxxxxxx
```

## 证书配置

因为硬件加速强制要求在安全的网络上下文环境中，故必须采用https进行部署。
将privkey.pem和cert.pem放进src目录中即可。


## 安装语音转文字模型

本项目采用了 [Vosk](https://alphacephei.com/vosk/) 语音识别模型，请下载中文模型并放置在 `src/model` 目录下。

```shell
wget https://alphacephei.com/vosk/models/vosk-model-cn-0.22.zip
unzip vosk-model-cn-0.22.zip
```


## 🗂项目结构

```TEXT
.
├── src/
│   ├── assets/
│   │   ├── panorama/
│   │   ├── preview/
│   │   └── positions.json
│   ├── mcp_server/
│   │   └── mcp_server.py
│   ├── rag/
│   │   ├── base.txt
│   │   └── rag.py
│   ├── tts/
│   │   ├── speech_to_text.py
│   │   ├── text_speech_synthesis.py
│   │   └── tts_service.py
│   ├── .env
│   ├── index.html
│   └── main.py
├── .venv/
├── LICENSE
├── README.md
├── cert.pem
├── privkey.pem
├── README.md
└── requirements.txt
```

## ✅ 待办

- [ ] 整理代码



