from typing import Dict, Any, List


def validate_output(
    answer: str,
    evidence: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate the final answer before it is returned to the user.

    The validator checks:
    1. The answer is not empty.
    2. The answer does not contain obvious unsupported claims.
    3. A task marked 'To Do' is not automatically treated as a blocker.
    4. The answer does not claim blockers when the evidence explicitly
       says that no confirmed blocker exists.

    Returns:
        {
            "passed": bool,
            "errors": [...]
        }
    """

    errors: List[str] = []

    # ---------------------------------------------------------
    # BASIC VALIDATION
    # ---------------------------------------------------------

    if not answer or not answer.strip():
        return {
            "passed": False,
            "errors": [
                "Final answer is empty."
            ],
        }

    if not evidence:
        return {
            "passed": False,
            "errors": [
                "No evidence was available for output validation."
            ],
        }

    answer_lower = answer.lower()

    # ---------------------------------------------------------
    # BUILD EVIDENCE TEXT
    # ---------------------------------------------------------

    evidence_text = ""

    for item in evidence:

        if not isinstance(item, dict):
            continue

        for key, value in item.items():

            if value is None:
                continue

            evidence_text += (
                f"{key}: {value}\n"
            )

    evidence_lower = evidence_text.lower()

    # ---------------------------------------------------------
    # CHECK 1:
    # TO DO DOES NOT MEAN BLOCKER
    # ---------------------------------------------------------

    blocker_claims = [
        "is a blocker",
        "are blockers",
        "is currently a blocker",
        "are currently blockers",
        "marked as blocker",
        "marked as blockers",
        "identified as blockers",
        "identified as a blocker",
    ]

    todo_terms = [
        "to do",
        "todo",
        "to-do",
    ]

    has_blocker_claim = any(
        phrase in answer_lower
        for phrase in blocker_claims
    )

    has_todo_evidence = any(
        phrase in evidence_lower
        for phrase in todo_terms
    )

    # If the answer claims ordinary To Do tasks are blockers,
    # reject the output unless the evidence explicitly supports it.

    if has_blocker_claim and has_todo_evidence:

        explicit_blocker_evidence = any(
            phrase in evidence_lower
            for phrase in [
                "confirmed blocker",
                "critical blocker",
                "blocking",
                "blocked",
                "is a blocker",
                "are blockers",
            ]
        )

        if not explicit_blocker_evidence:

            errors.append(
                "The answer appears to treat a 'To Do' task "
                "as a blocker without explicit blocker evidence."
            )

    # ---------------------------------------------------------
    # CHECK 2:
    # EXPLICIT NO-BLOCKER EVIDENCE
    # ---------------------------------------------------------

    no_blocker_phrases = [
        "no confirmed production blocker",
        "no documented critical blocker",
        "no confirmed blocker",
        "no critical blocker",
        "no blocker",
        "no blockers",
    ]

    evidence_says_no_blocker = any(
        phrase in evidence_lower
        for phrase in no_blocker_phrases
    )

    if evidence_says_no_blocker:

        contradictory_claims = [
            "all four issues",
            "all issues are blockers",
            "all tasks are blockers",
            "all listed tasks are blockers",
            "these issues are explicitly identified as blockers",
            "these tasks are blockers",
            "the tasks are blockers",
        ]

        for claim in contradictory_claims:

            if claim in answer_lower:

                errors.append(
                    "The answer contradicts evidence stating "
                    "that no confirmed or documented blocker exists."
                )

                break

    # ---------------------------------------------------------
    # CHECK 3:
    # DO NOT CLAIM DEADLINES WITHOUT EVIDENCE
    # ---------------------------------------------------------

    deadline_claim_terms = [
        "deadline is",
        "deadline:",
        "deadline on",
        "due on",
        "due date is",
        "milestone is",
        "milestone:",
    ]

    has_deadline_claim = any(
        phrase in answer_lower
        for phrase in deadline_claim_terms
    )

    deadline_evidence = any(
        phrase in evidence_lower
        for phrase in [
            "deadline",
            "due_date",
            "due date",
            "milestone",
        ]
    )

    if has_deadline_claim and not deadline_evidence:

        errors.append(
            "The answer appears to contain a deadline or "
            "milestone claim that is not supported by evidence."
        )

    # ---------------------------------------------------------
    # CHECK 4:
    # DO NOT CLAIM COMPLETION WITHOUT EVIDENCE
    # ---------------------------------------------------------

    completion_claim_terms = [
        "completed",
        "finished",
        "successfully completed",
        "has been completed",
        "was completed",
    ]

    has_completion_claim = any(
        phrase in answer_lower
        for phrase in completion_claim_terms
    )

    completion_evidence = any(
        phrase in evidence_lower
        for phrase in [
            "done",
            "completed",
            "closed",
            "resolved",
        ]
    )

    if has_completion_claim and not completion_evidence:

        errors.append(
            "The answer appears to claim task completion "
            "without supporting evidence."
        )

    # ---------------------------------------------------------
    # RESULT
    # ---------------------------------------------------------

    return {
        "passed": len(errors) == 0,
        "errors": errors,
    }


# -------------------------------------------------------------
# DIRECT TEST
# -------------------------------------------------------------

if __name__ == "__main__":

    print("=" * 70)
    print("OUTPUT VALIDATOR TEST")
    print("=" * 70)

    evidence = [
        {
            "source": "rag",
            "content": (
                "The primary technical risk is the "
                "database connection task. "
                "No confirmed production blocker or "
                "critical incident is documented here."
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

    # ---------------------------------------------------------
    # TEST 1 — VALID ANSWER
    # ---------------------------------------------------------

    valid_answer = """
    The primary technical risk is the database connection task.
    KAN-2 is currently To Do.
    No confirmed production blocker is documented.
    """

    result = validate_output(
        answer=valid_answer,
        evidence=evidence,
    )

    print()
    print("TEST 1 — VALID ANSWER")
    print("PASSED:", result["passed"])
    print("ERRORS:", result["errors"])

    # ---------------------------------------------------------
    # TEST 2 — INVALID BLOCKER CLAIM
    # ---------------------------------------------------------

    invalid_answer = """
    KAN-2 is a blocker because it is currently To Do.
    All listed tasks are blockers.
    """

    result = validate_output(
        answer=invalid_answer,
        evidence=evidence,
    )

    print()
    print("TEST 2 — INVALID BLOCKER CLAIM")
    print("PASSED:", result["passed"])
    print("ERRORS:", result["errors"])

    # ---------------------------------------------------------
    # TEST 3 — INVALID DEADLINE CLAIM
    # ---------------------------------------------------------

    deadline_answer = """
    Project X has a deadline on September 20.
    """

    result = validate_output(
        answer=deadline_answer,
        evidence=evidence,
    )

    print()
    print("TEST 3 — UNSUPPORTED DEADLINE")
    print("PASSED:", result["passed"])
    print("ERRORS:", result["errors"])