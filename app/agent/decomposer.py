import json
import re
from typing import Dict, Any, List

from app.agent.llm import ask_llm


# =========================================================
# JSON EXTRACTION
# =========================================================

def extract_json(text: str) -> Dict[str, Any]:
    """
    Extract a JSON object from an LLM response.
    """

    if not text or not text.strip():
        raise ValueError(
            "No JSON object found in LLM response."
        )

    text = text.strip()

    # Remove markdown code fences.
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

    # Find the first JSON object.
    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL,
    )

    if not match:
        raise ValueError(
            "No JSON object found in LLM response."
        )

    return json.loads(match.group(0))


# =========================================================
# FALLBACK DECOMPOSER
# =========================================================

def _fallback_decompose(
    user_query: str,
) -> Dict[str, Any]:
    """
    Deterministic fallback used when the LLM does not
    return usable JSON.

    This keeps decomposition reliable even when the
    LLM response is empty or unavailable.
    """

    query = user_query.strip()
    lower_query = query.lower()

    # -----------------------------------------------------
    # DEADLINES
    # -----------------------------------------------------

    if (
        "deadline" in lower_query
        or "due date" in lower_query
        or "due dates" in lower_query
        or "milestone" in lower_query
    ):

        return {
            "intent": "deadline_analysis",
            "project_name": "",
            "sub_questions": [
                query
            ],
        }

    # -----------------------------------------------------
    # BLOCKERS
    # -----------------------------------------------------

    if (
        "blocker" in lower_query
        or "blocked" in lower_query
        or "blocking" in lower_query
        or "impediment" in lower_query
    ):

        return {
            "intent": "blocker_analysis",
            "project_name": "",
            "sub_questions": [
                query
            ],
        }

    # -----------------------------------------------------
    # TASKS
    # -----------------------------------------------------

    if (
        "task" in lower_query
        or "tasks" in lower_query
        or "issue" in lower_query
        or "issues" in lower_query
    ):

        return {
            "intent": "task_analysis",
            "project_name": "",
            "sub_questions": [
                query
            ],
        }

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    if (
        "status" in lower_query
        or "happening" in lower_query
        or "progress" in lower_query
        or "update" in lower_query
        or "updates" in lower_query
    ):

        return {
            "intent": "project_status",
            "project_name": "",
            "sub_questions": [
                query
            ],
        }

    # -----------------------------------------------------
    # GENERAL PROJECT QUESTION
    # -----------------------------------------------------

    return {
        "intent": "general_project_question",
        "project_name": "",
        "sub_questions": [
            query
        ],
    }


# =========================================================
# DECOMPOSER
# =========================================================

def decompose_query(
    user_query: str,
) -> Dict[str, Any]:
    """
    Break a user's project-management question into
    smaller questions that can be answered using tools.

    If the LLM returns invalid/empty JSON, a deterministic
    fallback is used.
    """

    if not user_query or not user_query.strip():
        raise ValueError(
            "User query cannot be empty."
        )

    prompt = f"""
You are the Query Decomposer for an agentic project-management assistant.

The assistant can eventually retrieve information from:
- Gmail
- Notion
- Jira
- Internal RAG documents

Your job is to analyze the user's request and break it into
the minimum useful set of questions that the agent needs
to investigate.

Identify:

1. intent
2. project_name
3. sub_questions

Possible intents include:
- project_analysis
- project_status
- task_analysis
- deadline_analysis
- blocker_analysis
- general_project_question

Rules:

- Do not answer the user's question.
- Only identify what information needs to be retrieved.
- Keep sub_questions specific and useful.
- Do not create unnecessary questions.
- If the project name is not explicitly provided, use an empty string.
- Return ONLY valid JSON.
- Keep the JSON short.

Required JSON format:

{{
    "intent": "project_analysis",
    "project_name": "Project X",
    "sub_questions": [
        "What are the current project goals?",
        "What tasks are currently active?",
        "What deadlines changed?",
        "What blockers currently exist?"
    ]
}}

User request:
{user_query}
"""

    try:

        response = ask_llm(prompt)

        result = extract_json(response)

    except Exception:

        # LLM failed or returned invalid JSON.
        return _fallback_decompose(
            user_query
        )

    # -----------------------------------------------------
    # VALIDATE FIELDS
    # -----------------------------------------------------

    intent = result.get(
        "intent",
        "",
    )

    project_name = result.get(
        "project_name",
        "",
    )

    sub_questions = result.get(
        "sub_questions",
        [],
    )

    if not isinstance(intent, str):
        return _fallback_decompose(
            user_query
        )

    if not isinstance(project_name, str):
        return _fallback_decompose(
            user_query
        )

    if not isinstance(sub_questions, list):
        return _fallback_decompose(
            user_query
        )

    cleaned_questions: List[str] = []

    for question in sub_questions:

        if (
            isinstance(question, str)
            and question.strip()
        ):

            cleaned_questions.append(
                question.strip()
            )

    if not cleaned_questions:

        return _fallback_decompose(
            user_query
        )

    return {
        "intent": intent.strip(),
        "project_name": project_name.strip(),
        "sub_questions": cleaned_questions,
    }


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    print("=" * 70)
    print("DECOMPOSER TEST")
    print("=" * 70)

    queries = [
        "What is happening with Project X?",
        "What are the current blockers in Project X?",
        "Which deadlines changed for Project X?",
    ]

    for query in queries:

        print()
        print("QUESTION:")
        print(query)

        try:

            result = decompose_query(
                query
            )

            print()
            print("RESULT:")
            print(
                json.dumps(
                    result,
                    indent=4,
                )
            )

        except Exception as exc:

            print()
            print("ERROR:")
            print(exc)