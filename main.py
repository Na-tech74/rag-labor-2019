from src.generator import generate_answer
from src.retriever import search


def show_answer(answer, status, contexts):
    """In câu trả lời và nguồn tham khảo (nếu có)."""
    print("\n" + "=" * 60)
    print("CÂU TRẢ LỜI")
    print("=" * 60)
    print(answer)

    if status == "ok":
        print("\n" + "=" * 60)
        print("NGUỒN THAM KHẢO")
        print("=" * 60)
        seen = set()
        for ctx in contexts:
            source = f"{ctx['article']} - {ctx['title']}"
            if source in seen:
                continue
            seen.add(source)
            if ctx.get("page"):
                source += f" (trang {ctx['page']})"
            print(f"• {source}")
    elif status == "out_of_domain":
        print("\n(Câu hỏi không liên quan đến Bộ luật Lao động nên không có nguồn.)")
    elif status == "error":
        print("\n(Không có nguồn tham khảo vì Gemini chưa trả lời được.)")
    elif status == "not_found":
        print("\n(Không tìm thấy ngữ cảnh phù hợp trong Bộ luật.)")


def main():
    print("=" * 60)
    print("RAG - BỘ LUẬT LAO ĐỘNG 2019")
    print("=" * 60)

    while True:
        question = input("\nNhập câu hỏi: ").strip()
        if not question:
            print("Vui lòng nhập câu hỏi.")
            continue

        print("\nĐang tra cứu...")
        contexts = search(question)

        print("Đang hỏi Gemini...")
        answer, status = generate_answer(question, contexts)

        show_answer(answer, status, contexts)

        while True:
            choice = input("\nBạn có muốn hỏi câu khác không? (y/n) ").strip().lower()
            if choice in ("y", "yes"):
                break
            if choice in ("n", "no"):
                print("\nCảm ơn bạn đã sử dụng RAG Bộ luật Lao động 2019.")
                print("Chúc bạn một ngày tốt lành!")
                return
            print("Vui lòng nhập 'y' để hỏi tiếp hoặc 'n' để thoát.")


if __name__ == "__main__":
    main()
