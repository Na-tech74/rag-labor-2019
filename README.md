# RAG - Bộ luật Lao động 2019

Hệ thống hỏi đáp (Q&A) bằng tiếng Việt dựa trên **RAG (Retrieval-Augmented Generation)** cho nội dung Bộ luật Lao động 2019: trích xuất văn bản từ PDF scan → chia chunk theo Điều → tìm kiếm vector → Gemini sinh câu trả lời kèm nguồn tham khảo.

## Kiến trúc

```text
[PDF] → [Đọc/OCR từng trang] → [TXT + marker [PAGE N]] → [Chunking] → [Embedding] → [ChromaDB]
                                                                                      ↓
[Câu hỏi] → [Embedding] → [Vector Search] → [Top-5 chunks]                          ↓
                                                            [Gemini LLM + Context] → [Câu trả lời]
```

| Bước | Script | Mô tả |
|------|--------|-------|
| 1. Trang | `src/ocr.py` | Đọc PDF theo trang (text layer nếu có, không thì OCR Tesseract) → dò heading `Điều N` → **chèn marker `[PAGE N]` vào TXT** |
| 2. Chunk | `src/chunker.py` | TXT → chunks theo từng Điều, lấy số trang từ marker, **gỡ marker trước khi tách** → `chunk.json` |
| 3. Index | `src/indexer.py` | Chunks → embedding → ChromaDB (collection `labor_law_2019`, khoảng cách cosine) |
| 4. Retrieve | `src/retriever.py` | Vector search + lọc kết quả theo ngưỡng khoảng cách `MAX_DISTANCE` |
| 5. Generate | `src/generator.py` | Gemini trả lời **chỉ** dựa trên context được cung cấp |
| 6. App | `main.py` | CLI hỏi đáp |
| 7. Đánh giá | `evaluation/evaluate_retrieval.py` | Đo chất lượng retrieval trên bộ câu hỏi chuẩn |

> Số trang nằm **trong chính file TXT** dưới dạng `[PAGE N]` — không có file phụ nào.
> `src/chunker.py` gỡ marker trước khi tách nên marker không bao giờ lọt vào chunk,
> embedding hay câu trả lời Gemini. Chạy lại `src/ocr.py` bao nhiêu lần cũng được (idempotent).

## Công nghệ

| Package | Vai trò |
|---------|---------|
| langchain-google-genai | Gemini API (`gemini-3.8-flash`, temperature 0.1) |
| chromadb | Vector database (persistent, `data/index/`) |
| sentence-transformers | Embedding local: `paraphrase-multilingual-MiniLM-L12-v2` |
| pymupdf, pytesseract, Pillow | Render trang PDF + OCR lấy số trang |
| python-dotenv | Load API key từ `.env` |

> `requirements.txt` chỉ còn các thư viện thực sự dùng trong code (`langchain-google-genai`, `chromadb`, `sentence-transformers`, `pymupdf`, `pytesseract`, `Pillow`, `python-dotenv`).

## Cấu trúc dự án

```text
rag-labor-2019/
├── main.py                    # Entry point - CLI hỏi đáp
├── requirements.txt
├── .env / .env.example        # GEMINI_API_KEY
│
├── src/
│   ├── config.py               # Đường dẫn + cấu hình dùng chung
│   ├── ocr.py                  # Đọc PDF → xuất file TXT 
│   ├── chunker.py              # TXT → chunks theo Điều (lấy số trang từ marker)
│   ├── indexer.py              # Chunks → embedding → ChromaDB (cosine)
│   ├── retriever.py            # Vector search + lọc theo ngưỡng khoảng cách
│   └── generator.py            # Gemini sinh câu trả lời
│
├── evaluation/
│   ├── questions.json         # 5 câu hỏi + Điều chuẩn (ground truth)
│   ├── evaluate_retrieval.py  # Tính Hit@5, Recall@5, Precision@5, MRR
│   └── flow.txt               # Luồng xử lý + kết quả mẫu
│
├── data/
│   ├── raw/                   # bo-luat-lao-dong-2019.pdf
│   ├── processed/             # bo-luat-lao-dong-2019.txt (có marker [PAGE N]), chunk.json
│   └── index/                 # ChromaDB (chroma.sqlite3)
│
└── Bo_luat_Lao_dong_2019_da_chinh_sua.md
```

## Cài đặt

### 1. Yêu cầu

- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) **chỉ cần khi PDF là bản scan**
  (không có text layer) — có bộ ngôn ngữ `vie` và `eng`.
  PDF số hoá thì `src/ocr.py` đọc thẳng, không cần Tesseract.

```bash
tesseract --version
tesseract --list-langs
```

> `src/ocr.py` tìm tesseract theo thứ tự: biến môi trường `TESSERACT_CMD` → `PATH` →
> `%LOCALAPPDATA%\Tesseract-OCR` → `C:\Program Files\Tesseract-OCR`.

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

### 3. Đường dẫn & cấu hình

Toàn bộ đường dẫn, tên model, tên collection và ngưỡng khoảng cách nằm trong **`src/config.py`**.
Clone dự án về thư mục khác thì không cần sửa gì — đường dẫn tự tính theo vị trí file.

## Sử dụng

### Bước 1 — Ingest (chỉ chạy khi muốn build lại index)

```bash
python -m src.ocr        # Đọc PDF theo trang → chèn marker [PAGE N] vào TXT
python -m src.chunker    # TXT (có marker) → chunk.json (220 chunk, có số trang)
python -m src.indexer    # chunk.json → ChromaDB
```

`data/index/` được gitignore (không nằm trong repo) — cần chạy bước này một lần trước khi hỏi đáp.

> **Số trang:** nằm ngay trong `data/processed/bo-luat-lao-dong-2019.txt` dưới dạng
> `[PAGE N]` phía trên heading `### Điều N.`. `src/chunker.py` tự đọc và gỡ marker
> trước khi tách chunk. Không có file phụ nào, và chạy lại `src/ocr.py` bao nhiêu lần
> cũng không bị trùng marker (nó gỡ marker cũ trước khi chèn lại).

### Bước 2 — Hỏi đáp

```bash
python main.py
```

Ví dụ:

```text
Nhập câu hỏi: Người lao động được nghỉ phép năm bao nhiêu ngày?
```

Kết quả gồm **CÂU TRẢ LỜI** và danh sách **NGUỒN THAM KHẢO** (Điều - tiêu đề - trang).

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
