"""Cấu hình và đường dẫn dùng chung cho cả dự án.

Mọi file trong src/ đều import từ đây thay vì tự khai báo đường dẫn.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

# --- Dữ liệu ---
PDF_PATH = BASE_DIR / "data" / "raw" / "bo-luat-lao-dong-2019.pdf"

# Bản text đã làm sạch. src/ocr.py chèn marker "[PAGE N]" vào đây
# để src/chunker.py tự lấy số trang (không cần file phụ).
TXT_PATH = BASE_DIR / "data" / "processed" / "bo-luat-lao-dong-2019.txt"

# Chunk đã tạo.
JSON_PATH = BASE_DIR / "data" / "processed" / "chunk.json"

# Vector index.
CHROMA_PATH = BASE_DIR / "data" / "index"

# --- Cấu hình index ---
COLLECTION_NAME = "labor_law_2019"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# --- Cấu hình retrieval ---
DEFAULT_TOP_K = 5

# Khoảng cách cosine: 0 = giống hệt, 2 = trái ngược.
# Đo trên thực tế: câu hỏi đúng nằm trong khoảng 0.11 - 0.34,
# câu hỏi ngoài phạm vi nằm trong khoảng 0.71 - 0.84.
# Chọn 0.6 để giữ câu đúng và loại câu hỏi không liên quan.
MAX_DISTANCE = 0.6

# --- Đánh giá ---
QUESTIONS_PATH = BASE_DIR / "evaluation" / "questions.json"
