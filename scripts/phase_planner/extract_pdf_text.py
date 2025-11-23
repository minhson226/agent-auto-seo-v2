import sys
from pathlib import Path

from pypdf import PdfReader


def extract_pdf_to_text(pdf_path: str, txt_path: str) -> None:
    pdf_file = Path(pdf_path)
    out_file = Path(txt_path)

    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_file}")

    reader = PdfReader(str(pdf_file))
    pages_text = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        page_header = f"===== PAGE {i + 1} ====="
        pages_text.append(f"{page_header}\n{text.strip()}")

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text("\n\n".join(pages_text), encoding="utf-8")
    print(f"Saved extracted text to {out_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: extract_pdf_text.py INPUT.pdf OUTPUT.txt")
        sys.exit(1)

    extract_pdf_to_text(sys.argv[1], sys.argv[2])
