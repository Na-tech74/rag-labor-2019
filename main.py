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
        
    # Chỉ in nguồn tham khảo khi tra lời thành công
    OUT_OF_DOMAIN_MARKER = "không liên quan đến bộ luật lao động"
    
    is_error=(
        isinstance(answer,str) and answer.startswith("Gemini")
    )
    is_out_of_domain =isinstance(answer,str) and OUT_OF_DOMAIN_MARKER in answer.lower()
    if not is_error and not is_out_of_domain:
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
    else:
        if is_error:
            print("\nKhông có nguồn tham khảo vì Gemini chưa trả lời được.")
        elif is_out_of_domain:
            print("(Không có nguồn tham khảo vì câu hỏi không liên quan đến luật lao động.)")   
                 
    # Vòng lập đễ có thể hỏi liên tục
    while True:
        choice = input("\n Chào Bạn ,có muốn hỏi câu khác không ? (y/yes) ").strip().lower()
        if choice in ["y","yes"]:
            print("\nĐược nhé! Bạn cứ nhập câu hỏi tiếp theo.")
            break
        elif choice in ["n", "no"]:
            print("\nCảm ơn bạn đã sử dụng RAG Bộ luật Lao động 2019.")
            print("Chúc bạn một ngày tốt lành!")
            return
        else:
            print("Vui lòng nhập 'y' để hỏi tiếp hoặc 'n' để thoát.")

if __name__ == "__main__":
    main()
