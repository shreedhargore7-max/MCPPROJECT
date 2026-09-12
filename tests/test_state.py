from app.agent.state import AgentState


def main():
    state: AgentState = {
        "user_query": "What is happening with Project X?",
        "intent": "project_analysis",
        "project_name": "Project X",
        "sub_questions": [
            "What are the project goals?",
            "What tasks are active?",
            "What deadlines changed?",
            "What blockers exist?",
        ],
    }

    print("AgentState test PASSED!")
    print()
    print("User Query:")
    print(state["user_query"])
    print()
    print("Project:")
    print(state["project_name"])
    print()
    print("Sub Questions:")

    for question in state["sub_questions"]:
        print(f"- {question}")


if __name__ == "__main__":
    main()