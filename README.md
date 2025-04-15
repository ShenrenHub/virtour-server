# VirtualTour-Back

## Installation

Python Version: 3.10

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
---

Then, you need to create a file named .env at root dir.
The content should contain keys below.

DEEPSEEK_API_KEY=sk-xxxxxx
XUNFEI_APP_ID=xxxxxx
XUNFEI_API_KEY=xxxxxxx
XUNFEI_API_SECRET=MDJiOWQzxxxxxxxxxx
QWEN_API_KEY=sk-xxxxx
OPENAI_API_KEY=sk-xxxxxxx

## Project Structer
```TEXT
.
├── .venv/
├── mcp_server/
│   └── mcp.py
├── rag/
│   ├── base.txt
│   ├── rag.py
│   └── requirements.txt
├── tts/
│   ├── text_speech_synthesis.py
│   └── tts_service.py
├── .env
├── index.html
├── main.py
├── README.md
└── requirements.txt
```
**.env file is missing, you need create my you own**
