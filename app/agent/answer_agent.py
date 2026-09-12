from typing import Dict, Any, List

from app.agent.llm import ask_llm


def build_evidence_text(
    evidence: List[Dict[str, Any]]
) -> str:
    """
    Convert collected evidence into text that the LLM
    can understand.
    """

    if not evidence:
        return "No evidence was retrieved."

    sections = []

    for index, item in enumerate(evidence, start=1):

        if not isinstance(item, dict):
            continue

        source = item.get(
            "source",
            "unknown",
        )

        lines = [
            f"Evidence {index}",
            f"Source: {source}",
        ]

        for key, value in item.items():

            if key == "source":
                continue

            if value is None:
                continue

            if isinstance(value, (dict, list)):
                value = str(value)

            lines.append(
                f"{key}: {value}"
            )

        sections.append(
            "\n".join(lines)
        )

    if not sections:
        return "No valid evidence was retrieved."

    return "\n\n".join(sections)


def generate_answer(
    user_query: str,
    evidence: List[Dict[str, Any]],
) -> str:
    """
    Generate a final answer using ONLY retrieved evidence.

    Important grounding rules:
    - A Jira 'To Do' task is NOT automatically a blocker.
    - A risk is NOT automatically a blocker.
    - A task can only be called a blocker when the evidence
      explicitly identifies it as a blocker.
    """

    if not user_query or not user_query.strip():
        raise ValueError(
            "User query cannot be empty."
        )

    evidence_text = build_evidence_text(
        evidence
    )

    prompt = f"""
You are the Answer Agent in an agentic
project-management assistant.

Your job is to answer the user's question
using ONLY the retrieved evidence.

STRICT GROUNDING RULES:

1. Never invent facts.
2. Never infer information that is not explicitly
   supported by the evidence.
3. A Jira task with status "To Do" is NOT automatically
   a blocker.
4. A Jira task is a blocker ONLY when the evidence
   explicitly identifies it as a blocker.
5. A risk is NOT automatically a blocker.
6. If the evidence says there is no confirmed,
   documented, or critical blocker, report that clearly.
7. Do not convert planned work into blockers.
8. Do not convert technical requirements into risks
   unless the evidence explicitly describes them as risks.
9. Do not create deadlines or milestones unless they
   are explicitly supported by evidence.
10. If different sources disagree, report the disagreement
    rather than choosing one without explanation.
11. If information is missing, say:
    "Not found in the retrieved evidence."

User question:
{user_query}

Retrieved evidence:
{evidence_text}

Answer requirements:

- Directly answer the user's question.
- Separate RISKS, BLOCKERS, TASKS, DEADLINES,
  and OTHER INFORMATION when relevant.
- For risks, only report risks explicitly supported
  by the evidence.
- For blockers, only report explicitly documented
  blockers.
- Do NOT call a "To Do" task a blocker unless the
  evidence explicitly says it is a blocker.
- If no blocker is documented, say:
  "No confirmed/documented blockers were found
   in the retrieved evidence."
- Keep the answer concise and useful.
- Do not mention evidence numbers unless useful.
- Return ONLY the final answer.

User question:
{user_query}

Retrieved evidence:
{evidence_text}
"""

    return ask_llm(prompt).strip()


def answer_agent(
    state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Answer Agent node for the LangGraph workflow.

    The Answer Agent uses REDACTED evidence only.
    """

    user_query = state.get(
        "user_query",
        "",
    )

    evidence = state.get(
        "redacted_evidence",
        [],
    )

    try:

        answer = generate_answer(
            user_query=user_query,
            evidence=evidence,
        )

        return {
            **state,
            "answer": answer,
            "error": None,
        }

    except Exception as exc:

        return {
            **state,
            "answer": "",
            "error": (
                f"Answer generation failed: {exc}"
            ),
        }


def main():

    print("=" * 70)
    print("ANSWER AGENT TEST")
    print("=" * 70)

    sample_evidence = [
        {
            "source": "rag",
            "content": (
                "The primary technical risk identified "
                "for the initial development phase is "
                "the database connection task. "
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

    query = (
        "What are the risks and blockers "
        "in Project X?"
    )

    print()
    print("Generating answer...")
    print()

    answer = generate_answer(
        user_query=query,
        evidence=sample_evidence,
    )

    print("=" * 70)
    print("ANSWER")
    print("=" * 70)

    print()
    print(answer)


if __name__ == "__main__":
    main()