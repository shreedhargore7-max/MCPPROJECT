import json
import re
from typing import Dict, Any, List

from app.agent.llm import ask_llm


ALLOWED_SOURCES = {
    "gmail",
    "notion",
    "jira",
    "rag",
}


def extract_json(text: str) -> Dict[str, Any]:
    """
    Extract a JSON object from an LLM response.
    """

    text = text.strip()

    text = re.sub(
        r"```json\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"```\s*",
        "",
        text,
    )

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL,
    )

    if not match:
        raise ValueError(
            "No JSON object found in planner response."
        )

    return json.loads(match.group(0))


def create_plan(
    project_name: str,
    sub_questions: List[str],
) -> Dict[str, Any]:
    """
    Decide which information sources should be used
    to answer each decomposed question.
    """

    if not project_name or not project_name.strip():
        raise ValueError(
            "Project name is required."
        )

    if not sub_questions:
        raise ValueError(
            "At least one sub-question is required."
        )

    questions_text = "\n".join(
        f"{index}. {question}"
        for index, question in enumerate(
            sub_questions,
            start=1,
        )
    )

    prompt = f"""
You are the Planner for an agentic project-management assistant.

Your job is ONLY to create an execution plan.
Do NOT answer the user's questions.

The assistant has four information sources.

SOURCE 1: gmail
Use Gmail for:
- Recent project communication
- Status updates
- Decisions
- Discussions
- Deadline-change communication
- Risk discussions communicated by email

SOURCE 2: notion
Use Notion for:
- Project goals
- Requirements
- Planning documents
- Meeting notes
- Project documentation
- Official project plans

SOURCE 3: jira
Use Jira for:
- Tasks
- Issues
- Status
- Priority
- Assignees
- Due dates
- Sprint information
- Explicitly recorded blockers

IMPORTANT:
Do NOT assume that a Jira task being "To Do" means it is a blocker.
A task is a blocker ONLY when the retrieved evidence explicitly identifies
it as a blocker or impediment.

SOURCE 4: rag
Use RAG for:
- Internal PDF/document knowledge
- Risks described in internal documents
- Blockers described in internal documents
- Project documentation contained in PDFs
- Policies
- Reference material
- Requirements contained in internal documents
- Information that may not exist in Jira, Gmail, or Notion

IMPORTANT RAG RULE:
When a question asks about risks, blockers, technical risks,
internal documentation, requirements, policies, or PDF knowledge,
consider RAG as a relevant source.

Project:
{project_name}

Questions created by the decomposer:

{questions_text}

Create an execution plan.

For every question provide:

1. question
2. sources
3. reason

Use ONLY:

gmail
notion
jira
rag

SOURCE SELECTION RULES:

- Use the minimum number of useful sources.
- You may use more than one source when cross-source information is useful.
- Do not use a source merely because it exists.
- Do not invent sources.
- Do not answer the questions.
- Every question must have at least one source.
- Use RAG when the answer may depend on internal PDF/document knowledge.
- For risk questions, RAG should normally be considered.
- For blocker questions, Jira should normally be used, and RAG should also
  be used when internal documentation may contain blocker information.
- For project goals, prefer Notion and/or RAG.
- For tasks and task status, prefer Jira.
- For recent communication or updates, prefer Gmail.
- For deadlines, prefer Jira and/or Notion.
- Never infer that "To Do" means "blocked".

Return ONLY valid JSON.

Required format:

{{
    "plan": [
        {{
            "question": "What are the current risks?",
            "sources": ["rag", "notion"],
            "reason": "RAG and project documentation may contain documented project risks."
        }},
        {{
            "question": "What are the current blockers?",
            "sources": ["jira", "rag"],
            "reason": "Jira tracks explicit blockers while internal documents may contain documented technical blockers."
        }}
    ],
    "required_sources": ["rag", "notion", "jira"]
}}
"""

    response = ask_llm(prompt)

    result = extract_json(response)

    plan = result.get("plan", [])
    required_sources = result.get(
        "required_sources",
        [],
    )

    if not isinstance(plan, list):
        raise ValueError(
            "Planner 'plan' must be a list."
        )

    if not isinstance(required_sources, list):
        raise ValueError(
            "Planner 'required_sources' must be a list."
        )

    cleaned_plan: List[Dict[str, Any]] = []
    discovered_sources = set()

    for item in plan:

        if not isinstance(item, dict):
            continue

        question = item.get("question", "")
        sources = item.get("sources", [])
        reason = item.get("reason", "")

        if not isinstance(question, str):
            continue

        question = question.strip()

        if not question:
            continue

        if not isinstance(sources, list):
            continue

        clean_sources = []

        for source in sources:

            if (
                isinstance(source, str)
                and source.lower() in ALLOWED_SOURCES
            ):

                source_name = source.lower()

                if source_name not in clean_sources:
                    clean_sources.append(
                        source_name
                    )

                discovered_sources.add(
                    source_name
                )

        if not clean_sources:
            continue

        cleaned_plan.append(
            {
                "question": question,
                "sources": clean_sources,
                "reason": (
                    reason.strip()
                    if isinstance(reason, str)
                    else ""
                ),
            }
        )

    if not cleaned_plan:
        raise ValueError(
            "Planner did not create a valid execution plan."
        )

    clean_required_sources = []

    for source in required_sources:

        if (
            isinstance(source, str)
            and source.lower() in ALLOWED_SOURCES
        ):

            source_name = source.lower()

            if source_name not in clean_required_sources:
                clean_required_sources.append(
                    source_name
                )

    for source in sorted(discovered_sources):

        if source not in clean_required_sources:
            clean_required_sources.append(source)

    return {
        "plan": cleaned_plan,
        "required_sources": clean_required_sources,
    }


def main():
    """
    Direct Planner test.
    """

    print("=" * 70)
    print("PLANNER TEST")
    print("=" * 70)

    project_name = "Project X"

    sub_questions = [
        "What are the current risks?",
        "What are the current blockers?",
    ]

    print()
    print("PROJECT:")
    print(project_name)

    print()
    print("SUB-QUESTIONS:")

    for index, question in enumerate(
        sub_questions,
        start=1,
    ):
        print(f"{index}. {question}")

    print()
    print("Creating execution plan...")

    try:

        result = create_plan(
            project_name,
            sub_questions,
        )

        print()
        print("=" * 70)
        print("EXECUTION PLAN")
        print("=" * 70)

        for index, item in enumerate(
            result["plan"],
            start=1,
        ):

            print()
            print(f"Step {index}")
            print(
                f"Question: {item['question']}"
            )
            print(
                f"Sources: {item['sources']}"
            )
            print(
                f"Reason: {item['reason']}"
            )

        print()
        print("REQUIRED SOURCES:")
        print(result["required_sources"])

    except Exception as exc:

        print()
        print("PLANNER ERROR:")
        print(exc)


if __name__ == "__main__":
    main()