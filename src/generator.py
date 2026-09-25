import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.1
)

#Hàm tạo sinh câu trả lời
def generate_answer(question, contexts):
    """
    Tạo câu trả lời bằng RAG:
    - Ghép ngữ cảnh từ retrieve thành context_text
    - Gửi prompt ràng buộc Gemini trả lời CHỈ dựa trên ngữ cảnh
    """
    if not contexts:
        return "Không tìm thấy thông tin phù hợp trong Bộ luật Lao động 2019."

    context_text = "\n\n".join(
        f"[{ctx['article']} - {ctx['title']}]\n{ctx['text']}"
        for ctx in contexts
    )

    prompt = f"""
Bạn là trợ lý tra cứu Bộ luật Lao động Việt Nam 2019.

Hãy trả lời câu hỏi CHỈ dựa trên CONTEXT bên dưới.

Quy tắc:
- Không tự bịa thông tin.
- Không sử dụng kiến thức bên ngoài CONTEXT.
- Nếu CONTEXT không đủ thông tin, hãy nói rõ.
- Nếu câu hỏi KHÔNG liên quan đến luật lao động, hãy trả lời: "Câu hỏi này không liên quan đến Bộ luật Lao động 2019."
- Nêu Điều liên quan nếu có.
- Trả lời bằng tiếng Việt.
- Trả lời ngắn gọn, dễ hiểu.

CÂU HỎI:
{question}

CONTEXT:
{context_text}

CÂU TRẢ LỜI:
"""

    try:
        response = llm.invoke(prompt)
        content = response.content

        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            )
        return str(content)

    except Exception as e:
        error_message = str(e)
        
        if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
            return (
                "Gemini API hiện đã hết quota. "
                "Vui lòng thử lại sau khi quota được reset."
            )
            
        if "503" in error_message or "UNAVAILABLE" in error_message:
            return ( "Gemini đang tạm thời quá tải." 
                        " Vui lòng thử lại sau." )
        return f" Không thể tạo ra câu trả lời từ Gemini: {e}"
