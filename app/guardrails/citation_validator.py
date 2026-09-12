from typing import Dict, Any, List


def validate_citations(
    answer: str,
    evidence: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate that the generated answer is supported by
    the retrieved evidence.

    This validator performs basic evidence-grounding checks.
    It does not attempt to determine whether every sentence
    is factually correct using external knowledge.

    Returns:
        {
            "passed": bool,
            "citations": [...],
            "errors": [...]
        }
    """

    errors: List[str] = []
    citations: List[Dict[str, Any]] = []

    if not answer or not answer.strip():
        return {
            "passed": False,
            "citations": [],
            "errors": [
                "Answer is empty."
            ],
        }

    if not evidence:
        return {
            "passed": False,
            "citations": [],
            "errors": [
                "No evidence is available to validate the answer."
            ],
        }

    # ---------------------------------------------------------
    # BUILD EVIDENCE TEXT
    # ---------------------------------------------------------

    evidence_text_parts = []

    for index, item in enumerate(
        evidence,
        start=1,
    ):

        if not isinstance(item, dict):
            continue

        source = item.get(
            "source",
            "unknown",
        )

        content_parts = []

        for key, value in item.items():

            if key == "source":
                continue

            if value is None:
                continue

            content_parts.append(
                f"{key}: {value}"
            )

        evidence_text_parts.append(
            {
                "index": index,
                "source": source,
                "text": " ".join(content_parts),
            }
        )

    if not evidence_text_parts:
        return {
            "passed": False,
            "citations": [],
            "errors": [
                "No valid evidence records are available."
            ],
        }

    # ---------------------------------------------------------
    # FIND SIMPLE EXPLICIT REFERENCES
    # ---------------------------------------------------------

    answer_lower = answer.lower()

    for item in evidence_text_parts:

        evidence_index = item["index"]
        source = item["source"]
        text = item["text"]

        text_lower = text.lower()

        matched_terms = []

        # Jira issue keys
        for token in (
            "kan-1",
            "kan-2",
            "kan-3",
            "kan-4",
            "kan-5",
        ):
            if token in answer_lower and token in text_lower:
                matched_terms.append(token)

        # Common project facts
        important_terms = [
            "database connection",
            "database connectivity",
            "authentication",
            "project documentation",
            "integration",
            "to do",
            "blocker",
            "critical blocker",
            "deadline",
            "milestone",
            "initial development phase",
        ]

        for term in important_terms:

            if (
                term in answer_lower
                and term in text_lower
            ):
                matched_terms.append(term)

        if matched_terms:

            citations.append(
                {
                    "evidence_index": evidence_index,
                    "source": source,
                    "matched_terms": sorted(
                        set(matched_terms)
                    ),
                }
            )

    # ---------------------------------------------------------
    # BASIC GROUNDING CHECK
    # ---------------------------------------------------------

    if not citations:

        errors.append(
            "The answer does not contain any clearly "
            "traceable terms from the retrieved evidence."
        )

    # ---------------------------------------------------------
    # RETURN RESULT
    # ---------------------------------------------------------

    return {
        "passed": len(errors) == 0,
        "citations": citations,
        "errors": errors,
    }


if __name__ == "__main__":

    print("=" * 70)
    print("CITATION VALIDATOR TEST")
    print("=" * 70)

    sample_evidence = [
        {
            "source": "rag",
            "content": (
                "The primary technical risk is the "
                "database connection task."
            ),
        },
        {
            "source": "jira",
            "issue_key": "KAN-2",
            "summary": "Fix database connection",
            "status": "To Do",
            "priority": "Medium",
        },
    ]

    sample_answer = """
    The primary technical risk is the database
    connection task. KAN-2 is currently To Do.
    """

    result = validate_citations(
        answer=sample_answer,
        evidence=sample_evidence,
    )

    print()
    print("PASSED:")
    print(result["passed"])

    print()
    print("CITATIONS:")
    print(result["citations"])

    print()
    print("ERRORS:")
    print(result["errors"])