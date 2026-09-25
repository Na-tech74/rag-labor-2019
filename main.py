from src.retriever import search
from src.generator import generate_answer


def main():
    print("=" * 60)
    print("RAG - BỘ LUẬT LAO ĐỘNG 2019")
    print("=" * 60)

    question = input("\nNhập câu hỏi: ").strip()
    if not question:
        print("Vui lòng nhập câu hỏi.")
        return

    # BƯỚC 1: RETRIEVAL - Tìm các điều luật liên quan đến câu hỏi
    print("\nĐang tra cứu...")
    contexts = search(question, top_k=5)

    # BƯỚC 2: GENERATION - Gửi câu hỏi + ngữ cảnh cho Gemini sinh câu trả lời
    print("Đang hỏi Gemini...")
    answer = generate_answer(question, contexts)

    print("\n" + "=" * 60)
    print("CÂU TRẢ LỜI")
    print("=" * 60)

    if isinstance(answer, list):
        for item in answer:
            if isinstance(item, dict) and item.get("type") == "text":
                print(item.get("text", ""))
            else:
                print(item)
    else:
        print(answer)

    print("\n" + "=" * 60)
    print("NGUỒN THAM KHẢO")
    print("=" * 60)

    seen = set()
    for ctx in contexts:
        article = ctx.get("article", "")
        title = ctx.get("title", "")
        source = f"{article} - {title}"
        if source not in seen:
            print(f"• {source}")
            seen.add(source)


if __name__ == "__main__":
    main()
