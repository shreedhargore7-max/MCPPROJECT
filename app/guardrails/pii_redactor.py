import re
from typing import Dict, Any, List


# ---------------------------------------------------------
# PII / SENSITIVE DATA PATTERNS
# ---------------------------------------------------------

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

API_KEY_PATTERN = re.compile(
    r"\b(?:"
    r"sk-[A-Za-z0-9_-]{10,}"
    r"|AIza[A-Za-z0-9_-]{20,}"
    r"|ghp_[A-Za-z0-9_]{20,}"
    r")\b"
)

PHONE_PATTERN = re.compile(
    r"(?<!\d)"
    r"(?:\+91[\s-]?)?"
    r"(?:\d[\s-]?){10}"
    r"(?!\d)"
)

IP_ADDRESS_PATTERN = re.compile(
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
)


# ---------------------------------------------------------
# REDACT TEXT
# ---------------------------------------------------------

def redact_text(text: str) -> str:
    """
    Redact common PII and sensitive credentials.

    API keys are redacted before phone numbers so that
    numeric portions inside an API key are not incorrectly
    identified as phone numbers.
    """

    if not isinstance(text, str):
        return text

    redacted = text

    # -----------------------------------------------------
    # IMPORTANT:
    # API KEY MUST BE REDACTED BEFORE PHONE NUMBERS
    # -----------------------------------------------------

    redacted = API_KEY_PATTERN.sub(
        "[REDACTED API KEY]",
        redacted,
    )

    redacted = EMAIL_PATTERN.sub(
        "[REDACTED EMAIL]",
        redacted,
    )

    redacted = PHONE_PATTERN.sub(
        "[REDACTED PHONE]",
        redacted,
    )

    redacted = IP_ADDRESS_PATTERN.sub(
        "[REDACTED IP]",
        redacted,
    )

    return redacted


# ---------------------------------------------------------
# REDACT EVIDENCE
# ---------------------------------------------------------

def redact_evidence(
    evidence: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Redact sensitive information from retrieved evidence.

    The original evidence is not modified.
    """

    if not evidence:
        return []

    redacted_evidence: List[Dict[str, Any]] = []

    for item in evidence:

        if not isinstance(item, dict):
            continue

        redacted_item: Dict[str, Any] = {}

        for key, value in item.items():

            if isinstance(value, str):

                redacted_item[key] = redact_text(value)

            elif isinstance(value, list):

                redacted_item[key] = [
                    redact_text(element)
                    if isinstance(element, str)
                    else element
                    for element in value
                ]

            elif isinstance(value, dict):

                redacted_item[key] = {
                    nested_key: (
                        redact_text(nested_value)
                        if isinstance(nested_value, str)
                        else nested_value
                    )
                    for nested_key, nested_value
                    in value.items()
                }

            else:

                redacted_item[key] = value

        redacted_evidence.append(
            redacted_item
        )

    return redacted_evidence


# ---------------------------------------------------------
# DIRECT TEST
# ---------------------------------------------------------

def main():

    print("=" * 70)
    print("PII REDACTOR TEST")
    print("=" * 70)

    evidence = [
        {
            "source": "gmail",
            "subject": "Project X update",
            "content": (
                "Contact john.doe@example.com "
                "or call +91 9876543210."
            ),
        },
        {
            "source": "jira",
            "summary": "Database connection issue",
            "description": (
                "ServerIP is 192.168.1.100"
            ),
        },
        {
            "source": "rag",
            "content": (
                "API key: sk-1234567890abcdefghijk"
            ),
        },
    ]

    print()
    print("ORIGINAL EVIDENCE:")
    print("-" * 70)

    for item in evidence:
        print(item)

    redacted = redact_evidence(evidence)

    print()
    print("REDACTED EVIDENCE:")
    print("-" * 70)

    for item in redacted:
        print(item)

    print()
    print("TEST:")
    print("-" * 70)

    combined = str(redacted)

    checks = {
        "Email redacted":
            "[REDACTED EMAIL]" in combined,

        "Phone redacted":
            "[REDACTED PHONE]" in combined,

        "IP redacted":
            "[REDACTED IP]" in combined,

        "API key redacted":
            "[REDACTED API KEY]" in combined,
    }

    for name, passed in checks.items():

        print(
            f"{name}: "
            f"{'PASSED' if passed else 'FAILED'}"
        )


if __name__ == "__main__":
    main()