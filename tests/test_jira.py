from app.tools.jira import (
    get_project,
    get_project_issues,
)


def test_jira_connection():
    project = get_project("KAN")

    assert project is not None
    assert project.get("key") == "KAN"


def test_jira_project_issues():
    issues = get_project_issues("KAN")

    assert isinstance(issues, list)

    for issue in issues:
        assert "key" in issue
        assert "summary" in issue
        assert "status" in issue