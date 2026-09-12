import json
import re
from typing import Dict, Any, List

from app.agent.llm import ask_llm


def extract_json(text: str) -> Dict[str, Any]:
    """
    Extract a JSON object from an LLM response.
    """

    text = text.strip()

    # Remove markdown code fences if the model adds them.
    text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```\s*", "", text)

    # Find the first JSON object.
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in LLM response.")

    return json.loads(match.group(0))


def decompose_query(user_query: str) -> Dict[str, Any]:
    """
    Break a user's project-management question into
    smaller questions that can be answered using tools.
    """

    if not user_query or not user_query.strip():
        raise ValueError("User query cannot be empty.")

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

    response = ask_llm(prompt)

    result = extract_json(response)

    # Validate the expected fields.
    intent = result.get("intent", "")
    project_name = result.get("project_name", "")
    sub_questions = result.get("sub_questions", [])

    if not isinstance(intent, str):
        raise ValueError("Invalid intent returned by LLM.")

    if not isinstance(project_name, str):
        raise ValueError("Invalid project_name returned by LLM.")

    if not isinstance(sub_questions, list):
        raise ValueError("sub_questions must be a list.")

    cleaned_questions: List[str] = []

    for question in sub_questions:
        if isinstance(question, str) and question.strip():
            cleaned_questions.append(question.strip())

    if not cleaned_questions:
        raise ValueError(
            "The decomposer did not generate any sub-questions."
        )

    return {
        "intent": intent.strip(),
        "project_name": project_name.strip(),
        "sub_questions": cleaned_questions,
    }