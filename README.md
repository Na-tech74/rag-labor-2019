# RAG - Bộ luật Lao động 2019

Hệ thống hỏi đáp (Q&A) bằng tiếng Việt dựa trên **RAG (Retrieval-Augmented Generation)** cho nội dung Bộ luật Lao động 2019: trích xuất văn bản từ PDF scan → chia chunk theo Điều → tìm kiếm vector → Gemini sinh câu trả lời kèm nguồn tham khảo.

## Kiến trúc

```text
[PDF] → [OCR] → [TXT] → [Chunking] → [Embedding] → [ChromaDB]
                                                        ↓
[Câu hỏi] → [Embedding] → [Vector Search] → [Top-5 chunks]
                                                        ↓
                              [Gemini LLM + Context] → [Câu trả lời]
```

| Bước | Script | Mô tả |
|------|--------|-------|
| 1. OCR | `src/ocr.py` | PDF scan → TXT (PyMuPDF render 2x + Tesseract `vie+eng`, đánh dấu `[PAGE X]`) |
| 2. Chunk | `src/chunker.py` | TXT → chunks theo từng Điều (regex split), lưu `chunk.json` |
| 3. Index | `src/indexer.py` | Chunks → embedding → ChromaDB (collection `labor_law_2019`) |
| 4. Retrieve | `src/retriever.py` | Vector search top-5 chunks liên quan |
| 5. Generate | `src/generator.py` | Gemini trả lời **chỉ** dựa trên context được cung cấp |
| 6. App | `main.py` | CLI hỏi đáp |
| 7. Đánh giá | `evaluation/evaluate_retrieval.py` | Đo chất lượng retrieval trên bộ câu hỏi chuẩn |

## Công nghệ

| Package | Vai trò |
|---------|---------|
| langchain-google-genai | Gemini API (`gemini-3.8-flash`, temperature 0.1) |
| chromadb | Vector database (persistent, `data/index/`) |
| sentence-transformers | Embedding local: `paraphrase-multilingual-MiniLM-L12-v2` |
| pymupdf, pytesseract, Pillow | Đọc PDF & OCR |
| python-dotenv | Load API key từ `.env` |

> `requirements.txt` còn cài `langchain`, `langchain-community`, `rank-bm25`, `streamlit` — hiện chưa được dùng trong code.

## Cấu trúc dự án

```text
rag-labor-2019/
├── main.py                    # Entry point - CLI hỏi đáp
├── requirements.txt
├── .env / .env.example        # GEMINI_API_KEY
│
├── src/
│   ├── ocr.py                 # PDF → TXT (OCR Tesseract)
│   ├── chunker.py             # TXT → chunks theo Điều
│   ├── indexer.py             # Chunks → embedding → ChromaDB
│   ├── retriever.py           # Vector search top-5
│   └── generator.py           # Gemini sinh câu trả lời
│
├── evaluation/
│   ├── questions.json         # 5 câu hỏi + Điều chuẩn (ground truth)
│   ├── evaluate_retrieval.py  # Tính Hit@5, Recall@5, Precision@5, MRR
│   └── flow.txt               # Luồng xử lý + kết quả mẫu
│
├── data/
│   ├── raw/                   # bo-luat-lao-dong-2019.pdf
│   ├── processed/             # bo-luat-lao-dong-2019.txt, chunk.json
│   └── index/                 # ChromaDB (chroma.sqlite3)
│
└── Bo_luat_Lao_dong_2019_da_chinh_sua.md
```

## Cài đặt

### 1. Yêu cầu

- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) cho Windows, có ngôn ngữ `vie` và `eng`

```bash
tesseract --version
tesseract --list-langs
```

### 2. Environment

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

```bash
copy .env.example .env         # rồi điền GEMINI_API_KEY của bạn
```

`.env`:

```env
GEMINI_API_KEY = your_api_key
```

### 3. Đường dẫn cứng (quan trọng)

Các file `src/ocr.py`, `src/chunker.py`, `src/indexer.py`, `src/retriever.py`, `evaluation/evaluate_retrieval.py` đang hardcode đường dẫn tuyệt đối `D:\rag-labor-2019\...`, và `ocr.py` hardcode đường dẫn `tesseract.exe`.

Nếu bạn clone dự án về thư mục khác hoặc cài Tesseract ở chỗ khác, hãy sửa các hằng số này:

- `PDF_PATH`, `TXT_PATH`, `JSON_PATH`, `CHUNKS_PATH`
- `CHROMA_PATH`, `QUESTIONS_PATH`
- `pytesseract.pytesseract.tesseract_cmd`

## Sử dụng

### Bước 1 — Ingest (chỉ chạy khi muốn build lại index)

```bash
python src/ocr.py        # PDF → TXT   (chậm, ~mỗi trang một lần OCR)
python src/chunker.py    # TXT → chunk.json
python src/indexer.py    # chunk.json → ChromaDB
```

Index đã được build sẵn trong `data/index/`, nên mặc định có thể bỏ qua bước này.

### Bước 2 — Hỏi đáp

```bash
python main.py
```

Ví dụ:

```text
Nhập câu hỏi: Người lao động được nghỉ phép năm bao nhiêu ngày?
```

Kết quả gồm **CÂU TRẢ LỜI** và danh sách **NGUỒN THAM KHẢO** (Điều - tiêu đề).

Chỉ xem top-5 chunks mà không gọi LLM:

```bash
python src/retriever.py
```

## Đánh giá retrieval

Đo chất lượng bước tìm kiếm (chưa tính LLM) trên bộ 5 câu hỏi chuẩn trong `evaluation/questions.json`:

```bash
python evaluation/evaluate_retrieval.py
```

Các chỉ số với `k = 5`:

| Chỉ số | Ý nghĩa |
|--------|---------|
| Hit@5 | Câu hỏi có ít nhất 1 Điều đúng trong top-5 không (0/1) |
| Recall@5 | Tỷ lệ Điều đúng được tìm thấy trong top-5 |
| Precision@5 | Tỷ lệ kết quả top-5 là Điều đúng |
| MRR | Ngược đãi hạng của kết quả đúng đầu tiên (1/rank) |

Kết quả mẫu (xem đầy đủ trong `evaluation/flow.txt`): 4/5 câu hit, câu hụt là *"Người lao động có quyền đơn phương chấm dứt hợp đồng lao động không?"* — retriever trả về Điều 37/36/38 thay vì Điều 35.

## Nguyên tắc sinh câu trả lời

Prompt trong `src/generator.py` ràng buộc Gemini:

- Trả lời **chỉ** dựa trên CONTEXT được retriever cung cấp, không tự bịa.
- Nếu CONTEXT không đủ thông tin, nói rõ là chưa đủ.
- Nêu Điều liên quan, trả lời bằng tiếng Việt, ngắn gọn.
- Không có context nào phù hợp → trả lời *"Không tìm thấy thông tin phù hợp trong Bộ luật Lao động 2019."*

## Ghi chú

- Dự án phục vụ mục đích tra cứu/tham khảo, **không phải tư vấn pháp lý**.
- Bộ luật có thể được sửa đổi, đối chiếu với văn bản chính thức tại [vanban.chinhphu.vn](https://vanban.chinhphu.vn).
