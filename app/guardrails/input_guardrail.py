from typing import Dict, Any

from app.agent.llm import ask_llm


def input_guardrail(user_query: str) -> Dict[str, Any]:
    """
    Check whether the user's request is appropriate
    for our project-management agent.

    Returns:
        {
            "allowed": bool,
            "reason": str
        }
    """

    if not user_query or not user_query.strip():
        return {
            "allowed": False,
            "reason": "The user query is empty."
        }

    prompt = f"""
You are the input safety guardrail for an AI project management assistant.

The assistant is designed to help users:
- understand project status
- analyze project tasks
- identify blockers
- identify deadlines
- summarize project information
- analyze information from connected work tools

Determine whether the following user request is appropriate
for this assistant.

User request:
{user_query}

Return ONLY one of these two formats:

ALLOWED
or
BLOCKED

Do not provide any other text.
"""

    try:
        result = ask_llm(prompt).strip().upper()

        if "BLOCKED" in result:
            return {
                "allowed": False,
                "reason": "The request was blocked by the input guardrail."
            }

        return {
            "allowed": True,
            "reason": "The request passed the input guardrail."
        }

    except Exception as exc:
        return {
            "allowed": False,
            "reason": f"Guardrail error: {exc}"
        }