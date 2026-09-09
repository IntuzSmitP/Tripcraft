def ask_user(question: str) -> dict:
    """
    Suspends agent execution to solicit clarifying input from the user.

    This tool acts as a circuit breaker when the LLM detects underspecified
    requirements (e.g., missing destination, budget, or dates). Instead of
    hallucinating parameters, the agent halts and prompts the user directly.

    Args:
        question: The precise clarification requested by the agent.

    Returns:
        A dictionary wrapping the raw user input string.
    """
    # Note: Execution logic for this tool is intercepted by the agent loop
    # in app/agent/loop.py, which actually suspends execution and waits for input.
    # This function is just a dummy implementation for the registry to read the signature.
    return {"user_response": ""}
