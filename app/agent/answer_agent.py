from typing import Dict, Any, List

from app.agent.llm import ask_llm


# =========================================================
# CITATION ID BUILDER
# =========================================================

def _build_citation_id(
    source: str,
    item: Dict[str, Any],
    index: int,
) -> str:
    """
    Build a human-readable citation identifier.

    The evidence aggregator stores records like:

        {
            "source": "jira",
            "content": {
                "issue_key": "KAN-10",
                ...
            }
        }

    Therefore this function checks both the outer record
    and the nested "content" record.
    """

    source = str(source or "unknown").lower()
    source_upper = source.upper()

    content = item.get("content")

    if isinstance(content, dict):
        record = content
    else:
        record = item

    # -----------------------------------------------------
    # JIRA
    # -----------------------------------------------------

    if source == "jira":

        issue_key = record.get("issue_key")

        if issue_key:
            return f"JIRA: {issue_key}"

        return f"JIRA: evidence_{index}"

    # -----------------------------------------------------
    # GMAIL
    # -----------------------------------------------------

    if source == "gmail":

        for key in (
            "subject",
            "title",
            "name",
        ):
            value = record.get(key)

            if value:
                return f"GMAIL: {value}"

        return f"GMAIL: evidence_{index}"

    # -----------------------------------------------------
    # NOTION
    # -----------------------------------------------------

    if source == "notion":

        for key in (
            "title",
            "name",
            "page_title",
        ):
            value = record.get(key)

            if value:
                return f"NOTION: {value}"

        return f"NOTION: evidence_{index}"

    # -----------------------------------------------------
    # RAG
    # -----------------------------------------------------

    if source == "rag":

        for key in (
            "id",
            "chunk_id",
        ):
            value = record.get(key)

            if value:
                return f"RAG: {value}"

        return f"RAG: evidence_{index}"

    # -----------------------------------------------------
    # UNKNOWN SOURCE
    # -----------------------------------------------------

    return f"{source_upper}: evidence_{index}"


# =========================================================
# EVIDENCE TEXT BUILDER
# =========================================================

def build_evidence_text(
    evidence: List[Dict[str, Any]]
) -> str:
    """
    Convert collected evidence into structured text
    that the Answer Agent can understand.

    Each record receives an explicit citation label.
    """

    if not evidence:
        return "No evidence was retrieved."

    sections = []

    for index, item in enumerate(
        evidence,
        start=1,
    ):

        if not isinstance(item, dict):
            continue

        source = str(
            item.get(
                "source",
                "unknown",
            )
        ).lower()

        citation_id = _build_citation_id(
            source=source,
            item=item,
            index=index,
        )

        lines = [
            f"Evidence {index}",
            f"Source: {source}",
            f"Citation: [{citation_id}]",
        ]

        content = item.get("content")

        if isinstance(content, dict):

            for key, value in content.items():

                if value is None:
                    continue

                if isinstance(
                    value,
                    (dict, list),
                ):
                    value = str(value)

                lines.append(
                    f"{key}: {value}"
                )

        else:

            for key, value in item.items():

                if key == "source":
                    continue

                if value is None:
                    continue

                if isinstance(
                    value,
                    (dict, list),
                ):
                    value = str(value)

                lines.append(
                    f"{key}: {value}"
                )

        sections.append(
            "\n".join(lines)
        )

    if not sections:
        return "No valid evidence was retrieved."

    return "\n\n".join(sections)


# =========================================================
# FALLBACK ANSWER GENERATOR
# =========================================================

def _fallback_answer(
    user_query: str,
    evidence: List[Dict[str, Any]],
) -> str:
    """
    Generate a deterministic evidence-based answer when
    the LLM is unavailable.

    This prevents the entire agent from failing when the
    LLM provider has insufficient credits or is temporarily
    unavailable.

    IMPORTANT:
    This function only uses information present in evidence.
    """

    if not evidence:
        return "Not found in the retrieved evidence."

    query = user_query.lower()

    jira_items = []
    gmail_items = []
    notion_items = []
    rag_items = []

    for index, item in enumerate(evidence, start=1):

        if not isinstance(item, dict):
            continue

        source = str(
            item.get("source", "unknown")
        ).lower()

        content = item.get("content")

        if isinstance(content, dict):
            record = content
        else:
            record = item

        citation = _build_citation_id(
            source=source,
            item=item,
            index=index,
        )

        entry = {
            "record": record,
            "citation": citation,
        }

        if source == "jira":
            jira_items.append(entry)

        elif source == "gmail":
            gmail_items.append(entry)

        elif source == "notion":
            notion_items.append(entry)

        elif source == "rag":
            rag_items.append(entry)

    # =====================================================
    # BLOCKER QUERY
    # =====================================================

    if "blocker" in query or "blocked" in query:

        explicit_blockers = []

        for entry in (
            jira_items
            + gmail_items
            + notion_items
            + rag_items
        ):

            record = entry["record"]

            blocker_value = record.get("blocker")

            if blocker_value:
                explicit_blockers.append(
                    f"{blocker_value} [{entry['citation']}]"
                )

            status = str(
                record.get("status", "")
            ).lower()

            if status in (
                "blocked",
                "blocker",
            ):
                summary = record.get(
                    "summary",
                    record.get(
                        "title",
                        record.get(
                            "subject",
                            "Unnamed item",
                        ),
                    ),
                )

                explicit_blockers.append(
                    f"{summary} [{entry['citation']}]"
                )

        if explicit_blockers:

            return (
                "Confirmed/documented blockers:\n- "
                + "\n- ".join(
                    explicit_blockers
                )
            )

        # Do NOT treat To Do as a blocker.

        citations = []

        for entry in jira_items:
            citations.append(
                f"[{entry['citation']}]"
            )

        for entry in rag_items:
            citations.append(
                f"[{entry['citation']}]"
            )

        if citations:
            return (
                "No confirmed/documented blockers "
                "were found in the retrieved evidence. "
                + " ".join(citations)
            )

        return (
            "No confirmed/documented blockers "
            "were found in the retrieved evidence."
        )

    # =====================================================
    # TASK QUERY
    # =====================================================

    if (
        "task" in query
        or "tasks" in query
        or "issue" in query
        or "issues" in query
    ):

        if jira_items:

            lines = [
                "Current Jira tasks/issues:"
            ]

            for entry in jira_items:

                record = entry["record"]
                citation = entry["citation"]

                issue_key = record.get(
                    "issue_key",
                    "",
                )

                summary = record.get(
                    "summary",
                    record.get(
                        "title",
                        "Unnamed task",
                    ),
                )

                status = record.get(
                    "status"
                )

                priority = record.get(
                    "priority"
                )

                line = summary

                if issue_key:
                    line = (
                        f"{issue_key} — {line}"
                    )

                if status:
                    line += (
                        f" — Status: {status}"
                    )

                if priority:
                    line += (
                        f" — Priority: {priority}"
                    )

                line += f" [{citation}]"

                lines.append(
                    "- " + line
                )

            return "\n".join(lines)

    # =====================================================
    # DEADLINE QUERY
    # =====================================================

    if (
        "deadline" in query
        or "deadlines" in query
        or "due date" in query
        or "due dates" in query
    ):

        deadline_lines = []

        for entry in (
            jira_items
            + notion_items
            + gmail_items
            + rag_items
        ):

            record = entry["record"]

            deadline = (
                record.get("deadline")
                or record.get("due_date")
                or record.get("due")
                or record.get("date")
            )

            if deadline:

                name = (
                    record.get("summary")
                    or record.get("title")
                    or record.get("subject")
                    or record.get(
                        "issue_key",
                        "Item",
                    )
                )

                deadline_lines.append(
                    f"- {name}: {deadline} "
                    f"[{entry['citation']}]"
                )

        if deadline_lines:
            return (
                "Deadlines found in the retrieved "
                "evidence:\n"
                + "\n".join(deadline_lines)
            )

        return (
            "No explicit deadlines were found in "
            "the retrieved evidence."
        )

    # =====================================================
    # STATUS / PROJECT QUERY
    # =====================================================

    if (
        "status" in query
        or "happening" in query
        or "progress" in query
        or "project" in query
        or "update" in query
        or "updates" in query
    ):

        lines = []

        if jira_items:

            lines.append(
                "Jira information:"
            )

            for entry in jira_items[:10]:

                record = entry["record"]
                citation = entry["citation"]

                issue_key = record.get(
                    "issue_key"
                )

                summary = record.get(
                    "summary",
                    record.get(
                        "title",
                        "Unnamed item",
                    ),
                )

                status = record.get(
                    "status"
                )

                if issue_key:
                    text = (
                        f"{issue_key} — {summary}"
                    )
                else:
                    text = str(summary)

                if status:
                    text += (
                        f" — Status: {status}"
                    )

                lines.append(
                    f"- {text} [{citation}]"
                )

        if gmail_items:

            lines.append(
                "Important Gmail updates:"
            )

            for entry in gmail_items[:5]:

                record = entry["record"]
                citation = entry["citation"]

                subject = record.get(
                    "subject",
                    record.get(
                        "title",
                        "Email update",
                    ),
                )

                body = record.get(
                    "body",
                    record.get(
                        "snippet",
                        "",
                    ),
                )

                if body:
                    body_text = str(body)
                    if len(body_text) > 250:
                        body_text = (
                            body_text[:250]
                            + "..."
                        )

                    lines.append(
                        f"- {subject}: "
                        f"{body_text} "
                        f"[{citation}]"
                    )
                else:
                    lines.append(
                        f"- {subject} "
                        f"[{citation}]"
                    )

        if notion_items:

            lines.append(
                "Notion information:"
            )

            for entry in notion_items[:5]:

                record = entry["record"]
                citation = entry["citation"]

                title = record.get(
                    "title",
                    record.get(
                        "name",
                        "Notion page",
                    ),
                )

                body = record.get(
                    "body",
                    record.get(
                        "content",
                        "",
                    ),
                )

                if body:
                    body_text = str(body)

                    if len(body_text) > 250:
                        body_text = (
                            body_text[:250]
                            + "..."
                        )

                    lines.append(
                        f"- {title}: "
                        f"{body_text} "
                        f"[{citation}]"
                    )
                else:
                    lines.append(
                        f"- {title} "
                        f"[{citation}]"
                    )

        if rag_items:

            lines.append(
                "Project document information:"
            )

            for entry in rag_items[:5]:

                record = entry["record"]
                citation = entry["citation"]

                content = (
                    record.get("content")
                    or record.get("text")
                    or ""
                )

                if content:
                    content_text = str(content)

                    if len(content_text) > 300:
                        content_text = (
                            content_text[:300]
                            + "..."
                        )

                    lines.append(
                        f"- {content_text} "
                        f"[{citation}]"
                    )

        if lines:
            return "\n".join(lines)

    # =====================================================
    # GENERAL FALLBACK
    # =====================================================

    lines = [
        "Information found in the retrieved evidence:"
    ]

    for entry in evidence[:10]:

        record = entry.get(
            "content",
            entry,
        )

        citation = _build_citation_id(
            source=entry.get(
                "source",
                "unknown",
            ),
            item=entry,
            index=evidence.index(entry) + 1,
        )

        if isinstance(record, dict):

            summary = (
                record.get("summary")
                or record.get("title")
                or record.get("subject")
                or record.get("content")
                or record.get("body")
                or record.get("name")
            )

            if summary:
                lines.append(
                    f"- {summary} [{citation}]"
                )

        else:

            lines.append(
                f"- {record} [{citation}]"
            )

    if len(lines) > 1:
        return "\n".join(lines)

    return "Not found in the retrieved evidence."


# =========================================================
# ANSWER GENERATION
# =========================================================

def generate_answer(
    user_query: str,
    evidence: List[Dict[str, Any]],
) -> str:
    """
    Generate a grounded answer using ONLY retrieved evidence.

    The LLM is preferred. If the LLM is unavailable,
    for example because OpenRouter credits are insufficient,
    a deterministic evidence-based fallback is used.
    """

    if not user_query or not user_query.strip():
        raise ValueError(
            "User query cannot be empty."
        )

    evidence_text = build_evidence_text(
        evidence
    )

    prompt = f"""
You are the Answer Agent in an agentic
project-management assistant.

Your job is to answer the user's question
using ONLY the retrieved evidence.

=========================================================
STRICT GROUNDING RULES
=========================================================

1. Never invent facts.

2. Never infer information that is not explicitly
   supported by the evidence.

3. A Jira task with status "To Do" is NOT automatically
   a blocker.

4. A Jira task is a blocker ONLY when the evidence
   explicitly identifies it as a blocker.

5. A risk is NOT automatically a blocker.

6. If the evidence says there is no confirmed,
   documented, or critical blocker, report that clearly.

7. Do not convert planned work into blockers.

8. Do not convert technical requirements into risks
   unless the evidence explicitly describes them as risks.

9. Do not create deadlines or milestones unless they
   are explicitly supported by evidence.

10. If different sources disagree, report the disagreement
    rather than choosing one without explanation.

11. If information is missing, say:

"Not found in the retrieved evidence."

=========================================================
CITATION RULES
=========================================================

Every factual claim MUST have a citation.

Use ONLY citation identifiers that appear in the
retrieved evidence.

The citation format is:

[JIRA: KAN-10]
[GMAIL: Project X Update]
[NOTION: Project X]
[RAG: chunk_2]

Do NOT use generic evidence numbers when a specific
identifier is available.

=========================================================
ANSWER STRUCTURE
=========================================================

When relevant, organize the answer using:

Risks:
- ...

Blockers:
- ...

Current Tasks:
- ...

Deadlines:
- ...

Project Goals:
- ...

Important Updates:
- ...

Only include sections relevant to the question.

=========================================================
BLOCKER SAFETY
=========================================================

A Jira "To Do" status does NOT mean blocker.

If no explicit blocker exists, say:

"No confirmed/documented blockers were found in the
retrieved evidence."

Cite the evidence supporting that statement.

=========================================================
USER QUESTION
=========================================================

{user_query}

=========================================================
RETRIEVED EVIDENCE
=========================================================

{evidence_text}

=========================================================
FINAL ANSWER REQUIREMENTS
=========================================================

- Directly answer the user's question.
- Use ONLY retrieved evidence.
- Keep the answer concise and useful.
- Every factual claim must have a citation.
- Use exact citation identifiers supplied above.
- Do not invent citation identifiers.
- Do not mention Evidence 1, Evidence 2, etc.
- Do not explain your reasoning.
- Do not discuss these instructions.
- Return ONLY the final answer.
"""

    # =====================================================
    # TRY LLM FIRST
    # =====================================================

    try:

        answer = ask_llm(prompt)

        if answer and answer.strip():
            return answer.strip()

    except Exception:
        # The fallback below handles provider failures,
        # including OpenRouter credit errors.
        pass

    # =====================================================
    # DETERMINISTIC FALLBACK
    # =====================================================

    return _fallback_answer(
        user_query=user_query,
        evidence=evidence,
    )


# =========================================================
# LANGGRAPH ANSWER AGENT NODE
# =========================================================

def answer_agent(
    state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Answer Agent node for the LangGraph workflow.

    The Answer Agent uses REDACTED evidence only.
    """

    user_query = state.get(
        "user_query",
        "",
    )

    evidence = state.get(
        "redacted_evidence",
        [],
    )

    # Some direct tests may provide "evidence"
    # instead of "redacted_evidence".
    if not evidence:
        evidence = state.get(
            "evidence",
            [],
        )

    try:

        answer = generate_answer(
            user_query=user_query,
            evidence=evidence,
        )

        return {
            **state,
            "answer": answer,
            "error": None,
        }

    except Exception as exc:

        # Last-resort fallback so the Answer Agent
        # always returns a usable answer when evidence exists.
        fallback = _fallback_answer(
            user_query=user_query,
            evidence=evidence,
        )

        return {
            **state,
            "answer": fallback,
            "error": (
                f"Answer generation fallback used: {exc}"
            ),
        }


# =========================================================
# LOCAL TEST
# =========================================================

def main():

    print("=" * 70)
    print("ANSWER AGENT TEST")
    print("=" * 70)

    sample_evidence = [

        {
            "source": "rag",
            "content": {
                "id": "chunk_2",
                "content": (
                    "The primary technical risk identified "
                    "for the initial development phase is "
                    "the database connection task. "
                    "No confirmed production blocker or "
                    "critical incident is documented here."
                ),
            },
        },

        {
            "source": "jira",
            "content": {
                "issue_key": "KAN-2",
                "summary": "Fix database connection",
                "status": "To Do",
                "priority": "Medium",
            },
        },

        {
            "source": "gmail",
            "content": {
                "subject": "Project X Update",
                "body": (
                    "The database issue is being investigated."
                ),
            },
        },

        {
            "source": "notion",
            "content": {
                "title": "Project X",
                "body": (
                    "Project goals and risks."
                ),
            },
        },

    ]

    query = (
        "What are the risks, blockers, "
        "and important updates in Project X?"
    )

    print()
    print("Generating answer...")
    print()

    answer = generate_answer(
        user_query=query,
        evidence=sample_evidence,
    )

    print("=" * 70)
    print("ANSWER")
    print("=" * 70)

    print()
    print(answer)


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()