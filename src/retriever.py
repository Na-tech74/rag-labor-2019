import chromadb
from sentence_transformers import SentenceTransformer

from src.config import (
    CHROMA_PATH,
    COLLECTION_NAME,
    DEFAULT_TOP_K,
    EMBEDDING_MODEL,
    MAX_DISTANCE,
)

model = SentenceTransformer(EMBEDDING_MODEL)
client = chromadb.PersistentClient(path=str(CHROMA_PATH))
collection = client.get_collection(name=COLLECTION_NAME)


def search(query, top_k=DEFAULT_TOP_K, max_distance=MAX_DISTANCE):
    """
    Vector similarity search:
    1. Encode câu hỏi thành embedding vector
    2. Tìm top_k vectors gần nhất trong ChromaDB
    3. Bỏ kết quả có khoảng cách xa hơn ngưỡng max_distance
    """
    embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    context = []
    for i, document in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i]
        distance = results["distances"][0][i]

        if max_distance is not None and distance > max_distance:
            continue

        context.append({
            "article": metadata.get("article", ""),
            "title": metadata.get("title", ""),
            "page": metadata.get("page") or None,
            "text": document,
            "distance": distance,
        })
    return context


if __name__ == "__main__":
    question = input("Nhập câu hỏi: ")
    results = search(question, top_k=5)
    for i, result in enumerate(results, start=1):
        print("\n" + "=" * 60)
        print(f"#{i}")
        print(f"Điều: {result['article']}")
        print(f"Tiêu đề: {result['title']}")
        print(f"Trang: {result['page']}")
        print(f"Distance: {result['distance']:.4f}")
        print("-" * 60)
        print(result["text"][:1000])
