from pathlib import Path
import json
import re

TXT_PATH = Path(r"D:\rag-labor-2019\data\processed\bo-luat-lao-dong-2019.txt")
JSON_PATH = Path(r"D:\rag-labor-2019\data\processed\chunk.json")


def create_chunks():
    """Tách file text Bộ luật Lao động thành các chunks theo từng Điều."""
    text = TXT_PATH.read_text(encoding="utf-8")

    # Tách theo regex tìm vị trí bắt đầu mỗi "Điều X."
    parts = re.split(r"(?=Điều\s*\d+[\.:])", text)

    chunks = []
    for part in parts:
        part = part.strip()
        if not part.startswith("Điều"):
            continue

        match = re.match(r"Điều\s+(\d+)\.\s*(.*)", part)
        if not match:
            continue

        article_number = match.group(1)
        title = match.group(2).split("\n")[0].strip()
        page_match = re.search(r"\[PAGE\s+(\d+)\]", part)
        page = int(page_match.group(1)) if page_match else None

        chunks.append({
            "id": f"chunk_{len(chunks) + 1}",
            "article": f"Điều {article_number}",
            "title": title,
            "page": page,
            "text": part
        })

    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"Đã tạo: {JSON_PATH}")
    print(f"Số chunks: {len(chunks)}")


if __name__ == "__main__":
    create_chunks()
