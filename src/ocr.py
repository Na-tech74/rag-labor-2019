import os
import re
import shutil
import unicodedata
from pathlib import Path

import pymupdf

from src.config import PDF_PATH, TXT_PATH

# Bản scan -> render ảnh rồi OCR. PDF có text layer thì bỏ qua bước này.
DPI = 200
LANG = "vie+eng"

# Dòng "Điều N" ở đầu dòng của 1 trang PDF (đã bỏ dấu tiếng Việt).
ARTICLE_LINE = re.compile(r"^dieu\s*([^\s.,:;)\]]{1,4})", re.IGNORECASE)

# Tesseract hay nhầm ký tự thành số khi đọc heading.
# Ví dụ bản scan này: "Điều 81." được đọc thành "Điều $1.".
OCR_DIGIT_FIX = str.maketrans({"$": "8", "S": "5", "O": "0", "l": "1", "I": "1", "B": "8", "|": "1"})

# Heading trong TXT đã làm sạch: "### Điều 113. Nghỉ hằng năm".
HEADING_LINE = re.compile(r"^#*\s*Điều\s+(\d+)[.:]")

# Marker đã chèn từ lần chạy trước (chèn lại thì phải gỡ trước).
OLD_MARKER = re.compile(r"(?m)^\[PAGE\s+\d+\][ \t]*\n?")

_TESSERACT_CMD = None


def strip_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt: 'Điều 54.' -> 'Dieu 54.'"""
    text = text.replace("Đ", "D").replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def find_tesseract() -> str:
    """Tìm tesseract: env TESSERACT_CMD -> PATH -> đường dẫn mặc định trên Windows."""
    global _TESSERACT_CMD
    if _TESSERACT_CMD:
        return _TESSERACT_CMD

    env = os.environ.get("TESSERACT_CMD")
    if env and Path(env).exists():
        _TESSERACT_CMD = env
        return env

    which = shutil.which("tesseract")
    if which:
        _TESSERACT_CMD = which
        return which

    # Các vị trí cài đặt phổ biến trên Windows.
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        str(Path(os.environ.get("LOCALAPPDATA", "")) / "Tesseract-OCR" / "tesseract.exe"),
    ]
    for path in candidates:
        if path and Path(path).exists():
            _TESSERACT_CMD = path
            return path

    raise SystemExit(
        "Trang này là bản scan nên cần OCR, nhưng không tìm thấy tesseract.exe.\n"
        "Cài Tesseract (bộ ngôn ngữ vie) rồi đặt biến môi trường TESSERACT_CMD, "
        "hoặc thêm vào PATH."
    )


def ocr_page(page) -> str:
    """Đọc 1 trang bản scan bằng Tesseract."""
    import pytesseract
    from PIL import Image

    pytesseract.pytesseract.tesseract_cmd = find_tesseract()
    pix = page.get_pixmap(dpi=DPI)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return pytesseract.image_to_string(img, lang=LANG)


def collect_candidates(pdf_path: Path = PDF_PATH) -> tuple:
    """
    Đọc PDF -> ({số điều: [các trang có nhắc đến]}, số trang phải OCR).

    Gom TẤT CẢ ứng viên rồi mới chọn, để lọc được các câu nhắc đến Điều
    ở phần thân (vd: "Điều 42" xuất hiện ở trang 14 nhưng Điều 42 bắt đầu ở trang 16).
    """
    doc = pymupdf.open(pdf_path)
    candidates = {}
    scanned = 0

    for page_no, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if text:
            # PDF có text layer -> đọc thẳng, chính xác và không cần Tesseract.
            pass
        else:
            text = ocr_page(page).strip()
            scanned += 1
            print(f"  OCR trang {page_no} (bản scan)...")

        for line in text.splitlines():
            match = ARTICLE_LINE.match(strip_accents(line))
            if match:
                # Chữ "Điều" phải đi kèm số, không thì bỏ qua
                # (tránh nhầm các dòng như "Dieu la...").
                token = match.group(1).translate(OCR_DIGIT_FIX)
                if token.isdigit():
                    candidates.setdefault(int(token), []).append(page_no)

    doc.close()
    return candidates, scanned


def select_pages(candidates: dict) -> tuple:
    """
    Chọn trang mở đầu cho từng Điều.

    Số Điều tăng dần nên số trang cũng phải tăng dần: với mỗi Điều, lấy
    ứng viên đầu tiên không nhỏ hơn trang của Điều trước. Nhờ vậy câu nhắc
    đến Điều ở phần thân (nằm trước trang mở đầu) sẽ bị loại.
    """
    page_map = {}
    ambiguous = []
    prev_page = 0

    for article in sorted(candidates):
        pages = candidates[article]
        ok = [p for p in pages if p >= prev_page]
        page = ok[0] if ok else pages[-1]
        if len(set(pages)) > 1:
            ambiguous.append((article, sorted(set(pages)), page))
        page_map[article] = page
        prev_page = page

    return page_map, ambiguous


def insert_markers(page_map: dict, txt_path: Path = TXT_PATH) -> int:
    """Chèn [PAGE N] ngay trước heading 'Điều N.' trong TXT đã làm sạch."""
    text = OLD_MARKER.sub("", txt_path.read_text(encoding="utf-8"))

    out_lines = []
    added = 0
    for line in text.splitlines():
        match = HEADING_LINE.match(line)
        if match:
            article = int(match.group(1))
            if article in page_map:
                out_lines.append(f"[PAGE {page_map[article]}]")
                added += 1
        out_lines.append(line)

    body = "\n".join(out_lines)
    if text.endswith("\n"):
        body += "\n"
    txt_path.write_text(body, encoding="utf-8")
    return added


def update_pages(pdf_path: Path = PDF_PATH, txt_path: Path = TXT_PATH) -> None:
    candidates, scanned = collect_candidates(pdf_path)
    page_map, ambiguous = select_pages(candidates)
    added = insert_markers(page_map, txt_path)

    print(f"Đã đọc PDF: {pdf_path.name}")
    print(f"Số trang phải OCR: {scanned}")
    print(f"Số Điều tìm thấy số trang: {len(page_map)}")
    print(f"Đã chèn {added} marker [PAGE N] vào: {txt_path.name}")

    if ambiguous:
        print("\nCác Điều được nhắc ở nhiều trang (đã chọn trang mở đầu):")
        for article, pages, chosen in ambiguous:
            print(f"  Điều {article}: ứng viên {pages} -> chọn {chosen}")


if __name__ == "__main__":
    update_pages()
