import os
import sys

# =========================================================
# PROJECT ROOT
# =========================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# =========================================================
# IMPORTS
# =========================================================

import streamlit as st

from app.agent.graph import run_agent


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="MCPPROJECT AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>
        .main-title {
            font-size: 42px;
            font-weight: 700;
            margin-bottom: 5px;
        }

        .subtitle {
            font-size: 18px;
            color: #666666;
            margin-bottom: 30px;
        }

        .result-box {
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #dddddd;
            margin-top: 15px;
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
    "Project Intelligence Agent powered by "
    "RAG, Jira, Gmail and Notion"
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
        "the agent will retrieve information from "
        "your connected sources."
    )

    st.divider()

    st.subheader("Connected Sources")

    st.write("📧 Gmail")
    st.write("📋 Jira")
    st.write("📝 Notion")
    st.write("📚 RAG / PDF")

    st.divider()

    st.subheader("Capabilities")

    st.write("🔍 Project analysis")
    st.write("⚠️ Risk analysis")
    st.write("🚧 Blocker analysis")
    st.write("📋 Jira information")
    st.write("📧 Gmail information")
    st.write("📝 Notion information")

    st.divider()

    st.caption(
        "MCPPROJECT AI\n"
        "RAG + LangGraph + Jira + Gmail + Notion"
    )


# =========================================================
# MAIN INPUT
# =========================================================

st.subheader("Ask your project")

query = st.text_area(
    "Enter your question or action:",
    placeholder=(
        "Example: What are the risks and blockers "
        "in Project X?"
    ),
    height=120,
)


# =========================================================
# RUN AGENT
# =========================================================

run_button = st.button(
    "🚀 Run Agent",
    type="primary",
    use_container_width=True,
)


if run_button:

    if not query.strip():

        st.warning(
            "Please enter a question or request."
        )

    else:

        with st.spinner(
            "Agent is analyzing your request..."
        ):

            try:

                result = run_agent(
                    query.strip()
                )

            except Exception as exc:

                st.error(
                    "Agent execution failed."
                )

                st.exception(exc)

                result = None


        # =================================================
        # DISPLAY RESULT
        # =================================================

        if result:

            st.divider()

            st.subheader(
                "🤖 Agent Response"
            )

            # ---------------------------------------------
            # ACTION RESULT
            # ---------------------------------------------

            action_result = result.get(
                "action_result"
            )

            requested_action = result.get(
                "requested_action"
            )

            if requested_action:

                st.info(
                    "This request requires an external action."
                )

                st.write(
                    "**Requested Action:**"
                )

                st.json(
                    requested_action
                )

                if action_result:

                    status = action_result.get(
                        "status"
                    )

                    if status == "approval_required":

                        st.warning(
                            "Approval is required before "
                            "this action can be executed."
                        )

                    elif action_result.get(
                        "success"
                    ):

                        st.success(
                            "Action completed successfully."
                        )

                    else:

                        st.error(
                            "Action was not completed."
                        )

                    st.json(
                        action_result
                    )

            # ---------------------------------------------
            # FINAL ANSWER
            # ---------------------------------------------

            final_answer = result.get(
                "final_answer"
            )

            if final_answer:

                st.markdown(
                    "### 📊 Final Answer"
                )

                st.markdown(
                    final_answer
                )

            elif requested_action:

                st.info(
                    "The action request was processed "
                    "by the Action Agent."
                )

            else:

                st.warning(
                    "The agent did not return a final answer."
                )

            # ---------------------------------------------
            # AGENT DETAILS
            # ---------------------------------------------

            with st.expander(
                "🔍 Agent Details"
            ):

                st.markdown(
                    "### Agent Execution"
                )

                # -----------------------------------------
                # INTENT
                # -----------------------------------------

                intent = result.get(
                    "intent"
                )

                if intent:

                    st.write(
                        f"**Intent:** `{intent}`"
                    )

                else:

                    st.write(
                        "**Intent:** Not available"
                    )

                # -----------------------------------------
                # PROJECT
                # -----------------------------------------

                project_name = result.get(
                    "project_name"
                )

                if project_name:

                    st.write(
                        f"**Project:** `{project_name}`"
                    )

                else:

                    st.write(
                        "**Project:** Not available"
                    )

                # -----------------------------------------
                # REQUIRED SOURCES
                # -----------------------------------------

                required_sources = result.get(
                    "required_sources"
                )

                st.write(
                    "**Required Sources:**"
                )

                if required_sources:

                    for source in required_sources:

                        st.write(
                            f"• {str(source).upper()}"
                        )

                else:

                    st.write(
                        "• None"
                    )

                # -----------------------------------------
                # SUB QUESTIONS
                # -----------------------------------------

                sub_questions = result.get(
                    "sub_questions"
                )

                if sub_questions:

                    st.write(
                        "**Sub-questions:**"
                    )

                    for question in sub_questions:

                        st.write(
                            f"• {question}"
                        )

                # -----------------------------------------
                # RAW EVIDENCE
                # -----------------------------------------

                raw_evidence = result.get(
                    "raw_evidence"
                )

                if raw_evidence is not None:

                    st.write(
                        f"**Raw Evidence:** "
                        f"{len(raw_evidence)}"
                    )

                # -----------------------------------------
                # REDACTED EVIDENCE
                # -----------------------------------------

                redacted_evidence = result.get(
                    "redacted_evidence"
                )

                if redacted_evidence is not None:

                    st.write(
                        f"**Redacted Evidence:** "
                        f"{len(redacted_evidence)}"
                    )

                # -----------------------------------------
                # CITATION VALIDATION
                # -----------------------------------------

                citation_valid = result.get(
                    "citation_valid"
                )

                if citation_valid is not None:

                    if citation_valid:

                        st.success(
                            "Citation Validation: ✅ Passed"
                        )

                    else:

                        st.error(
                            "Citation Validation: ❌ Failed"
                        )

                # -----------------------------------------
                # OUTPUT VALIDATION
                # -----------------------------------------

                output_valid = result.get(
                    "output_valid"
                )

                if output_valid is not None:

                    if output_valid:

                        st.success(
                            "Output Validation: ✅ Passed"
                        )

                    else:

                        st.error(
                            "Output Validation: ❌ Failed"
                        )

                # -----------------------------------------
                # ERROR
                # -----------------------------------------

                error = result.get(
                    "error"
                )

                if error:

                    st.error(
                        f"Agent Error: {error}"
                    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "MCPPROJECT AI • RAG + LangGraph + Jira + Gmail + Notion"
)