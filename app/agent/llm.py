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
# LLM SETTINGS
# =========================================================

# Keep this small because the current OpenRouter
# account has limited remaining credits.
MAX_TOKENS = 512
TEMPERATURE = 0.2


# =========================================================
# LLM FUNCTION
# =========================================================

def ask_llm(prompt: str) -> str:
    """
    Send a prompt to OpenRouter and return
    the generated text.

    A small max_tokens value is intentionally used
    to reduce the cost of each request.
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
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )

    if not response.choices:
        return ""

    content = response.choices[0].message.content

    return content.strip() if content else ""