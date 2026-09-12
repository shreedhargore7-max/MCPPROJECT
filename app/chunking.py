from typing import List


def split_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100,
) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Text extracted from the PDF.
        chunk_size: Maximum number of characters per chunk.
        overlap: Number of characters shared between consecutive chunks.

    Returns:
        A list of text chunks.
    """

    if not text or not text.strip():
        return []

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than 0."
        )

    if overlap < 0:
        raise ValueError(
            "overlap cannot be negative."
        )

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size."
        )

    text = text.strip()

    chunks = []

    start = 0
    text_length = len(text)

    step = chunk_size - overlap

    while start < text_length:

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += step

    return chunks


if __name__ == "__main__":

    from pathlib import Path
    from app.pdf_loader import load_pdf

    print("=" * 60)
    print("CHUNKING TEST")
    print("=" * 60)

    base_dir = Path(__file__).resolve().parent.parent
    pdf_path = base_dir / "data" / "sample.pdf"

    try:

        text = load_pdf(str(pdf_path))

        chunks = split_text(
            text,
            chunk_size=500,
            overlap=100,
        )

        print()
        print(f"Total characters: {len(text)}")
        print(f"Total chunks: {len(chunks)}")

        for index, chunk in enumerate(
            chunks,
            start=1,
        ):

            print()
            print(f"CHUNK {index}")
            print("-" * 60)
            print(chunk)

    except Exception as exc:

        print()
        print("CHUNKING ERROR")
        print(exc)