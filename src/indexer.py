import json

import chromadb
from sentence_transformers import SentenceTransformer

from src.config import (
    CHROMA_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    JSON_PATH,
)


def load_chunks():
    """Đọc danh sách chunks từ file JSON."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def create_index():
    """Tạo vector index: text → embedding → ChromaDB (khoảng cách cosine)."""
    chunks = load_chunks()
    print(f"Số chunks: {len(chunks)}")

    print("Đang load embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    # Xóa index cũ rồi tạo lại với khoảng cách cosine,
    # để giá trị distance nằm trong [0, 2] và so sánh được với ngưỡng MAX_DISTANCE.
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print("Đã xóa index cũ.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    documents, ids, metadatas = [], [], []
    for chunk in chunks:
        ids.append(chunk["id"])
        documents.append(chunk["text"])
        metadatas.append({
            "article": chunk.get("article", ""),
            "title": chunk.get("title", ""),
            "page": int(chunk.get("page") or 0),
        })

    print("Đang tạo embeddings...")
    embeddings = model.encode(documents, show_progress_bar=True)

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings.tolist(),
    )

    print(f"Đã index {collection.count()} chunks vào '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    create_index()
