import os
import json
from typing import List, Dict
from langchain_community.vectorstores import FAISS
from langchain.embeddings.base import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 加载知识库源文件
def load_knowledge_base(file_path: str) -> List[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

# 创建向量数据库
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
    docs = db.similarity_search(query, k=3)
    return "\n".join([doc.page_content for doc in docs])

# 构造prompt信息
def prepare_prompt_template(question: str, context: str) -> List[Dict[str, str]]:
    with open("assets/positions.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    spots = "、".join([item["name"] for item in data])
    location = "颐和园"
    system_instruction = f"""
    请你作为一名专业的{location}导游，带领用户游览相应的地点。你的回复文字不要分点，用连贯、清晰的段落进行描述。

    此外，你有能力带游客去{location}的某个地方，如果游客询问，直接进行相应的肯定回复即可，并附上这个地方的介绍。

    你可以引导游客询问以下的景点：{spots}。

    如果游客的询问毫无意义，请你回答：
    “对不起，但是您的问题好像和本景点无关，也有可能是我没听清，您能重复一遍吗？”
    """
    return [
        {"role": "system", "content": system_instruction.strip()},
        {"role": "system", "content": f"上下文: {context}"},
        {"role": "user", "content": question},
    ]
