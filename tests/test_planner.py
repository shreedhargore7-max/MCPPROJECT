from app.agent.planner import create_plan


def test_project_status_plan():

    sub_questions = [
        "What are the current project goals?",
        "What tasks are currently active?",
        "What updates have occurred recently?",
        "What are the upcoming deadlines?",
        "What blockers currently exist?",
    ]

    result = create_plan(
        "Project X",
        sub_questions,
    )

    assert "plan" in result
    assert "required_sources" in result

    assert isinstance(
        result["plan"],
        list,
    )

    assert len(result["plan"]) > 0

    for item in result["plan"]:

        assert "question" in item
        assert "sources" in item
        assert "reason" in item

        assert isinstance(
            item["sources"],
            list,
        )

        assert len(item["sources"]) > 0

        for source in item["sources"]:
            assert source in {
                "gmail",
                "notion",
                "jira",
                "rag",
            }


def test_blocker_plan():

    sub_questions = [
        "What blockers currently exist in Project X?"
    ]

    result = create_plan(
        "Project X",
        sub_questions,
    )

    assert len(result["plan"]) > 0

    sources = result["plan"][0]["sources"]

    assert len(sources) > 0