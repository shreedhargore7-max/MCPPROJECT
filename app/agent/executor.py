from typing import Dict, Any, List

from app.agent.state import AgentState

from app.tools.jira import get_project_issues
from app.tools.notion import search_notion
from app.tools.gmail import search_project_emails
from app.tools.rag import search_project_rag


# ---------------------------------------------------------
# EXECUTE PLAN
# ---------------------------------------------------------

def execute_plan(state: AgentState) -> AgentState:
    """
    Execute the planner's execution plan.

    Supported sources:
        - Jira
        - Notion
        - Gmail
        - RAG

    All retrieved information is converted into
    a common evidence format.
    """

    plan = state.get("plan", [])
    project_name = state.get("project_name", "")

    if not plan:
        return {
            **state,
            "error": "No execution plan was provided.",
        }

    if not project_name:
        return {
            **state,
            "error": "No project name was provided.",
        }

    jira_results: List[Dict[str, Any]] = []
    notion_results: List[Dict[str, Any]] = []
    gmail_results: List[Dict[str, Any]] = []
    rag_results: List[Dict[str, Any]] = []

    execution_errors: List[str] = []

    # -----------------------------------------------------
    # EXECUTE EACH PLAN STEP
    # -----------------------------------------------------

    for step in plan:

        if not isinstance(step, dict):
            continue

        question = step.get("question", "")
        sources = step.get("sources", [])

        if not question:
            continue

        if not isinstance(sources, list):
            continue

        # -------------------------------------------------
        # JIRA
        # -------------------------------------------------

        if "jira" in sources:

            try:

                issues = get_project_issues("KAN")

                for issue in issues:

                    if not isinstance(issue, dict):
                        continue

                    jira_results.append(
                        {
                            "source": "jira",
                            "question": question,
                            "issue_key": issue.get("key"),
                            "summary": issue.get("summary"),
                            "status": issue.get("status"),
                            "priority": issue.get("priority"),
                            "assignee": issue.get("assignee"),
                            "due_date": issue.get("due_date"),
                        }
                    )

            except Exception as exc:

                execution_errors.append(
                    f"Jira execution failed: {exc}"
                )

        # -------------------------------------------------
        # NOTION
        # -------------------------------------------------

        if "notion" in sources:

            try:

                results = search_notion(question)

                if isinstance(results, list):

                    for item in results:

                        if not isinstance(item, dict):
                            continue

                        notion_results.append(
                            {
                                "source": "notion",
                                "question": question,
                                **item,
                            }
                        )

            except Exception as exc:

                execution_errors.append(
                    f"Notion execution failed: {exc}"
                )

        # -------------------------------------------------
        # GMAIL
        # -------------------------------------------------

        if "gmail" in sources:

            try:

                results = search_project_emails(
                    project_name,
                    max_results=10,
                )

                if isinstance(results, list):

                    for item in results:

                        if not isinstance(item, dict):
                            continue

                        gmail_results.append(
                            {
                                "source": "gmail",
                                "question": question,
                                **item,
                            }
                        )

            except Exception as exc:

                execution_errors.append(
                    f"Gmail execution failed: {exc}"
                )

        # -------------------------------------------------
        # RAG
        # -------------------------------------------------

        if "rag" in sources:

            try:

                results = search_project_rag(
                    query=question,
                    project_name=project_name,
                    top_k=3,
                )

                if isinstance(results, list):

                    for item in results:

                        if not isinstance(item, dict):
                            continue

                        rag_results.append(
                            {
                                "source": "rag",
                                "question": question,
                                "project_name": project_name,
                                "id": item.get("id"),
                                "content": item.get("content", ""),
                                "distance": item.get("distance"),
                            }
                        )

            except Exception as exc:

                execution_errors.append(
                    f"RAG execution failed: {exc}"
                )

    # -----------------------------------------------------
    # BUILD COMMON EVIDENCE
    # -----------------------------------------------------

    evidence: List[Dict[str, Any]] = []

    evidence.extend(jira_results)
    evidence.extend(notion_results)
    evidence.extend(gmail_results)
    evidence.extend(rag_results)

    # -----------------------------------------------------
    # RETURN UPDATED STATE
    # -----------------------------------------------------

    return {
        **state,

        "jira_results": jira_results,
        "notion_results": notion_results,
        "gmail_results": gmail_results,
        "rag_results": rag_results,

        "evidence": evidence,

        "error": (
            "; ".join(execution_errors)
            if execution_errors
            else None
        ),
    }


# ---------------------------------------------------------
# DIRECT TEST
# ---------------------------------------------------------

def main():

    print("=" * 70)
    print("EXECUTOR TEST")
    print("=" * 70)

    state: AgentState = {
        "project_name": "Project X",

        "plan": [
            {
                "question": "What recent updates have been made?",
                "sources": ["gmail"],
                "reason": (
                    "Project updates may be communicated "
                    "through email."
                ),
            },
            {
                "question": "What are the current tasks?",
                "sources": ["jira"],
                "reason": (
                    "Tasks are tracked in Jira."
                ),
            },
            {
                "question": "What is documented about the project?",
                "sources": ["notion"],
                "reason": (
                    "Project documentation is stored in Notion."
                ),
            },
            {
                "question": (
                    "What are the risks and blockers "
                    "in Project X?"
                ),
                "sources": ["rag"],
                "reason": (
                    "Project documentation is stored "
                    "in the PDF knowledge base."
                ),
            },
        ],
    }

    print()
    print("Executing plan...")
    print()

    result = execute_plan(state)

    print("=" * 70)
    print("EXECUTION RESULT")
    print("=" * 70)

    print()
    print("JIRA RESULTS:")
    print(len(result.get("jira_results", [])))

    print()
    print("NOTION RESULTS:")
    print(len(result.get("notion_results", [])))

    print()
    print("GMAIL RESULTS:")
    print(len(result.get("gmail_results", [])))

    print()
    print("RAG RESULTS:")
    print(len(result.get("rag_results", [])))

    print()
    print("TOTAL EVIDENCE:")
    print(len(result.get("evidence", [])))

    print()
    print("ERROR:")
    print(result.get("error"))


if __name__ == "__main__":
    main()