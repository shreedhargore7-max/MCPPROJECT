import os

from dotenv import load_dotenv
from openai import OpenAI


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()


OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

if not OPENROUTER_API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY is missing. "
        "Add it to the .env file."
    )


# =========================================================
# OPENROUTER CLIENT
# =========================================================

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


# =========================================================
# MODEL
# =========================================================

MODEL_NAME = "openai/gpt-oss-20b"


# =========================================================
# LLM FUNCTION
# =========================================================

def ask_llm(prompt: str) -> str:
    """
    Send a prompt to OpenRouter and return
    the generated text.

    A limited max_tokens value is used to avoid
    unnecessarily large requests.
    """

    if not prompt or not prompt.strip():
        return ""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        max_tokens=2048,
        temperature=0.2,
    )

    if not response.choices:
        return ""

    content = response.choices[0].message.content

    return content.strip() if content else ""