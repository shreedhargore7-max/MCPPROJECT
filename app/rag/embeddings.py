from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


# =========================================================
# CONFIGURATION
# =========================================================

MODEL_NAME = "all-MiniLM-L6-v2"

EMBEDDING_DIMENSION = 384


# =========================================================
# EMBEDDING MODEL
# =========================================================

_model = None


def get_embedding_model():
    """
    Load the embedding model once and reuse it.

    The model is stored globally so that repeated RAG
    queries do not reload the model.
    """

    global _model

    if _model is None:

        print(
            f"Loading embedding model: {MODEL_NAME}"
        )

        _model = SentenceTransformer(
            MODEL_NAME
        )

        print(
            "Embedding model loaded successfully."
        )

    return _model


# =========================================================
# CREATE EMBEDDINGS
# =========================================================

def create_embeddings(
    chunks: List[str],
) -> np.ndarray:
    """
    Convert multiple text chunks into vector embeddings.

    Args:
        chunks:
            List of text chunks.

    Returns:
        NumPy array containing embeddings.
    """

    if not chunks:

        return np.empty(
            (
                0,
                EMBEDDING_DIMENSION,
            ),
            dtype=np.float32,
        )

    model = get_embedding_model()

    embeddings = model.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return embeddings.astype(
        np.float32
    )


# =========================================================
# SINGLE QUERY EMBEDDING
# =========================================================

def create_query_embedding(
    query: str,
) -> np.ndarray:
    """
    Convert a user query into a single vector embedding.

    Args:
        query:
            User's search query.

    Returns:
        NumPy array containing the query embedding.
    """

    if not query or not query.strip():

        raise ValueError(
            "Query cannot be empty."
        )

    model = get_embedding_model()

    embedding = model.encode(
        query.strip(),
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return embedding.astype(
        np.float32
    )


# =========================================================
# DIRECT TEST
# =========================================================

if __name__ == "__main__":

    from pathlib import Path

    from app.pdf_loader import load_pdf
    from app.chunking import split_text

    print("=" * 60)
    print("EMBEDDING TEST")
    print("=" * 60)

    # -----------------------------------------------------
    # PROJECT ROOT
    # -----------------------------------------------------

    base_dir = (
        Path(__file__)
        .resolve()
        .parent
        .parent
        .parent
    )

    pdf_path = (
        base_dir
        / "data"
        / "sample.pdf"
    )

    print()
    print(
        f"PDF: {pdf_path}"
    )

    try:

        # -------------------------------------------------
        # LOAD PDF
        # -------------------------------------------------

        text = load_pdf(
            str(pdf_path)
        )

        print()
        print(
            f"Characters: {len(text)}"
        )

        # -------------------------------------------------
        # CHUNK TEXT
        # -------------------------------------------------

        chunks = split_text(
            text,
            chunk_size=500,
            overlap=100,
        )

        print()
        print(
            f"Chunks: {len(chunks)}"
        )

        # -------------------------------------------------
        # CREATE EMBEDDINGS
        # -------------------------------------------------

        embeddings = create_embeddings(
            chunks
        )

        print()
        print(
            "EMBEDDINGS CREATED"
        )

        print(
            f"Shape: {embeddings.shape}"
        )

        # -------------------------------------------------
        # QUERY EMBEDDING
        # -------------------------------------------------

        query = (
            "What are the risks and blockers "
            "in Project X?"
        )

        query_embedding = (
            create_query_embedding(
                query
            )
        )

        print()
        print(
            "QUERY EMBEDDING CREATED"
        )

        print(
            f"Query shape: "
            f"{query_embedding.shape}"
        )

        print()
        print("=" * 60)
        print("EMBEDDING TEST COMPLETE")
        print("=" * 60)

    except Exception as exc:

        print()
        print("=" * 60)
        print("EMBEDDING ERROR")
        print("=" * 60)

        print(exc)