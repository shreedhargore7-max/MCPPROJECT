from typing import Dict, Any, List, Tuple
import json


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
# NORMALIZATION HELPERS
# =========================================================

def _normalize_value(value: Any) -> str:
    """
    Convert a value into a normalized string so that
    semantically identical records can be compared.
    """

    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        try:
            value = json.dumps(
                value,
                sort_keys=True,
                ensure_ascii=False,
            )
        except Exception:
            value = str(value)

    return " ".join(
        str(value)
        .strip()
        .lower()
        .split()
    )


# =========================================================
# DUPLICATE KEY BUILDER
# =========================================================

def _build_duplicate_key(
    source: str,
    item: Any,
) -> Tuple[Any, ...]:
    """
    Build a source-specific key used to identify duplicate
    evidence.

    IMPORTANT:

    Jira:
        Different issue keys are different issues even when
        their summaries are identical.

    Gmail:
        Messages with the same subject and body are treated
        as duplicate evidence.

    Notion:
        The page ID is preferred. Otherwise title/body are used.

    RAG:
        Chunk ID is preferred. Otherwise the content itself
        is used.
    """

    source = _normalize_value(source)

    if not isinstance(item, dict):
        return (
            source,
            _normalize_value(item),
        )

    # =====================================================
    # JIRA
    # =====================================================

    if source == "jira":

        issue_key = item.get("issue_key")

        if issue_key:
            return (
                source,
                "issue",
                _normalize_value(issue_key),
            )

        return (
            source,
            "fallback",
            _normalize_value(
                item.get("summary")
            ),
            _normalize_value(
                item.get("status")
            ),
            _normalize_value(
                item.get("priority")
            ),
        )

    # =====================================================
    # GMAIL
    # =====================================================

    if source == "gmail":

        # A message ID is the strongest identifier when
        # available. However, Gmail searches can sometimes
        # return the same logical update with different IDs.
        #
        # Therefore subject + body is used to identify
        # duplicate evidence.

        subject = _normalize_value(
            item.get("subject")
        )

        body = _normalize_value(
            item.get(
                "body",
                item.get(
                    "snippet",
                    "",
                ),
            )
        )

        if subject or body:
            return (
                source,
                "message_content",
                subject,
                body,
            )

        message_id = item.get(
            "message_id"
        )

        if message_id:
            return (
                source,
                "message_id",
                _normalize_value(
                    message_id
                ),
            )

        return (
            source,
            "fallback",
            _normalize_value(item),
        )

    # =====================================================
    # NOTION
    # =====================================================

    if source == "notion":

        page_id = (
            item.get("id")
            or item.get("page_id")
        )

        if page_id:
            return (
                source,
                "page",
                _normalize_value(page_id),
            )

        title = _normalize_value(
            item.get(
                "title",
                item.get(
                    "name",
                    item.get(
                        "page_title",
                        "",
                    ),
                ),
            )
        )

        body = _normalize_value(
            item.get(
                "body",
                item.get(
                    "content",
                    "",
                ),
            )
        )

        return (
            source,
            "content",
            title,
            body,
        )

    # =====================================================
    # RAG
    # =====================================================

    if source == "rag":

        chunk_id = (
            item.get("id")
            or item.get("chunk_id")
        )

        if chunk_id:
            return (
                source,
                "chunk",
                _normalize_value(chunk_id),
            )

        content = _normalize_value(
            item.get(
                "content",
                item.get(
                    "text",
                    "",
                ),
            )
        )

        return (
            source,
            "content",
            content,
        )

    # =====================================================
    # UNKNOWN SOURCE
    # =====================================================

    return (
        source,
        "fallback",
        _normalize_value(item),
    )


# =========================================================
# DEDUPLICATION
# =========================================================

def _deduplicate_results(
    source: str,
    results: List[Any],
) -> List[Any]:
    """
    Remove duplicate evidence while preserving the original
    order of the results.

    Only the first occurrence of each duplicate is retained.
    """

    unique_results: List[Any] = []
    seen = set()

    for item in results:

        key = _build_duplicate_key(
            source=source,
            item=item,
        )

        if key in seen:
            continue

        seen.add(key)
        unique_results.append(item)

    return unique_results


# =========================================================
# EVIDENCE AGGREGATOR
# =========================================================

def aggregate_evidence(
    state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Combine all retrieved source results into one structured
    evidence package.

    The executor may return source-specific result lists such as:

        jira_results
        gmail_results
        notion_results
        rag_results

    This function:

    1. Keeps each source separated.
    2. Removes duplicate evidence.
    3. Preserves distinct Jira issues.
    4. Creates one combined evidence list.
    5. Calculates evidence statistics.
    """

    evidence_by_source: Dict[str, List[Any]] = {}

    combined_evidence: List[Dict[str, Any]] = []

    for source in SOURCE_NAMES:

        result_key = f"{source}_results"

        results = state.get(
            result_key,
            [],
        )

        if results is None:
            results = []

        if not isinstance(
            results,
            list,
        ):
            results = [results]

        # -------------------------------------------------
        # REMOVE DUPLICATES
        # -------------------------------------------------

        unique_results = _deduplicate_results(
            source=source,
            results=results,
        )

        evidence_by_source[source] = (
            unique_results
        )

        # -------------------------------------------------
        # BUILD COMBINED EVIDENCE
        # -------------------------------------------------

        for item in unique_results:

            combined_evidence.append(
                {
                    "source": source,
                    "content": item,
                }
            )

    # =====================================================
    # RETURN UPDATED STATE
    # =====================================================

    return {
        **state,

        # -------------------------------------------------
        # Structured evidence by source
        # -------------------------------------------------

        "evidence_by_source": (
            evidence_by_source
        ),

        # -------------------------------------------------
        # Combined evidence
        # -------------------------------------------------

        "evidence": combined_evidence,

        # -------------------------------------------------
        # Evidence statistics
        # -------------------------------------------------

        "evidence_count": len(
            combined_evidence
        ),

        "sources_with_evidence": [
            source
            for source, results
            in evidence_by_source.items()
            if results
        ],
    }