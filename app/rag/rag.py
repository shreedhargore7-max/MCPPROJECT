from typing import List, Dict, Any

from app.rag.rag_tool import search_rag


# ---------------------------------------------------------
# PROJECT RAG TOOL
# ---------------------------------------------------------

def search_project_rag(
    query: str,
    project_name: str = "",
    max_results: int = 3,
) -> List[Dict[str, Any]]:
    """
    Search the project PDF using the RAG pipeline.

    project_name is accepted for compatibility with the
    agent executor. The actual RAG search is performed
    using the query because the PDF currently contains
    Project X documentation.
    """

    if not query or not query.strip():
        return []

    results = search_rag(
        query=query.strip(),
        top_k=max_results,
    )

    if not isinstance(results, list):
        return []

    normalized_results = []

    for item in results:

        if not isinstance(item, dict):
            continue

        normalized_results.append(
            {
                "source": "rag",
                "project_name": project_name,
                "id": item.get("id"),
                "content": item.get("content", ""),
                "distance": item.get("distance"),
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

    query = "What are the risks and blockers in Project X?"

    print()
    print("QUERY:")
    print(query)

    print()
    print("PROJECT:")
    print("Project X")

    print()
    print("Searching project PDF...")

    try:

        results = search_project_rag(
            query=query,
            project_name="Project X",
            max_results=3,
        )

        print()
        print(f"Retrieved {len(results)} results.")

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
        print("RAG TOOL ERROR")
        print(exc)


if __name__ == "__main__":
    main()