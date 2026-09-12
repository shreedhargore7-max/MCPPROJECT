from app.agent.answer_agent import (
    build_evidence_text,
    generate_answer,
    answer_agent,
)


def test_build_evidence_text():

    evidence = [
        {
            "source": "jira",
            "issue_key": "KAN-1",
            "summary": "Build login page",
            "status": "To Do",
            "priority": "Medium",
        }
    ]

    text = build_evidence_text(
        evidence
    )

    assert "jira" in text
    assert "KAN-1" in text
    assert "Build login page" in text
    assert "To Do" in text


def test_generate_answer():

    evidence = [
        {
            "source": "jira",
            "issue_key": "KAN-1",
            "summary": "Build login page",
            "status": "To Do",
            "priority": "Medium",
        },
        {
            "source": "jira",
            "issue_key": "KAN-2",
            "summary": "Fix database connection",
            "status": "To Do",
            "priority": "Medium",
        },
    ]

    answer = generate_answer(
        user_query="What tasks are currently in Project X?",
        evidence=evidence,
    )

    assert isinstance(answer, str)
    assert len(answer) > 0


def test_answer_agent():

    state = {
        "user_query": "What is happening with Project X?",
        "project_name": "Project X",
        "evidence": [
            {
                "source": "jira",
                "issue_key": "KAN-1",
                "summary": "Build login page",
                "status": "To Do",
                "priority": "Medium",
            },
            {
                "source": "jira",
                "issue_key": "KAN-2",
                "summary": "Fix database connection",
                "status": "To Do",
                "priority": "Medium",
            },
        ],
    }

    result = answer_agent(state)

    assert "answer" in result
    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 0
    assert result["error"] is None