from app.agent.executor import execute_plan


def test_executor_with_jira():

    state = {
        "user_query": "What is happening with Project X?",
        "intent": "project_status",
        "project_name": "Project X",

        "sub_questions": [
            "What tasks are currently active?"
        ],

        "plan": [
            {
                "question": "What tasks are currently active?",
                "sources": ["jira"],
                "reason": "Jira contains project tasks and statuses.",
            }
        ],

        "required_sources": ["jira"],
    }

    result = execute_plan(state)

    assert "jira_results" in result
    assert isinstance(result["jira_results"], list)

    assert len(result["jira_results"]) > 0


def test_executor_returns_evidence():

    state = {
        "user_query": "What are the current blockers?",
        "intent": "blocker_analysis",
        "project_name": "Project X",

        "sub_questions": [
            "What blockers currently exist?"
        ],

        "plan": [
            {
                "question": "What blockers currently exist?",
                "sources": ["jira"],
                "reason": "Jira tracks project issues.",
            }
        ],

        "required_sources": ["jira"],
    }

    result = execute_plan(state)

    assert "evidence" in result
    assert isinstance(result["evidence"], list)
    assert len(result["evidence"]) > 0