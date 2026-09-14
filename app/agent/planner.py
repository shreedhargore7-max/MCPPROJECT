import json
import re
from typing import Dict, Any, List

from app.agent.llm import ask_llm


# =========================================================
# ALLOWED SOURCES
# =========================================================

ALLOWED_SOURCES = {
    "gmail",
    "notion",
    "jira",
    "rag",
}


# =========================================================
# JSON EXTRACTION
# =========================================================

def extract_json(text: str) -> Dict[str, Any]:
    """
    Extract a JSON object from an LLM response.
    """

    if not text or not text.strip():
        raise ValueError(
            "No JSON object found in planner response."
        )

    text = text.strip()

    # Remove markdown fences.
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

    return json.loads(
        match.group(0)
    )


# =========================================================
# SOURCE SELECTION FALLBACK
# =========================================================

def _select_sources(
    question: str,
) -> List[str]:
    """
    Deterministically select useful sources for a question.
    """

    q = question.lower()

    sources: List[str] = []

    # -----------------------------------------------------
    # GOALS / REQUIREMENTS
    # -----------------------------------------------------

    if (
        "goal" in q
        or "requirement" in q
        or "requirements" in q
        or "documentation" in q
        or "document" in q
        or "policy" in q
    ):

        sources.extend([
            "notion",
            "rag",
        ])

    # -----------------------------------------------------
    # TASKS
    # -----------------------------------------------------

    if (
        "task" in q
        or "tasks" in q
        or "issue" in q
        or "issues" in q
        or "status" in q
        or "assignee" in q
        or "sprint" in q
    ):

        sources.append(
            "jira"
        )

    # -----------------------------------------------------
    # UPDATES / COMMUNICATION
    # -----------------------------------------------------

    if (
        "update" in q
        or "updates" in q
        or "email" in q
        or "mail" in q
        or "communication" in q
        or "discussion" in q
        or "decision" in q
    ):

        sources.append(
            "gmail"
        )

    # -----------------------------------------------------
    # DEADLINES
    # -----------------------------------------------------

    if (
        "deadline" in q
        or "deadlines" in q
        or "due date" in q
        or "due dates" in q
        or "milestone" in q
        or "milestones" in q
    ):

        sources.extend([
            "jira",
            "notion",
        ])

    # -----------------------------------------------------
    # RISKS
    # -----------------------------------------------------

    if (
        "risk" in q
        or "risks" in q
    ):

        sources.extend([
            "rag",
            "notion",
        ])

    # -----------------------------------------------------
    # BLOCKERS
    # -----------------------------------------------------

    if (
        "blocker" in q
        or "blockers" in q
        or "blocked" in q
        or "blocking" in q
        or "impediment" in q
    ):

        sources.extend([
            "jira",
            "rag",
        ])

    # -----------------------------------------------------
    # GENERAL FALLBACK
    # -----------------------------------------------------

    if not sources:

        sources = [
            "jira",
            "gmail",
            "notion",
            "rag",
        ]

    # Remove duplicates while preserving order.

    unique_sources = []

    for source in sources:

        if source in ALLOWED_SOURCES:
            if source not in unique_sources:
                unique_sources.append(
                    source
                )

    return unique_sources


# =========================================================
# PLAN FALLBACK
# =========================================================

def _fallback_plan(
    project_name: str,
    sub_questions: List[str],
) -> Dict[str, Any]:
    """
    Deterministic planner fallback.

    Used when the LLM returns empty or malformed JSON.
    """

    cleaned_plan = []
    required_sources = []

    for question in sub_questions:

        if not isinstance(
            question,
            str,
        ):
            continue

        question = question.strip()

        if not question:
            continue

        sources = _select_sources(
            question
        )

        if not sources:
            continue

        reason = (
            "Selected sources based on the "
            "type of information requested."
        )

        cleaned_plan.append(
            {
                "question": question,
                "sources": sources,
                "reason": reason,
            }
        )

        for source in sources:

            if source not in required_sources:
                required_sources.append(
                    source
                )

    if not cleaned_plan:
        raise ValueError(
            "Planner did not create a valid execution plan."
        )

    return {
        "plan": cleaned_plan,
        "required_sources": required_sources,
    }


# =========================================================
# CREATE PLAN
# =========================================================

def create_plan(
    project_name: str,
    sub_questions: List[str],
) -> Dict[str, Any]:
    """
    Decide which information sources should be used
    to answer each decomposed question.

    If the LLM response is invalid, the planner falls
    back to deterministic source selection.
    """

    if (
        not project_name
        or not project_name.strip()
    ):

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

The assistant has four information sources:

gmail:
- Recent project communication
- Status updates
- Decisions
- Discussions
- Deadline-change communication
- Risk discussions communicated by email

notion:
- Project goals
- Requirements
- Planning documents
- Meeting notes
- Project documentation
- Official project plans

jira:
- Tasks
- Issues
- Status
- Priority
- Assignees
- Due dates
- Sprint information
- Explicitly recorded blockers

rag:
- Internal PDF/document knowledge
- Risks described in internal documents
- Blockers described in internal documents
- Project documentation contained in PDFs
- Policies
- Reference material
- Requirements contained in internal documents

IMPORTANT:

A Jira task being "To Do" does NOT mean it is a blocker.

A task is a blocker ONLY when retrieved evidence explicitly
identifies it as a blocker or impediment.

Project:
{project_name}

Questions:

{questions_text}

Source selection rules:

- Use the minimum number of useful sources.
- Use more than one source when cross-source information is useful.
- Do not invent sources.
- Every question must have at least one source.
- Use RAG when internal PDF/document knowledge may matter.
- For risk questions, normally consider RAG.
- For blocker questions, normally use Jira and RAG.
- For project goals, prefer Notion and/or RAG.
- For tasks and task status, prefer Jira.
- For recent updates, prefer Gmail.
- For deadlines, prefer Jira and/or Notion.
- Never infer that "To Do" means "blocked".

Return ONLY valid JSON.

Keep the response SHORT.

Required format:

{{
    "plan": [
        {{
            "question": "What are the current risks?",
            "sources": ["rag", "notion"],
            "reason": "These sources may contain documented project risks."
        }}
    ],
    "required_sources": ["rag", "notion"]
}}
"""

    try:

        response = ask_llm(
            prompt
        )

        result = extract_json(
            response
        )

    except Exception:

        return _fallback_plan(
            project_name,
            sub_questions,
        )

    # -----------------------------------------------------
    # VALIDATE PLAN
    # -----------------------------------------------------

    plan = result.get(
        "plan",
        [],
    )

    required_sources = result.get(
        "required_sources",
        [],
    )

    if not isinstance(
        plan,
        list,
    ):

        return _fallback_plan(
            project_name,
            sub_questions,
        )

    if not isinstance(
        required_sources,
        list,
    ):

        return _fallback_plan(
            project_name,
            sub_questions,
        )

    cleaned_plan: List[
        Dict[str, Any]
    ] = []

    discovered_sources = set()

    for item in plan:

        if not isinstance(
            item,
            dict,
        ):
            continue

        question = item.get(
            "question",
            "",
        )

        sources = item.get(
            "sources",
            [],
        )

        reason = item.get(
            "reason",
            "",
        )

        if not isinstance(
            question,
            str,
        ):
            continue

        question = question.strip()

        if not question:
            continue

        if not isinstance(
            sources,
            list,
        ):
            continue

        clean_sources = []

        for source in sources:

            if (
                isinstance(
                    source,
                    str,
                )
                and source.lower()
                in ALLOWED_SOURCES
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
                    if isinstance(
                        reason,
                        str,
                    )
                    else ""
                ),
            }
        )

    # -----------------------------------------------------
    # IF LLM PLAN IS INVALID, FALLBACK
    # -----------------------------------------------------

    if not cleaned_plan:

        return _fallback_plan(
            project_name,
            sub_questions,
        )

    # -----------------------------------------------------
    # REQUIRED SOURCES
    # -----------------------------------------------------

    clean_required_sources = []

    for source in required_sources:

        if (
            isinstance(
                source,
                str,
            )
            and source.lower()
            in ALLOWED_SOURCES
        ):

            source_name = source.lower()

            if (
                source_name
                not in clean_required_sources
            ):

                clean_required_sources.append(
                    source_name
                )

    # Include sources discovered in plan.

    for source in sorted(
        discovered_sources
    ):

        if (
            source
            not in clean_required_sources
        ):

            clean_required_sources.append(
                source
            )

    return {
        "plan": cleaned_plan,
        "required_sources": clean_required_sources,
    }


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    print("=" * 70)
    print("PLANNER TEST")
    print("=" * 70)

    project_name = "Project X"

    sub_questions = [
        "What are the current project goals?",
        "What tasks are currently active?",
        "What updates have occurred recently?",
        "What are the upcoming deadlines?",
        "What blockers currently exist?",
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

        print(
            f"{index}. {question}"
        )

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
            print(
                f"Step {index}"
            )

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
        print(
            result[
                "required_sources"
            ]
        )

    except Exception as exc:

        print()
        print("PLANNER ERROR:")
        print(exc)