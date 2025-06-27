from langchain.embeddings.base import Embeddings
from transformers import AutoTokenizer, AutoModel
import torch
from typing import List

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
