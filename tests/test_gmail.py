from app.tools.gmail import (
    get_gmail_service,
    search_gmail,
    search_project_emails,
)


def test_gmail_connection():
    service = get_gmail_service()

    assert service is not None


def test_gmail_search():
    results = search_gmail(
        "newer_than:30d",
        max_results=5,
    )

    assert isinstance(results, list)


def test_project_email_search():
    results = search_project_emails(
        "Project X",
        max_results=5,
    )

    assert isinstance(results, list)