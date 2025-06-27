# 部署前完成的工作：知识库构建与向量化

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

def build_knowledge_base(
    raw_text_path: str,
    faiss_index_path: str,
    embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    chunk_size: int = 500,
    chunk_overlap: int = 50
):
    """
    构建知识库：文本分段、向量化并存入FAISS
    :param raw_text_path: 原始文本文件路径
    :param faiss_index_path: FAISS索引保存路径
    :param embedding_model_name: 嵌入模型名称
    :param chunk_size: 分段长度
    :param chunk_overlap: 分段重叠
    """
    # 读取原始文本
    with open(raw_text_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 文本分段
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = splitter.create_documents([text])

    # 加载嵌入模型
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)

    # 构建FAISS向量库
    vectorstore = FAISS.from_documents(docs, embeddings)

    # 保存向量库
    vectorstore.save_local(faiss_index_path)
    print(f"知识库已构建并保存到 {faiss_index_path}")
