from app.agent.llm import ask_llm


def main():
    prompt = """
You are testing the LLM connection for an agentic AI project.

Explain in one short sentence what an agentic AI system is.
"""

    answer = ask_llm(prompt)

    print("OpenRouter LLM test PASSED!")
    print()
    print("LLM RESPONSE:")
    print(answer)


if __name__ == "__main__":
    main()