from typing import List, Dict, Any

from app.rag.embeddings import create_query_embedding
from app.rag.vectorstore import search


# ---------------------------------------------------------
# RAG SEARCH TOOL
# ---------------------------------------------------------

def search_rag(
    query: str,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Search the project PDF using RAG.

    Pipeline:

        User Question
              ↓
        Query Embedding
              ↓
        ChromaDB
              ↓
        Relevant PDF Chunks
              ↓
        Normalized Evidence
    """

    if not query or not query.strip():
        return []

    # -----------------------------------------------------
    # CREATE QUERY EMBEDDING
    # -----------------------------------------------------

    query_embedding = create_query_embedding(
        query.strip()
    )

    # -----------------------------------------------------
    # SEARCH VECTOR DATABASE
    # -----------------------------------------------------

    results = search(
        query_embedding,
        top_k=top_k,
    )

    # -----------------------------------------------------
    # NORMALIZE RESULTS
    # -----------------------------------------------------

    normalized_results: List[Dict[str, Any]] = []

    for result in results:

        if not isinstance(result, dict):
            continue

        content = result.get(
            "content",
            "",
        )

        if not content:
            continue

        normalized_results.append(
            {
                "source": "rag",
                "id": result.get("id"),
                "content": content,
                "distance": result.get("distance"),
            }
        )

    return normalized_results


# ---------------------------------------------------------
# PROJECT RAG SEARCH
# ---------------------------------------------------------

def search_project_rag(
    query: str,
    project_name: str = "",
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Project-level RAG search used by the Executor.

    project_name is accepted so the Executor can provide
    the project context, while the actual vector search
    is performed using the question.
    """

    if not query or not query.strip():
        return []

    project_name = (
        project_name.strip()
        if isinstance(project_name, str)
        else ""
    )

    # -----------------------------------------------------
    # BUILD PROJECT-AWARE QUERY
    # -----------------------------------------------------

    if project_name:
        rag_query = (
            f"Project: {project_name}\n"
            f"Question: {query.strip()}"
        )
    else:
        rag_query = query.strip()

    results = search_rag(
        rag_query,
        top_k=top_k,
    )

    # -----------------------------------------------------
    # ADD PROJECT CONTEXT TO RESULTS
    # -----------------------------------------------------

    normalized_results: List[Dict[str, Any]] = []

    for result in results:

        if not isinstance(result, dict):
            continue

        normalized_results.append(
            {
                **result,
                "project_name": project_name,
            }
        )

    return normalized_results


# ---------------------------------------------------------
# DIRECT TEST
# ---------------------------------------------------------

def main():

    print("=" * 70)
    print("PROJECT RAG TOOL TEST")
    print("=" * 70)

    project_name = "Project X"

    query = (
        "What are the risks and blockers "
        "in Project X?"
    )

    print()
    print("PROJECT:")
    print(project_name)

    print()
    print("QUERY:")
    print(query)

    print()
    print("Searching project PDF...")

    try:

        results = search_project_rag(
            query=query,
            project_name=project_name,
            top_k=3,
        )

        print()
        print(
            f"Retrieved {len(results)} results."
        )

        for index, result in enumerate(
            results,
            start=1,
        ):

            print()
            print(f"RESULT {index}")
            print("-" * 70)

            print(
                f"ID: {result.get('id')}"
            )

            print(
                f"Distance: {result.get('distance')}"
            )

            print(
                f"Content:\n{result.get('content')}"
            )

    except Exception as exc:

        print()
        print("RAG ERROR")
        print(exc)


if __name__ == "__main__":
    main()