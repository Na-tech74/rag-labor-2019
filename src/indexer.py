from pathlib import Path
import json

import chromadb
from sentence_transformers import SentenceTransformer

CHUNKS_PATH = Path(r"D:\rag-labor-2019\data\processed\chunk.json")
CHROMA_PATH = Path(r"D:\rag-labor-2019\data\index")
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "labor_law_2019"


def load_chunks():
    """Đọc danh sách chunks từ file JSON."""
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def create_index():
    """Tạo vector index: text → embedding → ChromaDB."""
    chunks = load_chunks()
    print(f"Số chunks: {len(chunks)}")

    print("Đang load embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    documents, ids, metadatas = [], [], []
    for chunk in chunks:
        ids.append(chunk["id"])
        documents.append(chunk["text"])
        metadatas.append({
            "article": chunk.get("article", ""),
            "title": chunk.get("title", ""),
            "page": chunk.get("page", 0)
        })

    #print("Đang tạo embeddings...")
    embeddings = model.encode(documents, show_progress_bar=True)

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings.tolist()
    )

    #print(f"\nĐã lưu vào ChromaDB. Số documents: {collection.count()}")


if __name__ == "__main__":
    create_index()
