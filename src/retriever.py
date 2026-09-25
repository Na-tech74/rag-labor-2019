from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = Path(r"D:\rag-labor-2019\data\index")
COLLECTION_NAME = "labor_law_2019"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

model = SentenceTransformer(MODEL_NAME)
client = chromadb.PersistentClient(path=str(CHROMA_PATH))
collection = client.get_collection(name=COLLECTION_NAME)


def search(query, top_k=5):
    """
    Vector similarity search:
    1. Encode câu hỏi thành embedding vector
    2. Tìm top_k vectors gần nhất trong ChromaDB
    3. Trả về danh sách context (text + metadata)
    """
    embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    context = []
    for i, document in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i]
        distance = results["distances"][0][i]

        context.append({
            "article": metadata.get("article", ""),
            "title": metadata.get("title", ""),
            "page": metadata.get("page"),
            "text": document,
            "distance": distance
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
        print(f"Distance: {result['distance']:.4f}")
        print("-" * 60)
        print(result["text"][:1000])
