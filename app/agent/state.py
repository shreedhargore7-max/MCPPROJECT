from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict, total=False):
    """
    Shared state for the entire agentic workflow.
    """

    # ---------------------------------------------------------
    # USER INPUT
    # ---------------------------------------------------------

    user_query: str

    # ---------------------------------------------------------
    # QUERY UNDERSTANDING
    # ---------------------------------------------------------

    intent: str
    project_name: str
    sub_questions: List[str]

    # ---------------------------------------------------------
    # PLANNING
    # ---------------------------------------------------------

    plan: List[Dict[str, Any]]
    required_sources: List[str]

    # ---------------------------------------------------------
    # INFORMATION FROM DIFFERENT SOURCES
    # ---------------------------------------------------------

    project_goals: List[Dict[str, Any]]
    tasks: List[Dict[str, Any]]
    deadlines: List[Dict[str, Any]]
    blockers: List[Dict[str, Any]]

    # ---------------------------------------------------------
    # TOOL RESULTS
    # ---------------------------------------------------------

    gmail_results: List[Dict[str, Any]]
    notion_results: List[Dict[str, Any]]
    jira_results: List[Dict[str, Any]]
    rag_results: List[Dict[str, Any]]

    # ---------------------------------------------------------
    # EVIDENCE
    # ---------------------------------------------------------

    evidence: List[Dict[str, Any]]
    redacted_evidence: List[Dict[str, Any]]

    # ---------------------------------------------------------
    # ANSWER
    # ---------------------------------------------------------

    answer: str
    citations: List[Dict[str, Any]]

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    citation_validation_passed: bool
    output_validation_passed: bool
    validation_errors: List[str]

    # ---------------------------------------------------------
    # PERMISSIONS / ACTIONS
    # ---------------------------------------------------------

    requested_action: Optional[Dict[str, Any]]
    requires_approval: bool
    approved: bool
    action_result: Optional[Dict[str, Any]]

    # ---------------------------------------------------------
    # WORKFLOW CONTROL
    # ---------------------------------------------------------

    error: Optional[str]