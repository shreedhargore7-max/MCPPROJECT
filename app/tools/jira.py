import os
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv


load_dotenv()


# =========================================================
# JIRA CONFIGURATION
# =========================================================

JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")


# =========================================================
# CONFIG VALIDATION
# =========================================================

def validate_config() -> None:
    """Validate Jira configuration."""

    missing = []

    if not JIRA_URL:
        missing.append("JIRA_URL")

    if not JIRA_EMAIL:
        missing.append("JIRA_EMAIL")

    if not JIRA_API_TOKEN:
        missing.append("JIRA_API_TOKEN")

    if missing:
        raise RuntimeError(
            "Missing Jira configuration: "
            + ", ".join(missing)
        )


# =========================================================
# COMMON JIRA REQUEST
# =========================================================

def jira_request(
    method: str,
    endpoint: str,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Make an authenticated Jira API request.
    """

    validate_config()

    url = f"{JIRA_URL.rstrip('/')}{endpoint}"

    response = requests.request(
        method=method,
        url=url,
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=30,
        **kwargs,
    )

    if not response.ok:
        raise RuntimeError(
            f"Jira API error {response.status_code}: "
            f"{response.text}"
        )

    # Some Jira endpoints may return an empty response.
    if not response.text.strip():
        return {}

    return response.json()


# =========================================================
# GET PROJECT
# =========================================================

def get_project(
    project_key: str
) -> Dict[str, Any]:
    """Get Jira project information."""

    if not project_key:
        raise ValueError(
            "Project key cannot be empty."
        )

    return jira_request(
        "GET",
        f"/rest/api/3/project/{project_key}"
    )


# =========================================================
# GET PROJECT ISSUES
# =========================================================

def get_project_issues(
    project_key: str,
    max_results: int = 20
) -> List[Dict[str, Any]]:
    """
    Retrieve issues belonging to a Jira project.
    """

    if not project_key:
        raise ValueError(
            "Project key cannot be empty."
        )

    jql = (
        f"project = {project_key} "
        f"ORDER BY updated DESC"
    )

    response = jira_request(
        "GET",
        "/rest/api/3/search/jql",
        params={
            "jql": jql,
            "maxResults": max_results,
            "fields": (
                "summary,status,priority,"
                "assignee,duedate,updated,"
                "description"
            ),
        },
    )

    issues = []

    for issue in response.get("issues", []):

        fields = issue.get(
            "fields",
            {}
        )

        status = fields.get(
            "status"
        )

        priority = fields.get(
            "priority"
        )

        assignee = fields.get(
            "assignee"
        )

        issues.append(
            {
                "key": issue.get("key"),

                "summary": fields.get(
                    "summary"
                ),

                "status": (
                    status.get("name")
                    if status
                    else None
                ),

                "priority": (
                    priority.get("name")
                    if priority
                    else None
                ),

                "assignee": (
                    assignee.get("displayName")
                    if assignee
                    else None
                ),

                "due_date": fields.get(
                    "duedate"
                ),

                "updated": fields.get(
                    "updated"
                ),

                "description": fields.get(
                    "description"
                ),
            }
        )

    return issues


# =========================================================
# SEARCH ISSUES
# =========================================================

def search_issues(
    jql: str,
    max_results: int = 20
) -> List[Dict[str, Any]]:
    """Search Jira using JQL."""

    if not jql or not jql.strip():
        raise ValueError(
            "JQL query cannot be empty."
        )

    response = jira_request(
        "GET",
        "/rest/api/3/search/jql",
        params={
            "jql": jql,
            "maxResults": max_results,
        },
    )

    return response.get(
        "issues",
        []
    )


# =========================================================
# CREATE JIRA ISSUE
# =========================================================

def create_issue(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
) -> Dict[str, Any]:
    """
    Create a new Jira issue.

    This function performs a REAL Jira write operation.

    IMPORTANT:
    The caller (Action Agent) must ensure that the user
    has explicitly approved the action before calling this.
    """

    if not project_key:
        raise ValueError(
            "Project key cannot be empty."
        )

    if not summary or not summary.strip():
        raise ValueError(
            "Issue summary cannot be empty."
        )

    if not description or not description.strip():
        description = (
            "Issue created by MCPPROJECT agent."
        )

    payload = {
        "fields": {
            "project": {
                "key": project_key
            },

            "summary": summary.strip(),

            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description.strip()
                            }
                        ]
                    }
                ]
            },

            "issuetype": {
                "name": issue_type
            },
        }
    }

    return jira_request(
        "POST",
        "/rest/api/3/issue",
        json=payload,
    )


# =========================================================
# UPDATE JIRA ISSUE
# =========================================================

def update_issue(
    issue_key: str,
    fields: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update an existing Jira issue.

    Example:

        update_issue(
            "KAN-2",
            {
                "summary": "Updated database task"
            }
        )
    """

    if not issue_key:
        raise ValueError(
            "Issue key cannot be empty."
        )

    if not isinstance(fields, dict):
        raise ValueError(
            "Fields must be provided as a dictionary."
        )

    if not fields:
        raise ValueError(
            "At least one field must be provided."
        )

    payload = {
        "fields": fields
    }

    return jira_request(
        "PUT",
        f"/rest/api/3/issue/{issue_key}",
        json=payload,
    )


# =========================================================
# UPDATE ISSUE SUMMARY
# =========================================================

def update_issue_summary(
    issue_key: str,
    summary: str
) -> Dict[str, Any]:
    """Update the summary of an existing Jira issue."""

    if not summary or not summary.strip():
        raise ValueError(
            "Issue summary cannot be empty."
        )

    return update_issue(
        issue_key,
        {
            "summary": summary.strip()
        }
    )


# =========================================================
# UPDATE ISSUE DESCRIPTION
# =========================================================

def update_issue_description(
    issue_key: str,
    description: str
) -> Dict[str, Any]:
    """Update the description of an existing Jira issue."""

    if not description or not description.strip():
        raise ValueError(
            "Issue description cannot be empty."
        )

    description_document = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": description.strip()
                    }
                ]
            }
        ]
    }

    return update_issue(
        issue_key,
        {
            "description": description_document
        }
    )


# =========================================================
# ACTION AGENT COMPATIBILITY FUNCTIONS
# =========================================================

def create_jira_issue(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
) -> Dict[str, Any]:
    """
    Wrapper used by the Action Agent.

    Performs a real Jira issue creation.
    Approval must be handled by the Action Agent
    before this function is called.
    """

    return create_issue(
        project_key=project_key,
        summary=summary,
        description=description,
        issue_type=issue_type,
    )


def update_jira_issue(
    issue_key: str,
    fields: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Wrapper used by the Action Agent.

    Performs a real Jira issue update.
    Approval must be handled by the Action Agent
    before this function is called.
    """

    return update_issue(
        issue_key=issue_key,
        fields=fields,
    )

















# =========================================================
# DIRECT TEST
# =========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("JIRA TOOL TEST")
    print("=" * 60)

    project_key = "KAN"

    # -----------------------------------------------------
    # CONNECTION TEST
    # -----------------------------------------------------

    print()
    print(
        f"Connecting to Jira project: {project_key}"
    )

    project = get_project(
        project_key
    )

    print()
    print(
        "JIRA CONNECTION SUCCESSFUL"
    )

    print(
        f"Project name: {project.get('name')}"
    )

    print(
        f"Project key: {project.get('key')}"
    )

    # -----------------------------------------------------
    # ISSUE RETRIEVAL TEST
    # -----------------------------------------------------

    print()
    print(
        "Retrieving issues..."
    )

    issues = get_project_issues(
        project_key
    )

    print(
        f"Retrieved {len(issues)} issues."
    )

    for issue in issues:

        print()

        print(
            f"{issue['key']} - "
            f"{issue['summary']}"
        )

        print(
            f"Status: {issue['status']}"
        )

        print(
            f"Priority: {issue['priority']}"
        )

        print(
            f"Due date: {issue['due_date']}"
        )

    # -----------------------------------------------------
    # WRITE OPERATIONS ARE NOT EXECUTED HERE
    # -----------------------------------------------------

    print()
    print(
        "CREATE/UPDATE TEST:"
    )

    print(
        "Skipped intentionally."
    )

    print(
        "Real Jira write operations require "
        "explicit approval through the Action Agent."
    )

    print()
    print("=" * 60)
    print("JIRA TOOL TEST COMPLETE")
    print("=" * 60)