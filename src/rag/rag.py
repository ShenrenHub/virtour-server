import base64
import json
import os
import torch
from openai import OpenAI
from faiss import RandomGenerator
from typing import List, Dict, Any, AsyncGenerator, Generator
from langchain_community.vectorstores import FAISS
from langchain.embeddings.base import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer, AutoModel
from tts.tts_service import generate_speech_xunfei
from tts.tts_service import generate_speech_microsoft

# 加载嵌入模型
class LocalEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        super().__init__()
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.batch_size = 32
        self.max_seq_length = 512

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        texts = [text.replace("\n", " ") for text in texts]
        inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt",
                                max_length=self.max_seq_length).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings.cpu().numpy().tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

# 加载知识库
def load_knowledge_base(file_path: str) -> List[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

# # 创建向量数据库
# def create_vector_db(texts: List[str], embedder: Embeddings):
#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
#     all_splits = text_splitter.create_documents(texts)
#     return FAISS.from_documents(all_splits, embedding=embedder)

def load_db(texts: List[str], embedder: Embeddings, index_path: str = "./vector_store") -> FAISS:
    if os.path.exists(index_path):
        print("正在从本地加载向量数据库...")
        db = FAISS.load_local(index_path, embeddings=embedder)
    else:
        print("本地向量数据库不存在，正在重新构建...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
        all_splits = text_splitter.create_documents(texts)
        db = FAISS.from_documents(all_splits, embedding=embedder)
        db.save_local(index_path)
    return db

# 获取相关上下文
def get_retrieved_context(query: str, db) -> str:
    retrieved_docs = db.similarity_search(query, k=3)
    return "\n".join([doc.page_content for doc in retrieved_docs])

# 构造提示信息
def prepare_prompt_template(question: str, context: str, location: str) -> List[Dict[str, str]]:
    system_instruction_template = """
    请你作为一名专业的{location}导游，带领用户游览相应的地点。你的回复文字不要分点，用连贯、清晰的段落进行描述。

    此外，你有能力带游客去{location}的某个地方，如果游客询问，直接进行相应的肯定回复即可，并附上这个地方的介绍。

    你可以引导游客询问以下的景点：{suggested_spots}。

    如果游客的询问毫无意义，请你回答：
    “对不起，但是您的问题好像和本景点无关，也有可能是我没听清，您能重复一遍吗？”
    """
    with open("../assets/positions.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        spots = [item["name"] for item in data]
        suggested_spots = "、".join(spots)
        location = "颐和园"
        system_instruction = system_instruction_template.format(
            location=location,
            suggested_spots=suggested_spots
        )

        return [
            {"role": "system", "content": system_instruction.strip()},
            {"role": "system", "content": f"上下文: {context}"},
            {"role": "user", "content": question},
        ]

def get_model_answer(query: str) -> AsyncGenerator[str, Any]:
    print("开始向大模型发送问题")
    # 知识库文本路径
    knowledge_file = "./base.txt"
    question = query

    # 加载知识库并创建向量数据库
    knowledge_texts = load_knowledge_base(knowledge_file)
    embedder = LocalEmbeddings(model_name="BAAI/bge-large-en-v1.5")
    index_path = "./vector_store"
    # vector_db = create_vector_db(knowledge_texts, embedder)
    vector_db = load_db(knowledge_texts, embedder, index_path)

    print("知识库加载完成")

    # 检索上下文并获取回答
    context = get_retrieved_context(question, vector_db)
    print("上下文加载完成:", context)
    prompt = prepare_prompt_template(question, '')
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
                print(buffer)
                # Buffer中如果有句号，则从句号截断
                for i in ["。", "？", "！"]:
                    if i in buffer:
                        chunk_id += 1
                        sentence, buffer = buffer.split(i, 1)
                        sentence += i
                        print("sentence截断，开始生成音频", sentence)
                        audio_binary = await generate_speech_microsoft(sentence)
                        # 临时测试: 直接使用本地音频test.wav todo
                        # audio_binary = open("test.wav", "rb").read()
                        # print("音频生成完成", audio_binary)
                        yield json.dumps(
                            {"chunk_id": chunk_id, "text": sentence,
                             "audio": base64.b64encode(audio_binary).decode('utf-8')}) + "\n"

    return event_generator()
