from typing import Literal

from langgraph.graph import StateGraph, START, END

from app.agent.state import AgentState
from app.guardrails.input_guardrail import input_guardrail
from app.guardrails.pii_redactor import redact_evidence
from app.guardrails.citation_validator import validate_citations
from app.guardrails.output_validator import validate_output

from app.agent.decomposer import decompose_query
from app.agent.planner import create_plan
from app.agent.executor import execute_plan
from app.agent.answer_agent import answer_agent

from app.agent.action_agent import (
    detect_action,
    approval_required,
    execute_action,
)


# =========================================================
# INPUT GUARDRAIL NODE
# =========================================================

def input_guardrail_node(state: AgentState) -> AgentState:
    """
    Validate the user's query before the workflow starts.
    """

    user_query = state.get("user_query", "")

    result = input_guardrail(user_query)

    if result["allowed"]:
        return {
            **state,
            "intent": "project_analysis",
            "error": None,
        }

    return {
        **state,
        "intent": "blocked",
        "error": result["reason"],
    }


# =========================================================
# ACTION DETECTION NODE
# =========================================================

def action_detection_node(state: AgentState) -> AgentState:
    """
    Detect whether the user requested an external action.

    This node does not execute anything.
    """

    return detect_action(state)


# =========================================================
# INITIAL ROUTER
# =========================================================

def initial_router(
    state: AgentState,
) -> Literal["action", "analysis", "blocked"]:
    """
    Decide whether the request is:

        action   -> external action requested
        analysis -> normal information request
        blocked  -> input guardrail rejected request
    """

    if state.get("error"):
        return "blocked"

    if state.get("requested_action"):
        return "action"

    return "analysis"


# =========================================================
# ACTION APPROVAL NODE
# =========================================================

def action_approval_node(state: AgentState) -> AgentState:
    """
    Prepare the state for the approval decision.

    No external action is executed here.
    """

    requires = approval_required(state)

    return {
        **state,
        "requires_approval": requires,
    }


# =========================================================
# ACTION ROUTER
# =========================================================

def action_router(
    state: AgentState,
) -> Literal["execute", "waiting"]:
    """
    Decide whether an external action can be executed.

    An action is executed only when:
        approved == True

    Otherwise the graph safely returns the pending
    action information to the caller.
    """

    if state.get("approved", False):
        return "execute"

    return "waiting"


# =========================================================
# WAITING ACTION NODE
# =========================================================

def waiting_action_node(state: AgentState) -> AgentState:
    """
    Return a clear response when an action needs approval.

    This prevents the UI from receiving an empty answer.
    """

    requested_action = state.get("requested_action") or {}

    action_type = requested_action.get(
        "type",
        "external_action",
    )

    return {
        **state,
        "answer": (
            f"Approval required before executing the action: "
            f"{action_type}."
        ),
        "action_result": None,
        "error": None,
    }


# =========================================================
# EXECUTE ACTION NODE
# =========================================================

def action_execution_node(state: AgentState) -> AgentState:
    """
    Execute an approved external action.
    """

    return execute_action(state)


# =========================================================
# ACTION RESULT NODE
# =========================================================

def action_result_node(state: AgentState) -> AgentState:
    """
    Convert the external action result into a final
    user-friendly answer.
    """

    action_result = state.get("action_result")

    if not action_result:
        return {
            **state,
            "answer": "The action could not be completed.",
        }

    if isinstance(action_result, dict):

        success = action_result.get("success")

        if success is False:

            error_message = (
                action_result.get("error")
                or action_result.get("message")
                or "The action failed."
            )

            return {
                **state,
                "answer": (
                    f"Action failed: {error_message}"
                ),
                "error": error_message,
            }

        message = (
            action_result.get("message")
            or action_result.get("result")
        )

        if message:
            return {
                **state,
                "answer": str(message),
                "error": None,
            }

    return {
        **state,
        "answer": (
            f"Action completed successfully: "
            f"{action_result}"
        ),
        "error": None,
    }


# =========================================================
# DECOMPOSER NODE
# =========================================================

def decomposer_node(state: AgentState) -> AgentState:
    """
    Break the user's query into smaller questions.

    If the decomposer identifies a project name, use it.

    If it does not identify one, preserve the project name
    supplied by the API.

    This allows queries such as:

        What are the project goals?

    to still operate against the default project.
    """

    user_query = state.get(
        "user_query",
        "",
    )

    existing_project_name = (
        state.get(
            "project_name",
            "",
        )
        or ""
    ).strip()

    result = decompose_query(
        user_query
    )

    detected_project_name = (
        result.get(
            "project_name",
            "",
        )
        or ""
    ).strip()

    project_name = (
        detected_project_name
        if detected_project_name
        else existing_project_name
    )

    if not project_name:
        project_name = "Project X"

    return {
        **state,
        "intent": result["intent"],
        "project_name": project_name,
        "sub_questions": result["sub_questions"],
    }


# =========================================================
# PLANNER NODE
# =========================================================

def planner_node(state: AgentState) -> AgentState:
    """
    Create an execution plan.
    """

    project_name = state.get(
        "project_name",
        "",
    )

    sub_questions = state.get(
        "sub_questions",
        [],
    )

    result = create_plan(
        project_name,
        sub_questions,
    )

    return {
        **state,
        "plan": result["plan"],
        "required_sources": result["required_sources"],
    }


# =========================================================
# EXECUTOR NODE
# =========================================================

def executor_node(state: AgentState) -> AgentState:
    """
    Execute the information-retrieval plan against
    Jira, Notion, Gmail and RAG.
    """

    return execute_plan(state)


# =========================================================
# PII REDACTION NODE
# =========================================================

def pii_redactor_node(state: AgentState) -> AgentState:
    """
    Remove PII and sensitive credentials from evidence
    before sending evidence to the Answer Agent.
    """

    evidence = state.get(
        "evidence",
        [],
    )

    redacted_evidence = redact_evidence(
        evidence
    )

    return {
        **state,
        "redacted_evidence": redacted_evidence,
    }


# =========================================================
# ANSWER AGENT NODE
# =========================================================

def answer_agent_node(state: AgentState) -> AgentState:
    """
    Generate the final answer using redacted evidence.
    """

    redacted_evidence = state.get(
        "redacted_evidence",
        [],
    )

    safe_state = {
        **state,
        "evidence": redacted_evidence,
    }

    return answer_agent(
        safe_state
    )


# =========================================================
# CITATION VALIDATION NODE
# =========================================================

def citation_validation_node(
    state: AgentState,
) -> AgentState:
    """
    Check whether the generated answer is grounded
    in retrieved evidence.
    """

    answer = state.get(
        "answer",
        "",
    )

    evidence = state.get(
        "redacted_evidence",
        [],
    )

    result = validate_citations(
        answer=answer,
        evidence=evidence,
    )

    validation_errors = list(
        state.get(
            "validation_errors",
            [],
        )
    )

    validation_errors.extend(
        result.get(
            "errors",
            [],
        )
    )

    return {
        **state,
        "citations": result.get(
            "citations",
            [],
        ),
        "citation_validation_passed": result.get(
            "passed",
            False,
        ),
        "validation_errors": validation_errors,
    }


# =========================================================
# OUTPUT VALIDATION NODE
# =========================================================

def output_validation_node(
    state: AgentState,
) -> AgentState:
    """
    Validate the final answer before returning it.
    """

    answer = state.get(
        "answer",
        "",
    )

    evidence = state.get(
        "redacted_evidence",
        [],
    )

    result = validate_output(
        answer=answer,
        evidence=evidence,
    )

    validation_errors = list(
        state.get(
            "validation_errors",
            [],
        )
    )

    validation_errors.extend(
        result.get(
            "errors",
            [],
        )
    )

    return {
        **state,
        "output_validation_passed": result.get(
            "passed",
            False,
        ),
        "validation_errors": validation_errors,
    }


# =========================================================
# BUILD GRAPH
# =========================================================

def build_graph():

    graph = StateGraph(
        AgentState
    )

    # -----------------------------------------------------
    # NODES
    # -----------------------------------------------------

    graph.add_node(
        "input_guardrail",
        input_guardrail_node,
    )

    graph.add_node(
        "action_detection",
        action_detection_node,
    )

    graph.add_node(
        "action_approval",
        action_approval_node,
    )

    graph.add_node(
        "waiting_action",
        waiting_action_node,
    )

    graph.add_node(
        "action_execution",
        action_execution_node,
    )

    graph.add_node(
        "action_result",
        action_result_node,
    )

    graph.add_node(
        "decomposer",
        decomposer_node,
    )

    graph.add_node(
        "planner",
        planner_node,
    )

    graph.add_node(
        "executor",
        executor_node,
    )

    graph.add_node(
        "pii_redactor",
        pii_redactor_node,
    )

    graph.add_node(
        "answer_agent",
        answer_agent_node,
    )

    graph.add_node(
        "citation_validator",
        citation_validation_node,
    )

    graph.add_node(
        "output_validator",
        output_validation_node,
    )

    # -----------------------------------------------------
    # START -> INPUT GUARDRAIL
    # -----------------------------------------------------

    graph.add_edge(
        START,
        "input_guardrail",
    )

    # -----------------------------------------------------
    # INPUT GUARDRAIL -> ACTION DETECTION / END
    # -----------------------------------------------------

    graph.add_conditional_edges(
        "input_guardrail",
        lambda state: (
            "blocked"
            if state.get("error")
            else "continue"
        ),
        {
            "continue": "action_detection",
            "blocked": END,
        },
    )

    # -----------------------------------------------------
    # ACTION DETECTION -> ACTION / ANALYSIS / BLOCKED
    # -----------------------------------------------------

    graph.add_conditional_edges(
        "action_detection",
        initial_router,
        {
            "action": "action_approval",
            "analysis": "decomposer",
            "blocked": END,
        },
    )

    # -----------------------------------------------------
    # ACTION APPROVAL -> EXECUTE / WAITING
    # -----------------------------------------------------

    graph.add_conditional_edges(
        "action_approval",
        action_router,
        {
            "execute": "action_execution",
            "waiting": "waiting_action",
        },
    )

    # -----------------------------------------------------
    # WAITING -> END
    # -----------------------------------------------------

    graph.add_edge(
        "waiting_action",
        END,
    )

    # -----------------------------------------------------
    # ACTION EXECUTION -> ACTION RESULT
    # -----------------------------------------------------

    graph.add_edge(
        "action_execution",
        "action_result",
    )

    # -----------------------------------------------------
    # ACTION RESULT -> END
    # -----------------------------------------------------

    graph.add_edge(
        "action_result",
        END,
    )

    # -----------------------------------------------------
    # NORMAL ANALYSIS WORKFLOW
    # -----------------------------------------------------

    graph.add_edge(
        "decomposer",
        "planner",
    )

    graph.add_edge(
        "planner",
        "executor",
    )

    graph.add_edge(
        "executor",
        "pii_redactor",
    )

    graph.add_edge(
        "pii_redactor",
        "answer_agent",
    )

    graph.add_edge(
        "answer_agent",
        "citation_validator",
    )

    graph.add_edge(
        "citation_validator",
        "output_validator",
    )

    graph.add_edge(
        "output_validator",
        END,
    )

    return graph.compile()


# =========================================================
# API / EXTERNAL ENTRY FUNCTION
# =========================================================

def run_agent(
    user_query: str,
    project_name: str = "Project X",
    approved: bool = False,
):
    """
    Run the MCPPROJECT agent.

    Parameters
    ----------
    user_query:
        User's natural-language request.

    project_name:
        Project name supplied by the API/frontend.

        If the user query contains a more specific project
        name, decomposer_node may replace this value.

    approved:
        Whether the user explicitly approved an external
        Jira/Gmail action.

        False:
            Action is detected and returned as pending.

        True:
            Approved external action may be executed.
    """

    if not user_query or not user_query.strip():
        raise ValueError(
            "User query cannot be empty."
        )

    app = build_graph()

    project_name = (
        project_name.strip()
        if project_name and project_name.strip()
        else "Project X"
    )

    state: AgentState = {
        "user_query": user_query.strip(),
        "project_name": project_name,
        "validation_errors": [],
        "approved": approved,
        "requires_approval": False,
        "action_result": None,
        "error": None,
    }

    return app.invoke(
        state
    )


# =========================================================
# TEST WORKFLOW
# =========================================================

def main():

    app = build_graph()

    # =====================================================
    # TEST 1 — NORMAL INFORMATION QUERY
    # =====================================================

    query = (
        "What are the risks and blockers in Project X?"
    )

    print("=" * 70)
    print("TEST 1 — INFORMATION QUERY")
    print("=" * 70)

    print()
    print("USER QUERY:")
    print(query)

    print()
    print("Running agent...")
    print()

    initial_state: AgentState = {
        "user_query": query,
        "project_name": "Project X",
        "validation_errors": [],
        "approved": False,
    }

    result = app.invoke(
        initial_state
    )

    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    print()
    print("INTENT:")
    print(
        result.get(
            "intent"
        )
    )

    print()
    print("PROJECT:")
    print(
        result.get(
            "project_name"
        )
    )

    print()
    print("SUB-QUESTIONS:")

    for index, question in enumerate(
        result.get(
            "sub_questions",
            []
        ),
        start=1,
    ):
        print(
            f"{index}. {question}"
        )

    print()
    print("REQUIRED SOURCES:")
    print(
        result.get(
            "required_sources",
            [],
        )
    )

    print()
    print("RAW EVIDENCE COUNT:")
    print(
        len(
            result.get(
                "evidence",
                [],
            )
        )
    )

    print()
    print("REDACTED EVIDENCE COUNT:")
    print(
        len(
            result.get(
                "redacted_evidence",
                [],
            )
        )
    )

    print()
    print("CITATION VALIDATION:")
    print(
        result.get(
            "citation_validation_passed",
            False,
        )
    )

    print()
    print("OUTPUT VALIDATION:")
    print(
        result.get(
            "output_validation_passed",
            False,
        )
    )

    print()
    print("FINAL ANSWER:")
    print("-" * 70)
    print(
        result.get(
            "answer",
            "",
        )
    )

    print()
    print("ERROR:")
    print(
        result.get(
            "error"
        )
    )

    # =====================================================
    # TEST 2 — JIRA ACTION WITHOUT APPROVAL
    # =====================================================

    print()
    print()
    print("=" * 70)
    print("TEST 2 — JIRA ACTION / NO APPROVAL")
    print("=" * 70)

    action_query = (
        "Create a Jira task for the database connection issue"
    )

    print()
    print("USER QUERY:")
    print(action_query)

    action_state: AgentState = {
        "user_query": action_query,
        "project_name": "Project X",
        "validation_errors": [],
        "approved": False,
    }

    action_result = app.invoke(
        action_state
    )

    print()
    print("REQUESTED ACTION:")
    print(
        action_result.get(
            "requested_action"
        )
    )

    print()
    print("REQUIRES APPROVAL:")
    print(
        action_result.get(
            "requires_approval",
            False,
        )
    )

    print()
    print("FINAL ANSWER:")
    print(
        action_result.get(
            "answer",
            "",
        )
    )

    print()
    print("ACTION RESULT:")
    print(
        action_result.get(
            "action_result"
        )
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()