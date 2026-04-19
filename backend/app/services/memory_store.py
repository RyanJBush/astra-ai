from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings


class SimpleEmbeddings(Embeddings):
    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * 8
        for idx, char in enumerate(text[:256]):
            vector[idx % 8] += (ord(char) % 31) / 31.0
        return vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class MemoryStore:
    def __init__(self) -> None:
        self.embeddings = SimpleEmbeddings()
        self._store = FAISS.from_texts(
            ["seed"],
            embedding=self.embeddings,
            metadatas=[{"seed": True}],
        )

    def add_chunks(self, chunks: list[str], research_id: int, source_url: str) -> None:
        metadatas = [{"research_id": research_id, "source_url": source_url} for _ in chunks]
        self._store.add_texts(chunks, metadatas=metadatas)
