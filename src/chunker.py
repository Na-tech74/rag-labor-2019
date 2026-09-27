import json
import re

from src.config import JSON_PATH, TXT_PATH

# Chỉ tách chunk khi "Điều N." đứng ở đầu dòng (đầu heading markdown).
# Nhờ vậy không cắt nhầm phần phụ lục của Điều 219
# (ví dụ: **"Điều 54. Điều kiện hưởng lương hưu** thuộc Luật BHXH).
SPLIT_PATTERN = re.compile(r"(?m)^#*\s*(?=Điều\s+\d+[\.:])")
HEADING_PATTERN = re.compile(r"^#*\s*Điều\s+(\d+)\.\s*(.*)")

# Marker trang do src/ocr.py chèn vào TXT: "[PAGE 42]".
PAGE_PATTERN = re.compile(r"^\[PAGE\s+(\d+)\]\s*$")
MARKER_LINE = re.compile(r"(?m)^\[PAGE\s+\d+\][ \t]*\n?")


def build_page_map(text: str) -> dict:
    """
    Quét text có marker -> {số điều: số trang}.

    Marker chỉ có tác dụng khi nằm ngay trước heading; heading không có
    marker thì giữ nguyên None (không đoán mò).
    """
    page_map = {}
    pending = None

    for line in text.splitlines():
        marker = PAGE_PATTERN.match(line)
        if marker:
            pending = int(marker.group(1))
            continue

        heading = HEADING_PATTERN.match(line)
        if heading and pending is not None:
            page_map.setdefault(int(heading.group(1)), pending)
            pending = None

    return page_map


def create_chunks():
    """Tách file text Bộ luật Lao động thành các chunks theo từng Điều."""
    text = TXT_PATH.read_text(encoding="utf-8")
    page_map = build_page_map(text)

    # Gỡ marker trước khi tách -> marker không bao giờ lọt vào chunk.
    parts = SPLIT_PATTERN.split(MARKER_LINE.sub("", text))

    chunks = []
    for part in parts:
        part = part.strip()
        match = HEADING_PATTERN.match(part)
        if not match:
            continue

        article_number = int(match.group(1))
        chunks.append({
            "id": f"chunk_{len(chunks) + 1}",
            "article": f"Điều {article_number}",
            "title": match.group(2).split("\n")[0].strip(),
            "page": page_map.get(article_number),
            "text": part,
        })

    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Đã tạo: {JSON_PATH}")
    print(f"Số chunks: {len(chunks)}")
    print(f"Số chunk có số trang: {sum(1 for c in chunks if c['page'])}")


if __name__ == "__main__":
    create_chunks()
