from typing import Dict, Any, List


# =========================================================
# ALLOWED SOURCES
# =========================================================

SOURCE_NAMES = [
    "jira",
    "gmail",
    "notion",
    "rag",
]


# =========================================================
# EVIDENCE AGGREGATOR
# =========================================================

def aggregate_evidence(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combine all retrieved source results into one structured
    evidence package.

    The executor may return source-specific result lists such as:

        jira_results
        gmail_results
        notion_results
        rag_results

    This function keeps those sources separated while also
    creating one combined evidence list for downstream agents.
    """

    evidence_by_source: Dict[str, List[Any]] = {}

    combined_evidence: List[Dict[str, Any]] = []

    for source in SOURCE_NAMES:

        result_key = f"{source}_results"

        results = state.get(result_key, [])

        if results is None:
            results = []

        if not isinstance(results, list):
            results = [results]

        evidence_by_source[source] = results

        for item in results:

            combined_evidence.append(
                {
                    "source": source,
                    "content": item,
                }
            )

    return {
        **state,

        # -----------------------------------------------------
        # Structured evidence by source
        # -----------------------------------------------------

        "evidence_by_source": evidence_by_source,

        # -----------------------------------------------------
        # Combined evidence
        # -----------------------------------------------------

        "evidence": combined_evidence,

        # -----------------------------------------------------
        # Evidence statistics
        # -----------------------------------------------------

        "evidence_count": len(combined_evidence),

        "sources_with_evidence": [
            source
            for source, results in evidence_by_source.items()
            if results
        ],
    }