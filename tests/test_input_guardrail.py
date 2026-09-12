from app.guardrails.input_guardrail import input_guardrail


def test_valid_project_query():
    result = input_guardrail(
        "What is happening with Project X?"
    )

    assert result["allowed"] is True


def test_valid_blocker_query():
    result = input_guardrail(
        "What are the current blockers?"
    )

    assert result["allowed"] is True


def test_valid_deadline_query():
    result = input_guardrail(
        "What deadlines changed this quarter?"
    )

    assert result["allowed"] is True


def test_empty_query():
    result = input_guardrail("")

    assert result["allowed"] is False