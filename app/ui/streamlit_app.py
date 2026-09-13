import sys
from pathlib import Path

import requests
import streamlit as st


# =========================================================
# PROJECT ROOT
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =========================================================
# CONFIGURATION
# =========================================================

API_URL = "http://127.0.0.1:8000"


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="MCPPROJECT AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>
        .main-title {
            font-size: 42px;
            font-weight: 700;
            margin-bottom: 0;
        }

        .subtitle {
            font-size: 17px;
            color: #777;
            margin-bottom: 25px;
        }

        .stChatMessage {
            border-radius: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🤖 MCPPROJECT AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Project Intelligence Agent • "
    "RAG + LangGraph + Jira + Gmail + Notion"
    "</div>",
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.header("MCPPROJECT")

    st.write(
        "Ask questions about your project and "
        "let the agent retrieve information from "
        "your connected sources."
    )

    st.divider()

    st.subheader("Connected Sources")

    st.write("📄 RAG")
    st.write("📋 Jira")
    st.write("📧 Gmail")
    st.write("📝 Notion")

    st.divider()

    st.subheader("Agent")

    st.write("🧠 LangGraph")
    st.write("🛡️ Guardrails")
    st.write("🔐 Approval System")

    st.divider()

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()


# =========================================================
# DISPLAY AGENT DETAILS
# =========================================================

def display_details(details):
    if not details:
        return

    with st.expander("🔍 Agent Details"):
        intent = details.get("intent")

        if intent:
            st.write(f"**Intent:** `{intent}`")

        project_name = details.get("project_name")

        if project_name:
            st.write(f"**Project:** `{project_name}`")

        sources = details.get("required_sources")

        if sources:
            st.write("**Required Sources:**")

            for source in sources:
                st.write(f"- {str(source).upper()}")

        questions = details.get("sub_questions")

        if questions:
            st.write("**Sub-questions:**")

            for question in questions:
                st.write(f"- {question}")

        raw_evidence = details.get("raw_evidence")

        if raw_evidence is not None:
            st.write(
                f"**Raw Evidence:** {len(raw_evidence)}"
            )

        redacted_evidence = details.get(
            "redacted_evidence"
        )

        if redacted_evidence is not None:
            st.write(
                f"**Redacted Evidence:** "
                f"{len(redacted_evidence)}"
            )

        citation_valid = details.get(
            "citation_valid"
        )

        if citation_valid is True:
            st.success(
                "Citation validation: Passed"
            )

        elif citation_valid is False:
            st.error(
                "Citation validation: Failed"
            )

        output_valid = details.get(
            "output_valid"
        )

        if output_valid is True:
            st.success(
                "Output validation: Passed"
            )

        elif output_valid is False:
            st.error(
                "Output validation: Failed"
            )


# =========================================================
# DISPLAY PREVIOUS CHAT
# =========================================================

for message in st.session_state.messages:

    role = message.get("role", "assistant")
    content = message.get("content", "")

    with st.chat_message(role):
        st.markdown(content)

        if role == "assistant":
            display_details(
                message.get("details")
            )


# =========================================================
# CALL FASTAPI
# =========================================================

def call_agent(
    user_query,
    approved=False,
):
    response = requests.post(
        f"{API_URL}/run",
        json={
            "user_query": user_query,
            "approved": approved,
        },
        timeout=300,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# CHAT INPUT
# =========================================================

user_query = st.chat_input(
    "Ask MCPPROJECT AI..."
)


# =========================================================
# PROCESS USER QUERY
# =========================================================

if user_query:

    # -----------------------------------------------------
    # SAVE USER MESSAGE
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_query,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_query)

    # -----------------------------------------------------
    # RUN AGENT
    # -----------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "MCPPROJECT AI is thinking..."
        ):

            try:

                result = call_agent(
                    user_query=user_query,
                    approved=False,
                )

                # -------------------------------------------------
                # RESULT
                # -------------------------------------------------

                if isinstance(result, dict):

                    answer = (
                        result.get("final_answer")
                        or result.get("answer")
                        or result.get("message")
                    )

                    if not answer:
                        answer = (
                            "The agent did not return "
                            "a final answer."
                        )

                    details = {
                        "intent": result.get(
                            "intent"
                        ),
                        "project_name": result.get(
                            "project_name"
                        ),
                        "required_sources": result.get(
                            "required_sources"
                        ),
                        "sub_questions": result.get(
                            "sub_questions"
                        ),
                        "raw_evidence": result.get(
                            "raw_evidence"
                        ),
                        "redacted_evidence": result.get(
                            "redacted_evidence"
                        ),
                        "citation_valid": result.get(
                            "citation_valid",
                            result.get(
                                "citation_validation_passed"
                            ),
                        ),
                        "output_valid": result.get(
                            "output_valid",
                            result.get(
                                "output_validation_passed"
                            ),
                        ),
                    }

                    requires_approval = result.get(
                        "requires_approval",
                        False,
                    )

                    action = result.get(
                        "requested_action"
                    )

                else:

                    answer = str(result)
                    details = {}
                    requires_approval = False
                    action = None

                # -------------------------------------------------
                # SHOW ANSWER
                # -------------------------------------------------

                st.markdown(answer)

                # -------------------------------------------------
                # SAVE ASSISTANT MESSAGE
                # -------------------------------------------------

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "details": details,
                    }
                )

                # -------------------------------------------------
                # AGENT DETAILS
                # -------------------------------------------------

                display_details(details)

                # -------------------------------------------------
                # APPROVAL
                # -------------------------------------------------

                if requires_approval:

                    st.warning(
                        "This action requires your approval "
                        "before it can be executed."
                    )

                    if action:
                        action_type = action.get(
                            "type",
                            "external action",
                        )
                    else:
                        action_type = (
                            "external action"
                        )

                    st.write(
                        f"**Requested action:** "
                        f"`{action_type}`"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        approve = st.button(
                            "✅ Approve",
                            key=(
                                "approve_"
                                + str(
                                    len(
                                        st.session_state.messages
                                    )
                                )
                            ),
                            use_container_width=True,
                        )

                    with col2:

                        reject = st.button(
                            "❌ Reject",
                            key=(
                                "reject_"
                                + str(
                                    len(
                                        st.session_state.messages
                                    )
                                )
                            ),
                            use_container_width=True,
                        )

                    if approve:

                        st.info(
                            "Sending approval to the agent..."
                        )

                        try:

                            approved_result = call_agent(
                                user_query=user_query,
                                approved=True,
                            )

                            approved_answer = (
                                approved_result.get(
                                    "final_answer"
                                )
                                or approved_result.get(
                                    "answer"
                                )
                                or approved_result.get(
                                    "message"
                                )
                                or "Action completed."
                            )

                            st.success(
                                approved_answer
                            )

                            st.session_state.messages.append(
                                {
                                    "role": "assistant",
                                    "content": approved_answer,
                                    "details": {},
                                }
                            )

                            st.rerun()

                        except Exception as exc:

                            st.error(
                                "Approval execution failed: "
                                f"{exc}"
                            )

                    if reject:

                        rejection_message = (
                            "Action rejected. "
                            "No external action was executed."
                        )

                        st.info(
                            rejection_message
                        )

                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": rejection_message,
                                "details": {},
                            }
                        )

                        st.rerun()

            except requests.exceptions.ConnectionError:

                error_message = (
                    "Unable to connect to the MCPPROJECT API. "
                    "Make sure FastAPI is running on "
                    "http://127.0.0.1:8000"
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                        "details": {},
                    }
                )

            except requests.exceptions.Timeout:

                error_message = (
                    "The agent took too long to respond. "
                    "Please try again."
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                        "details": {},
                    }
                )

            except requests.exceptions.HTTPError as exc:

                error_message = (
                    "API request failed: "
                    f"{exc}"
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                        "details": {},
                    }
                )

            except Exception as exc:

                error_message = (
                    "Agent error: "
                    f"{exc}"
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                        "details": {},
                    }
                )