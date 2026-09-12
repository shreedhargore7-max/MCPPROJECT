from app.agent.decomposer import decompose_query


def test_decompose_project_query():

    result = decompose_query(
        "What is happening with Project X?"
    )

    assert "intent" in result
    assert "project_name" in result
    assert "sub_questions" in result

    assert isinstance(result["sub_questions"], list)

    assert len(result["sub_questions"]) > 0


def test_decompose_blocker_query():

    result = decompose_query(
        "What are the current blockers in Project X?"
    )

    assert isinstance(result["sub_questions"], list)

    assert len(result["sub_questions"]) > 0


def test_decompose_deadline_query():

    result = decompose_query(
        "Which deadlines changed for Project X?"
    )

    assert isinstance(result["sub_questions"], list)

    assert len(result["sub_questions"]) > 0