from typing import List, Dict, Any

from app.rag.rag_tool import search_rag


# =========================================================
# PROJECT RAG SEARCH
# =========================================================

def search_project_rag(
    query: str,
    top_k: int = 3,
    project_name: str = "",
) -> List[Dict[str, Any]]:
    """
    Search the project PDF using the RAG pipeline.

    Args:
        query:
            Question to search for.

        top_k:
            Number of relevant chunks to retrieve.

        project_name:
            Project name associated with the query.

    Returns:
        List of normalized RAG evidence items.
    """

    # -----------------------------------------------------
    # VALIDATE QUERY
    # -----------------------------------------------------

    if not query or not query.strip():
        return []

    # -----------------------------------------------------
    # BUILD SEARCH QUERY
    # -----------------------------------------------------

    search_query = query.strip()

    if project_name and project_name.strip():

        search_query = (
            f"{project_name.strip()}: "
            f"{search_query}"
        )

    # -----------------------------------------------------
    # SEARCH RAG
    # -----------------------------------------------------

    results = search_rag(
        search_query,
        top_k=top_k,
    )

    # -----------------------------------------------------
    # VALIDATE RESULTS
    # -----------------------------------------------------

    if not isinstance(
        results,
        list,
    ):
        return []

    # -----------------------------------------------------
    # NORMALIZE RESULTS
    # -----------------------------------------------------

    normalized_results: List[
        Dict[str, Any]
    ] = []

    for result in results:

        if not isinstance(
            result,
            dict,
        ):
            continue

        normalized_results.append(
            {
                "source": "rag",
                "project_name": project_name,
                "question": query,
                "id": result.get("id"),
                "content": result.get(
                    "content",
                    "",
                ),
                "distance": result.get(
                    "distance"
                ),
            }
        )

    return normalized_results


# =========================================================
# DIRECT TEST
# =========================================================

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
            f"Retrieved "
            f"{len(results)} results."
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
                "-" * 70
            )

            print(
                f"ID: "
                f"{result.get('id')}"
            )

            print(
                f"Distance: "
                f"{result.get('distance')}"
            )

            print(
                "Content:"
            )

            print(
                result.get(
                    "content",
                    "",
                )
            )

    except Exception as exc:

        print()
        print("=" * 70)
        print("RAG ERROR")
        print("=" * 70)

        print(exc)


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()