from rag.embeddings import LocalEmbeddings
from rag.utils import load_knowledge_base, load_db

embedder = None
vector_db = None

def initialize_resources():
    global embedder, vector_db
    print("初始化中...")
    knowledge_file = "./base.txt"
    index_path = "./vector_store"
    embedder = LocalEmbeddings("BAAI/bge-large-en-v1.5")
    texts = load_knowledge_base(knowledge_file)
    vector_db = load_db(texts, embedder, index_path)
    print("模型和向量数据库初始化完成")
