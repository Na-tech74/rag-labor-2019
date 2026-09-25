from pathlib import Path
import pytesseract
import pymupdf
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Users\ASUS\AppData\Local\Tesseract-OCR\tesseract.exe"
)

PDF_PATH = Path(r"D:\rag-labor-2019\data\raw\bo-luat-lao-dong-2019.pdf")
TXT_PATH = Path(r"D:\rag-labor-2019\data\processed\bo-luat-lao-dong-2019.txt")


def pdf_to_txt(pdf_path: Path, txt_path: Path):
    """
    Pipeline OCR: đọc file PDF → render thành ảnh → OCR trích xuất text → ghi file TXT.
    Mỗi trang được đánh dấu [PAGE X] để sau này biết trang nguồn.
    """
    txt_path.parent.mkdir(parents=True, exist_ok=True)

    document = pymupdf.open(pdf_path)
    pages = []

    print(f"Tổng số trang: {len(document)}")

    for page_number, page in enumerate(document, start=1):
        print(f"OCR page {page_number}/{len(document)}...")

        pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        text = pytesseract.image_to_string(image, lang="vie+eng")
        if text.strip():
            pages.append(f"[PAGE {page_number}]\n{text.strip()}")

    document.close()
    content = "\n\n".join(pages)
    txt_path.write_text(content, encoding="utf-8")

    print(f"\nĐã tạo: {txt_path}")
    print(f"Số trang đọc được: {len(pages)}")
    print(f"Tổng số ký tự: {len(content)}")


if __name__ == "__main__":
    pdf_to_txt(PDF_PATH, TXT_PATH)
