import os
import base64
from email.message import EmailMessage
from typing import List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# =========================================================
# CONFIGURATION
# =========================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

CREDENTIALS_FILE = os.path.join(
    BASE_DIR,
    "credentials.json"
)

TOKEN_FILE = os.path.join(
    BASE_DIR,
    "token.json"
)


# =========================================================
# GMAIL CONNECTION
# =========================================================

def get_gmail_service():
    """
    Authenticate with Gmail and return a Gmail API service.
    """

    creds = None

    # -----------------------------------------------------
    # Load existing token
    # -----------------------------------------------------

    if os.path.exists(TOKEN_FILE):

        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    # -----------------------------------------------------
    # Refresh existing credentials
    # -----------------------------------------------------

    if creds and creds.expired and creds.refresh_token:

        creds.refresh(Request())

    # -----------------------------------------------------
    # New authentication
    # -----------------------------------------------------

    elif not creds or not creds.valid:

        if not os.path.exists(CREDENTIALS_FILE):

            raise FileNotFoundError(
                "credentials.json was not found. "
                "Place credentials.json in the project root."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES
        )

        creds = flow.run_local_server(
            port=8080
        )

        with open(TOKEN_FILE, "w") as token:

            token.write(
                creds.to_json()
            )

    # -----------------------------------------------------
    # Build Gmail service
    # -----------------------------------------------------

    service = build(
        "gmail",
        "v1",
        credentials=creds
    )

    return service


# =========================================================
# EMAIL BODY DECODER
# =========================================================

def _decode_body(
    payload: Dict[str, Any]
) -> str:

    """
    Extract plain-text email body.
    """

    body = payload.get(
        "body",
        {}
    )

    data = body.get(
        "data"
    )

    if data:

        try:

            return base64.urlsafe_b64decode(
                data
            ).decode(
                "utf-8",
                errors="ignore"
            )

        except Exception:

            return ""

    parts = payload.get(
        "parts",
        []
    )

    # -----------------------------------------------------
    # Look for plain text
    # -----------------------------------------------------

    for part in parts:

        if part.get(
            "mimeType"
        ) == "text/plain":

            part_data = part.get(
                "body",
                {}
            ).get(
                "data"
            )

            if part_data:

                try:

                    return base64.urlsafe_b64decode(
                        part_data
                    ).decode(
                        "utf-8",
                        errors="ignore"
                    )

                except Exception:

                    return ""

    # -----------------------------------------------------
    # Recursively search parts
    # -----------------------------------------------------

    for part in parts:

        result = _decode_body(
            part
        )

        if result:

            return result

    return ""


# =========================================================
# SEARCH GMAIL
# =========================================================

def search_gmail(
    query: str,
    max_results: int = 10
) -> List[Dict[str, Any]]:

    """
    Search Gmail messages using Gmail search syntax.
    """

    if not query or not query.strip():

        raise ValueError(
            "Gmail search query cannot be empty."
        )

    service = get_gmail_service()

    response = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results
    ).execute()

    messages = response.get(
        "messages",
        []
    )

    results = []

    for message in messages:

        message_id = message.get(
            "id"
        )

        if not message_id:

            continue

        email = service.users().messages().get(
            userId="me",
            id=message_id,
            format="full"
        ).execute()

        payload = email.get(
            "payload",
            {}
        )

        headers = payload.get(
            "headers",
            []
        )

        subject = ""
        sender = ""
        date = ""

        for header in headers:

            name = header.get(
                "name",
                ""
            ).lower()

            value = header.get(
                "value",
                ""
            )

            if name == "subject":

                subject = value

            elif name == "from":

                sender = value

            elif name == "date":

                date = value

        body = _decode_body(
            payload
        )

        results.append(
            {
                "source": "gmail",
                "message_id": message_id,
                "subject": subject,
                "from": sender,
                "date": date,
                "body": body,
            }
        )

    return results


# =========================================================
# PROJECT EMAIL SEARCH
# =========================================================

def search_project_emails(
    project_name: str,
    max_results: int = 10
) -> List[Dict[str, Any]]:

    """
    Search Gmail for emails related to a project.
    """

    if not project_name:

        return []

    return search_gmail(
        f'"{project_name}"',
        max_results=max_results
    )


# =========================================================
# SEND EMAIL
# =========================================================

def send_email(
    to: str,
    subject: str,
    body: str
) -> Dict[str, Any]:

    """
    Send an email using Gmail API.

    IMPORTANT:
    This function only performs the Gmail write.
    Approval must be handled by the Action Agent
    before this function is called.
    """

    if not to or not to.strip():

        raise ValueError(
            "Recipient email address cannot be empty."
        )

    if not subject or not subject.strip():

        raise ValueError(
            "Email subject cannot be empty."
        )

    if body is None:

        raise ValueError(
            "Email body cannot be None."
        )

    service = get_gmail_service()

    message = EmailMessage()

    message["To"] = to.strip()
    message["Subject"] = subject.strip()

    message.set_content(
        body
    )

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    send_body = {
        "raw": encoded_message
    }

    response = service.users().messages().send(
        userId="me",
        body=send_body
    ).execute()

    return {
        "success": True,
        "status": "sent",
        "message_id": response.get("id"),
        "to": to.strip(),
        "subject": subject.strip(),
        "message": "Email sent successfully.",
    }


# =========================================================
# TEST
# =========================================================

def main():

    print("=" * 60)
    print("GMAIL TOOL TEST")
    print("=" * 60)

    print()
    print("Connecting to Gmail...")

    try:

        service = get_gmail_service()

        profile = service.users().getProfile(
            userId="me"
        ).execute()

        print()
        print("GMAIL CONNECTION SUCCESSFUL")

        print(
            f"Email: {profile.get('emailAddress')}"
        )

        # -------------------------------------------------
        # SEARCH TEST
        # -------------------------------------------------

        print()
        print("Searching recent emails...")

        results = search_gmail(
            "newer_than:30d",
            max_results=5
        )

        print(
            f"Retrieved {len(results)} emails."
        )

        for email in results:

            print()

            print(
                f"Subject: {email.get('subject')}"
            )

            print(
                f"From: {email.get('from')}"
            )

            print(
                f"Date: {email.get('date')}"
            )

        # -------------------------------------------------
        # SEND TEST
        # -------------------------------------------------

        print()
        print("SEND EMAIL TEST:")

        print(
            "Skipped intentionally."
        )

        print(
            "Real Gmail write operations require "
            "explicit approval through the Action Agent."
        )

    except Exception as exc:

        print()
        print("GMAIL ERROR")

        print(exc)

    print()
    print("=" * 60)
    print("GMAIL TOOL TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":

    main()