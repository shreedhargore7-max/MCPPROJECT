from typing import Dict, Any

from app.agent.state import AgentState
from app.tools.jira import create_jira_issue, update_jira_issue
from app.tools.gmail import send_email


# =========================================================
# ACTION DETECTION
# =========================================================

def detect_action(state: AgentState) -> AgentState:
    """
    Detect whether the user's request requires an external action.

    This function only detects the action.
    It does not execute anything.

    All external write operations require approval.
    """

    user_query = state.get(
        "user_query",
        ""
    ).strip()

    if not user_query:
        return {
            **state,
            "requested_action": None,
            "requires_approval": False,
            "approved": False,
            "action_result": None,
        }

    query = user_query.lower()

    # =====================================================
    # CREATE JIRA ISSUE
    # =====================================================

    jira_create_keywords = [
        "create jira",
        "create a jira",
        "add jira",
        "create issue",
        "create a task",
        "add a task",
        "make a jira task",
    ]

    if any(
        keyword in query
        for keyword in jira_create_keywords
    ):

        action = {
            "type": "create_jira_issue",
            "description": (
                "Create a Jira issue based on "
                "the user's request."
            ),
            "project": state.get(
                "project_name",
                ""
            ),
            "query": user_query,
        }

        return {
            **state,
            "requested_action": action,
            "requires_approval": True,
            "approved": False,
            "action_result": None,
        }

    # =====================================================
    # SEND EMAIL
    # =====================================================

    email_keywords = [
        "send email",
        "send an email",
        "email the team",
        "send mail",
        "send a mail",
    ]

    if any(
        keyword in query
        for keyword in email_keywords
    ):

        action = {
            "type": "send_email",
            "description": (
                "Send an email based on "
                "the user's request."
            ),
            "project": state.get(
                "project_name",
                ""
            ),
            "query": user_query,
        }

        return {
            **state,
            "requested_action": action,
            "requires_approval": True,
            "approved": False,
            "action_result": None,
        }

    # =====================================================
    # UPDATE JIRA ISSUE
    # =====================================================

    jira_update_keywords = [
        "update jira",
        "update the jira",
        "change jira",
        "update issue",
        "change issue status",
        "move jira",
    ]

    if any(
        keyword in query
        for keyword in jira_update_keywords
    ):

        action = {
            "type": "update_jira_issue",
            "description": (
                "Update an existing Jira issue."
            ),
            "project": state.get(
                "project_name",
                ""
            ),
            "query": user_query,
        }

        return {
            **state,
            "requested_action": action,
            "requires_approval": True,
            "approved": False,
            "action_result": None,
        }

    # =====================================================
    # NO ACTION
    # =====================================================

    return {
        **state,
        "requested_action": None,
        "requires_approval": False,
        "approved": False,
        "action_result": None,
    }


# =========================================================
# APPROVAL CHECK
# =========================================================

def approval_required(
    state: AgentState
) -> bool:
    """
    Return True when an action exists
    and still requires approval.
    """

    return bool(
        state.get("requested_action")
        and state.get(
            "requires_approval",
            False
        )
        and not state.get(
            "approved",
            False
        )
    )


# =========================================================
# EMAIL PARSER
# =========================================================

def _parse_email_request(
    query: str
) -> Dict[str, str]:
    """
    Parse a simple email request.

    Expected format:

    Send an email to test@example.com
    subject: Database Update
    message: The database connection issue is being worked on.
    """

    query_lower = query.lower()

    # -----------------------------------------------------
    # Extract recipient
    # -----------------------------------------------------

    to = ""

    if " to " in query_lower:

        start = query_lower.find(" to ") + 4

        remaining = query[start:]

        stop_positions = []

        for marker in [
            " subject:",
            " subject ",
            " message:",
            " message ",
        ]:

            position = remaining.lower().find(
                marker
            )

            if position != -1:
                stop_positions.append(
                    position
                )

        if stop_positions:

            end = min(stop_positions)

            to = remaining[:end].strip()

        else:

            to = remaining.strip()

    # -----------------------------------------------------
    # Extract subject
    # -----------------------------------------------------

    subject = ""

    subject_position = query_lower.find(
        "subject:"
    )

    if subject_position != -1:

        start = subject_position + len(
            "subject:"
        )

        remaining = query[start:]

        message_position = remaining.lower().find(
            "message:"
        )

        if message_position != -1:

            subject = remaining[
                :message_position
            ].strip()

        else:

            subject = remaining.strip()

    # -----------------------------------------------------
    # Extract message
    # -----------------------------------------------------

    body = ""

    message_position = query_lower.find(
        "message:"
    )

    if message_position != -1:

        start = message_position + len(
            "message:"
        )

        body = query[start:].strip()

    return {
        "to": to,
        "subject": subject,
        "body": body,
    }


# =========================================================
# ACTION EXECUTION
# =========================================================

def execute_action(
    state: AgentState
) -> AgentState:
    """
    Execute an approved action.

    IMPORTANT:
    No external write operation can happen
    without explicit approval.
    """

    action = state.get(
        "requested_action"
    )

    # -----------------------------------------------------
    # No action
    # -----------------------------------------------------

    if not action:

        return {
            **state,
            "action_result": None,
        }

    # -----------------------------------------------------
    # Approval protection
    # -----------------------------------------------------

    if not state.get(
        "approved",
        False
    ):

        return {
            **state,
            "action_result": {
                "success": False,
                "status": "approval_required",
                "message": (
                    "The requested action requires "
                    "explicit user approval before execution."
                ),
            },
        }

    action_type = action.get(
        "type"
    )

    # =====================================================
    # CREATE JIRA ISSUE
    # =====================================================

    if action_type == "create_jira_issue":

        try:

            result = create_jira_issue(
                project_key="KAN",
                summary="Fix database connection",
                description=(
                    "Created by the approved "
                    "Action Agent request.\n\n"
                    f"Original request: "
                    f"{action.get('query', '')}"
                ),
            )

            return {
                **state,
                "action_result": result,
            }

        except Exception as exc:

            return {
                **state,
                "action_result": {
                    "success": False,
                    "status": "error",
                    "action": action_type,
                    "message": str(exc),
                },
            }

    # =====================================================
    # UPDATE JIRA ISSUE
    # =====================================================

    if action_type == "update_jira_issue":

        return {
            **state,
            "action_result": {
                "success": False,
                "status": "not_implemented",
                "action": action_type,
                "message": (
                    "Jira issue update requires "
                    "an issue key and update details. "
                    "The update workflow will be connected next."
                ),
            },
        }

    # =====================================================
    # SEND EMAIL
    # =====================================================

    if action_type == "send_email":

        try:

            email_data = _parse_email_request(
                action.get(
                    "query",
                    ""
                )
            )

            if not email_data["to"]:

                return {
                    **state,
                    "action_result": {
                        "success": False,
                        "status": "invalid_request",
                        "action": action_type,
                        "message": (
                            "Could not determine the "
                            "recipient email address."
                        ),
                    },
                }

            if not email_data["subject"]:

                return {
                    **state,
                    "action_result": {
                        "success": False,
                        "status": "invalid_request",
                        "action": action_type,
                        "message": (
                            "Could not determine the "
                            "email subject."
                        ),
                    },
                }

            if not email_data["body"]:

                return {
                    **state,
                    "action_result": {
                        "success": False,
                        "status": "invalid_request",
                        "action": action_type,
                        "message": (
                            "Could not determine the "
                            "email message."
                        ),
                    },
                }

            result = send_email(
                to=email_data["to"],
                subject=email_data["subject"],
                body=email_data["body"],
            )

            return {
                **state,
                "action_result": result,
            }

        except Exception as exc:

            return {
                **state,
                "action_result": {
                    "success": False,
                    "status": "error",
                    "action": action_type,
                    "message": str(exc),
                },
            }

    # =====================================================
    # UNKNOWN ACTION
    # =====================================================

    return {
        **state,
        "action_result": {
            "success": False,
            "status": "unknown_action",
            "message": (
                f"Unknown action type: {action_type}"
            ),
        },
    }


# =========================================================
# DIRECT TEST
# =========================================================

def main():

    print("=" * 70)
    print("ACTION AGENT TEST")
    print("=" * 70)

    # =====================================================
    # TEST 1 — NORMAL QUERY
    # =====================================================

    print()
    print("TEST 1 — NORMAL QUERY")
    print("-" * 70)

    state: AgentState = {
        "user_query": (
            "What are the risks and blockers "
            "in Project X?"
        ),
        "project_name": "Project X",
    }

    result = detect_action(
        state
    )

    print("REQUESTED ACTION:")
    print(
        result.get(
            "requested_action"
        )
    )

    print("REQUIRES APPROVAL:")
    print(
        result.get(
            "requires_approval"
        )
    )

    # =====================================================
    # TEST 2 — JIRA ACTION
    # =====================================================

    print()
    print("TEST 2 — JIRA ACTION")
    print("-" * 70)

    state = {
        "user_query": (
            "Create a Jira task for "
            "the database connection issue"
        ),
        "project_name": "Project X",
    }

    result = detect_action(
        state
    )

    print("REQUESTED ACTION:")
    print(
        result.get(
            "requested_action"
        )
    )

    print("REQUIRES APPROVAL:")
    print(
        result.get(
            "requires_approval"
        )
    )

    # =====================================================
    # TEST 3 — JIRA WITHOUT APPROVAL
    # =====================================================

    print()
    print("TEST 3 — JIRA WITHOUT APPROVAL")
    print("-" * 70)

    result = execute_action(
        result
    )

    print("ACTION RESULT:")
    print(
        result.get(
            "action_result"
        )
    )

    # =====================================================
    # TEST 4 — GMAIL ACTION
    # =====================================================

    print()
    print("TEST 4 — GMAIL ACTION")
    print("-" * 70)

    state = {
        "user_query": (
            "Send an email to test@example.com "
            "subject: Database Update "
            "message: The database connection issue "
            "is being worked on."
        ),
        "project_name": "Project X",
    }

    result = detect_action(
        state
    )

    print("REQUESTED ACTION:")
    print(
        result.get(
            "requested_action"
        )
    )

    print("REQUIRES APPROVAL:")
    print(
        result.get(
            "requires_approval"
        )
    )

    # =====================================================
    # TEST 5 — GMAIL WITHOUT APPROVAL
    # =====================================================

    print()
    print("TEST 5 — GMAIL WITHOUT APPROVAL")
    print("-" * 70)

    result = execute_action(
        result
    )

    print("ACTION RESULT:")
    print(
        result.get(
            "action_result"
        )
    )

    # =====================================================
    # TEST 6 — EMAIL PARSER
    # =====================================================

    print()
    print("TEST 6 — EMAIL PARSER")
    print("-" * 70)

    email_query = (
        "Send an email to test@example.com "
        "subject: Database Update "
        "message: The database connection issue "
        "is being worked on."
    )

    parsed = _parse_email_request(
        email_query
    )

    print("TO:")
    print(
        parsed["to"]
    )

    print("SUBJECT:")
    print(
        parsed["subject"]
    )

    print("MESSAGE:")
    print(
        parsed["body"]
    )

    # =====================================================
    # TEST 7 — APPROVED GMAIL ACTION
    # =====================================================

    print()
    print("TEST 7 — APPROVED GMAIL ACTION")
    print("-" * 70)

    gmail_state: AgentState = {
        "user_query": (
            "Send an email to shreedhargore7@gmail.com "
            "subject: MCPPROJECT Gmail Test "
            "message: This is a test email from the "
            "MCPPROJECT Action Agent."
        ),
        "project_name": "Project X",
    }

    gmail_action = detect_action(
        gmail_state
    )

    print("REQUESTED ACTION:")
    print(
        gmail_action.get(
            "requested_action"
        )
    )

    print("REQUIRES APPROVAL:")
    print(
        gmail_action.get(
            "requires_approval"
        )
    )

    # -----------------------------------------------------
    # EXPLICIT APPROVAL
    # -----------------------------------------------------

    gmail_action["approved"] = True

    print()
    print("APPROVAL GRANTED")
    print(
        "Sending test email to your own Gmail account..."
    )

    gmail_result = execute_action(
        gmail_action
    )

    print("ACTION RESULT:")
    print(
        gmail_result.get(
            "action_result"
        )
    )

    print()
    print("=" * 70)
    print("ACTION AGENT TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()