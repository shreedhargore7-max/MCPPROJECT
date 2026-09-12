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
# ACTION APPROVAL ROUTER
# =========================================================

def action_router(
    state: AgentState,
) -> Literal["execute", "waiting"]:

    """
    Decide whether an action can be executed.

    If approval has not been given, stop safely.
    """

    if approval_required(state):
        return "waiting"

    if state.get("approved", False):
        return "execute"

    return "waiting"


# =========================================================
# EXECUTE ACTION NODE
# =========================================================

def action_execution_node(state: AgentState) -> AgentState:
    """
    Execute an approved external action.
    """

    return execute_action(state)


# =========================================================
# DECOMPOSER NODE
# =========================================================

def decomposer_node(state: AgentState) -> AgentState:
    """
    Break the user's query into smaller questions.
    """

    user_query = state.get("user_query", "")

    result = decompose_query(user_query)

    return {
        **state,
        "intent": result["intent"],
        "project_name": result["project_name"],
        "sub_questions": result["sub_questions"],
    }


# =========================================================
# PLANNER NODE
# =========================================================

def planner_node(state: AgentState) -> AgentState:
    """
    Create an execution plan.
    """

    project_name = state.get("project_name", "")
    sub_questions = state.get("sub_questions", [])

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
    Execute the plan against Jira, Notion, Gmail and RAG.
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

    evidence = state.get("evidence", [])

    redacted_evidence = redact_evidence(evidence)

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

    return answer_agent(safe_state)


# =========================================================
# CITATION VALIDATION NODE
# =========================================================

def citation_validation_node(state: AgentState) -> AgentState:
    """
    Check whether the generated answer is grounded
    in retrieved evidence.
    """

    answer = state.get("answer", "")

    evidence = state.get(
        "redacted_evidence",
        [],
    )

    result = validate_citations(
        answer=answer,
        evidence=evidence,
    )

    validation_errors = list(
        state.get("validation_errors", [])
    )

    validation_errors.extend(
        result.get("errors", [])
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

def output_validation_node(state: AgentState) -> AgentState:
    """
    Validate the final answer before returning it.
    """

    answer = state.get("answer", "")

    evidence = state.get(
        "redacted_evidence",
        [],
    )

    result = validate_output(
        answer=answer,
        evidence=evidence,
    )

    validation_errors = list(
        state.get("validation_errors", [])
    )

    validation_errors.extend(
        result.get("errors", [])
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

    graph = StateGraph(AgentState)

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

    graph.add_node(
        "action_execution",
        action_execution_node,
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
    # ACTION APPROVAL NODE
    # -----------------------------------------------------

    graph.add_node(
        "action_approval",
        lambda state: state,
    )

    # -----------------------------------------------------
    # ACTION APPROVAL -> EXECUTE / END
    # -----------------------------------------------------

    graph.add_conditional_edges(
        "action_approval",
        action_router,
        {
            "execute": "action_execution",
            "waiting": END,
        },
    )

    # -----------------------------------------------------
    # ACTION EXECUTION -> END
    # -----------------------------------------------------

    graph.add_edge(
        "action_execution",
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

def run_agent(user_query: str):
    """
    Run the MCPPROJECT agent for an external API request.

    This function is used by FastAPI and other callers
    that need to execute the complete LangGraph workflow.
    """

    if not user_query or not user_query.strip():
        raise ValueError(
            "User query cannot be empty."
        )

    app = build_graph()

    state: AgentState = {
        "user_query": user_query.strip(),
        "project_name": "",
        "validation_errors": [],
        "approved": False,
    }

    return app.invoke(state)


# =========================================================
# TEST WORKFLOW
# =========================================================

def main():

    app = build_graph()

    # =====================================================
    # TEST 1 — NORMAL INFORMATION QUERY
    # =====================================================

    query = "What are the risks and blockers in Project X?"

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
        "validation_errors": [],
        "approved": False,
    }

    result = app.invoke(initial_state)

    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    print()
    print("INTENT:")
    print(result.get("intent"))

    print()
    print("PROJECT:")
    print(result.get("project_name"))

    print()
    print("SUB-QUESTIONS:")

    for index, question in enumerate(
        result.get("sub_questions", []),
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
    # TEST 2 — ACTION QUERY
    # =====================================================

    print()
    print()
    print("=" * 70)
    print("TEST 2 — ACTION QUERY")
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

    action_result = app.invoke(action_state)

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