import re
from typing import Dict, Any

from app.agent.state import AgentState
from app.tools.jira import (
    create_jira_issue,
    update_jira_issue,
    get_jira_issue_transitions,
    transition_jira_issue,
)
from app.tools.gmail import send_email


# =========================================================
# ACTION DETECTION
# =========================================================

def detect_action(state: AgentState) -> AgentState:
    """
    Detect whether the user's request requires an external action.

    This function only detects the action.
    It does not execute anything.

    External write operations require explicit approval.
    The approval value already present in the state is preserved.
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

            # IMPORTANT:
            # Preserve approval received from the API.
            "approved": state.get(
                "approved",
                False
            ),

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

            # IMPORTANT:
            # Preserve approval received from the API.
            "approved": state.get(
                "approved",
                False
            ),

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
        "change issue",
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
            "approved": state.get(
                "approved",
                False
            ),
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
    Parse a natural-language email request.

    Supported formats include:

    1.
    Send an email to test@example.com
    subject: Database Update
    message: The database connection issue is being worked on.

    2.
    Send an email to test@example.com
    with subject Database Update
    and message The database connection issue is being worked on.

    3.
    Send an email to test@example.com
    with subject: Database Update
    and message: The database connection issue is being worked on.
    """

    if not query:
        return {
            "to": "",
            "subject": "",
            "body": "",
        }

    # -----------------------------------------------------
    # Normalize whitespace
    # -----------------------------------------------------

    original = " ".join(
        query.strip().split()
    )

    query_lower = original.lower()

    # -----------------------------------------------------
    # Extract recipient
    # -----------------------------------------------------

    to = ""

    email_match = re.search(
        r"\bto\s+([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})",
        original,
        re.IGNORECASE,
    )

    if email_match:
        to = email_match.group(1).strip()

    # -----------------------------------------------------
    # Extract subject
    #
    # Supports:
    #
    # subject:
    # subject
    # with subject
    # with subject:
    # -----------------------------------------------------

    subject = ""

    subject_match = re.search(
        r"\bsubject\s*:?\s*(.*?)(?=\s+\band\s+message\b|\s+\bmessage\b|$)",
        original,
        re.IGNORECASE,
    )

    if subject_match:
        subject = subject_match.group(1).strip()

    # -----------------------------------------------------
    # Extract message/body
    #
    # Supports:
    #
    # message:
    # message
    # and message
    # and message:
    # -----------------------------------------------------

    body = ""

    message_match = re.search(
        r"\b(?:and\s+)?message\s*:?\s*(.*)$",
        original,
        re.IGNORECASE,
    )

    if message_match:
        body = message_match.group(1).strip()

    # -----------------------------------------------------
    # Fallback subject parser
    #
    # Handles cases where "and message" occurs but
    # subject extraction did not match as expected.
    # -----------------------------------------------------

    if not subject:
        subject_match = re.search(
            r"\bsubject\s*:?\s*(.*?)\s+\band\s+message\b",
            original,
            re.IGNORECASE,
        )

        if subject_match:
            subject = subject_match.group(1).strip()

    # -----------------------------------------------------
    # Clean accidental punctuation
    # -----------------------------------------------------

    subject = subject.strip(" \t\r\n:;-")

    body = body.strip()

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
                "error": str(exc),
            }

    # =====================================================
    # UPDATE JIRA ISSUE
    # =====================================================

    if action_type == "update_jira_issue":
        try:
            query = action.get("query", "").strip()

            # Find Jira issue key, e.g. KAN-10
            issue_match = re.search(
                r"\b[A-Z][A-Z0-9]+-\d+\b",
                query,
                re.IGNORECASE,
            )

            if not issue_match:
                message = "Could not determine the Jira issue key."
                return {
                    **state,
                    "action_result": {
                        "success": False,
                        "status": "invalid_request",
                        "action": action_type,
                        "message": message,
                    },
                    "error": message,
                }

            issue_key = issue_match.group(0).upper()

            # -------------------------------------------------
            # UPDATE SUMMARY
            # -------------------------------------------------

            summary_match = re.search(
                r"summary\s+to\s+(.+)$",
                query,
                re.IGNORECASE,
            )

            if summary_match:
                new_summary = summary_match.group(1).strip()

                if not new_summary:
                    message = "The new Jira summary cannot be empty."
                    return {
                        **state,
                        "action_result": {
                            "success": False,
                            "status": "invalid_request",
                            "action": action_type,
                            "message": message,
                        },
                        "error": message,
                    }

                result = update_jira_issue(
                    issue_key=issue_key,
                    fields={"summary": new_summary},
                )

                return {
                    **state,
                    "action_result": {
                        "success": True,
                        "status": "updated",
                        "action": action_type,
                        "issue_key": issue_key,
                        "updated_fields": {"summary": new_summary},
                        "result": result,
                    },
                    "error": None,
                }

            # -------------------------------------------------
            # UPDATE STATUS
            # -------------------------------------------------

            status_match = re.search(
                r"status\s+to\s+(.+)$",
                query,
                re.IGNORECASE,
            )

            if status_match:
                new_status = status_match.group(1).strip()

                if not new_status:
                    message = "The new Jira status cannot be empty."
                    return {
                        **state,
                        "action_result": {
                            "success": False,
                            "status": "invalid_request",
                            "action": action_type,
                            "message": message,
                        },
                        "error": message,
                    }

                transitions = get_jira_issue_transitions(issue_key)

                requested_transition = None
                for transition in transitions:
                    transition_to = transition.get("to", {})
                    transition_name = transition_to.get("name", "")

                    if transition_name.lower() == new_status.lower():
                        requested_transition = transition
                        break

                if not requested_transition:
                    available_statuses = []
                    for transition in transitions:
                        transition_to = transition.get("to", {})
                        transition_name = transition_to.get("name")
                        if transition_name:
                            available_statuses.append(transition_name)

                    message = (
                        f"Could not find a Jira transition to status '{new_status}'. "
                        f"Available statuses: {', '.join(available_statuses)}"
                    )
                    return {
                        **state,
                        "action_result": {
                            "success": False,
                            "status": "invalid_request",
                            "action": action_type,
                            "issue_key": issue_key,
                            "message": message,
                            "available_statuses": available_statuses,
                        },
                        "error": message,
                    }

                transition_id = requested_transition.get("id")
                if not transition_id:
                    message = "The Jira transition did not contain a valid transition ID."
                    return {
                        **state,
                        "action_result": {
                            "success": False,
                            "status": "error",
                            "action": action_type,
                            "issue_key": issue_key,
                            "message": message,
                        },
                        "error": message,
                    }

                result = transition_jira_issue(
                    issue_key=issue_key,
                    transition_id=transition_id,
                )

                return {
                    **state,
                    "action_result": {
                        "success": True,
                        "status": "updated",
                        "action": action_type,
                        "issue_key": issue_key,
                        "updated_fields": {"status": new_status},
                        "transition_id": transition_id,
                        "result": result,
                    },
                    "error": None,
                }

            # -------------------------------------------------
            # UNKNOWN UPDATE FIELD
            # -------------------------------------------------

            message = (
                "Could not determine the update details. "
                "Supported formats are: "
                "'Update Jira issue KAN-10 summary to New summary' "
                "or 'Update Jira issue KAN-10 status to Done'."
            )

            return {
                **state,
                "action_result": {
                    "success": False,
                    "status": "invalid_request",
                    "action": action_type,
                    "message": message,
                },
                "error": message,
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
                "error": str(exc),
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

            # -------------------------------------------------
            # Validate recipient
            # -------------------------------------------------

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
                    "error": (
                        "Could not determine the "
                        "recipient email address."
                    ),
                }

            # -------------------------------------------------
            # Validate subject
            # -------------------------------------------------

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
                    "error": (
                        "Could not determine the "
                        "email subject."
                    ),
                }

            # -------------------------------------------------
            # Validate body
            # -------------------------------------------------

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
                    "error": (
                        "Could not determine the "
                        "email message."
                    ),
                }

            # -------------------------------------------------
            # Send email
            # -------------------------------------------------

            result = send_email(
                to=email_data["to"],
                subject=email_data["subject"],
                body=email_data["body"],
            )

            return {
                **state,
                "action_result": result,
                "error": None,
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
                "error": str(exc),
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
        "error": (
            f"Unknown action type: {action_type}"
        ),
    }


# =========================================================
# LOCAL TESTS
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
        "approved": False,
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
    # TEST 2 — JIRA ACTION WITHOUT APPROVAL
    # =====================================================

    print()
    print("TEST 2 — JIRA ACTION WITHOUT APPROVAL")
    print("-" * 70)

    jira_state: AgentState = {
        "user_query": (
            "Create a Jira task for "
            "the database connection issue"
        ),
        "project_name": "Project X",
        "approved": False,
    }

    jira_action = detect_action(
        jira_state
    )

    print("REQUESTED ACTION:")
    print(
        jira_action.get(
            "requested_action"
        )
    )

    print("REQUIRES APPROVAL:")
    print(
        jira_action.get(
            "requires_approval"
        )
    )

    print("APPROVED:")
    print(
        jira_action.get(
            "approved"
        )
    )

    # Do NOT execute because approval is False.
    jira_blocked = execute_action(
        jira_action
    )

    print("ACTION RESULT:")
    print(
        jira_blocked.get(
            "action_result"
        )
    )

    # =====================================================
    # TEST 3 — GMAIL DETECTION
    # =====================================================

    print()
    print("TEST 3 — GMAIL DETECTION")
    print("-" * 70)

    gmail_state: AgentState = {
        "user_query": (
            "Send an email to "
            "shreedhargore7@gmail.com "
            "with subject Project X Update "
            "and message The database issue "
            "is being investigated."
        ),
        "project_name": "Project X",
        "approved": False,
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

    print("APPROVED:")
    print(
        gmail_action.get(
            "approved"
        )
    )

    # =====================================================
    # TEST 4 — GMAIL WITHOUT APPROVAL
    # =====================================================

    print()
    print("TEST 4 — GMAIL WITHOUT APPROVAL")
    print("-" * 70)

    gmail_no_approval = execute_action(
        gmail_action
    )

    print("ACTION RESULT:")
    print(
        gmail_no_approval.get(
            "action_result"
        )
    )

    # =====================================================
    # TEST 5 — EMAIL PARSER
    # =====================================================

    print()
    print("TEST 5 — EMAIL PARSER")
    print("-" * 70)

    email_query = (
        "Send an email to "
        "shreedhargore7@gmail.com "
        "with subject Project X Update "
        "and message The database issue "
        "is being investigated."
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
    # TEST 6 — APPROVED GMAIL ACTION
    # =====================================================

    print()
    print("TEST 6 — APPROVED GMAIL ACTION")
    print("-" * 70)

    gmail_approved_state: AgentState = {
        "user_query": (
            "Send an email to "
            "shreedhargore7@gmail.com "
            "with subject MCPPROJECT Gmail Test "
            "and message This is a test email "
            "from the MCPPROJECT Action Agent."
        ),
        "project_name": "Project X",
        "approved": True,
    }

    gmail_approved_action = detect_action(
        gmail_approved_state
    )

    print("REQUESTED ACTION:")
    print(
        gmail_approved_action.get(
            "requested_action"
        )
    )

    print("REQUIRES APPROVAL:")
    print(
        gmail_approved_action.get(
            "requires_approval"
        )
    )

    print("APPROVED:")
    print(
        gmail_approved_action.get(
            "approved"
        )
    )

    # -----------------------------------------------------
    # Execute only because approval is True.
    #
    # WARNING:
    # This sends a real email if Gmail credentials
    # are configured.
    # -----------------------------------------------------

    print()
    print("APPROVAL GRANTED")
    print(
        "Executing approved Gmail action..."
    )

    gmail_result = execute_action(
        gmail_approved_action
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
