from pathlib import Path
from pypdf import PdfReader


def load_pdf(pdf_path: str) -> str:
    """
    Load all text from a PDF file.
    """

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF file not found: {path}"
        )

    if path.stat().st_size == 0:
        raise ValueError(
            f"PDF file is empty: {path}"
        )

    reader = PdfReader(str(path))

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    full_text = "\n\n".join(pages).strip()

    if not full_text:
        raise ValueError(
            f"No text could be extracted from PDF: {path}"
        )

    return full_text


if __name__ == "__main__":

    base_dir = Path(__file__).resolve().parent.parent
    pdf_path = base_dir / "data" / "sample.pdf"

    print("=" * 60)
    print("PDF LOADER TEST")
    print("=" * 60)

    print()
    print(f"PDF: {pdf_path}")

    try:
        text = load_pdf(str(pdf_path))

        print()
        print("PDF LOADED SUCCESSFULLY")
        print(f"Characters: {len(text)}")

        print()
        print("EXTRACTED TEXT")
        print("-" * 60)
        print(text)

    except Exception as exc:
        print()
        print("PDF LOADER ERROR")
        print(exc)