from pathlib import Path
from typing import List, Dict, Any

import chromadb
import numpy as np


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent

CHROMA_PATH = BASE_DIR / "chroma_db"

COLLECTION_NAME = "pdf_documents"


# ---------------------------------------------------------
# CHROMA CLIENT
# ---------------------------------------------------------

def get_chroma_client():
    """
    Create or connect to the persistent ChromaDB client.
    """

    CHROMA_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    return chromadb.PersistentClient(
        path=str(CHROMA_PATH)
    )


# ---------------------------------------------------------
# COLLECTION
# ---------------------------------------------------------

def get_collection():
    """
    Get or create the PDF document collection.
    """

    client = get_chroma_client()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    return collection


# ---------------------------------------------------------
# STORE EMBEDDINGS
# ---------------------------------------------------------

def store_embeddings(
    chunks: List[str],
    embeddings: np.ndarray,
) -> int:
    """
    Store text chunks and their embeddings in ChromaDB.

    Returns:
        Number of chunks stored.
    """

    if not chunks:
        return 0

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Number of chunks must match "
            "number of embeddings."
        )

    collection = get_collection()

    ids = [
        f"chunk_{index}"
        for index in range(len(chunks))
    ]

    # Remove existing test chunks so that
    # repeated ingestion does not create duplicates.
    try:
        collection.delete(
            ids=ids
        )
    except Exception:
        pass

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings.tolist(),
    )

    print(
        f"Stored {len(chunks)} chunks in ChromaDB."
    )

    return len(chunks)


# ---------------------------------------------------------
# SEARCH
# ---------------------------------------------------------

def search(
    query_embedding: np.ndarray,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Search ChromaDB using a query embedding.
    """

    if query_embedding is None:
        raise ValueError(
            "query_embedding cannot be None."
        )

    collection = get_collection()

    count = collection.count()

    if count == 0:
        return []

    top_k = min(
        max(top_k, 1),
        count,
    )

    results = collection.query(
        query_embeddings=[
            query_embedding.tolist()
        ],
        n_results=top_k,
    )

    documents = results.get(
        "documents",
        [[]],
    )[0]

    distances = results.get(
        "distances",
        [[]],
    )[0]

    ids = results.get(
        "ids",
        [[]],
    )[0]

    output = []

    for index, document in enumerate(
        documents
    ):

        output.append(
            {
                "source": "rag",
                "id": (
                    ids[index]
                    if index < len(ids)
                    else None
                ),
                "content": document,
                "distance": (
                    distances[index]
                    if index < len(distances)
                    else None
                ),
            }
        )

    return output


# ---------------------------------------------------------
# COLLECTION INFO
# ---------------------------------------------------------

def collection_count() -> int:
    """
    Return the number of stored documents.
    """

    collection = get_collection()

    return collection.count()


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    from app.pdf_loader import load_pdf
    from app.chunking import split_text
    from app.rag.embeddings import (
        create_embeddings,
        create_query_embedding,
    )

    print("=" * 60)
    print("VECTORSTORE TEST")
    print("=" * 60)

    pdf_path = (
        BASE_DIR
        / "data"
        / "sample.pdf"
    )

    try:

        # ---------------------------------------------
        # LOAD PDF
        # ---------------------------------------------

        text = load_pdf(
            str(pdf_path)
        )

        # ---------------------------------------------
        # CHUNK PDF
        # ---------------------------------------------

        chunks = split_text(
            text,
            chunk_size=500,
            overlap=100,
        )

        print()
        print(
            f"Chunks created: {len(chunks)}"
        )

        # ---------------------------------------------
        # CREATE EMBEDDINGS
        # ---------------------------------------------

        embeddings = create_embeddings(
            chunks
        )

        print()
        print(
            f"Embedding shape: {embeddings.shape}"
        )

        # ---------------------------------------------
        # STORE
        # ---------------------------------------------

        stored = store_embeddings(
            chunks,
            embeddings,
        )

        print()
        print(
            f"Chunks stored: {stored}"
        )

        # ---------------------------------------------
        # SEARCH
        # ---------------------------------------------

        query = (
            "What are the risks and blockers "
            "in Project X?"
        )

        print()
        print(
            f"Query: {query}"
        )

        query_embedding = (
            create_query_embedding(query)
        )

        results = search(
            query_embedding,
            top_k=3,
        )

        print()
        print(
            f"Retrieved results: {len(results)}"
        )

        for index, result in enumerate(
            results,
            start=1,
        ):

            print()
            print(
                f"RESULT {index}"
            )

            print(
                f"ID: {result.get('id')}"
            )

            print(
                f"Distance: {result.get('distance')}"
            )

            print(
                f"Content:\n{result.get('content')}"
            )

        print()
        print(
            f"Collection count: "
            f"{collection_count()}"
        )

    except Exception as exc:

        print()
        print("VECTORSTORE ERROR")
        print(exc)