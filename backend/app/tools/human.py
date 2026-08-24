def ask_user(question: str) -> dict:
    """
    Ask the user a question to clarify missing constraints or preferences.

    Use this tool when the user's prompt is missing critical information
    like origin, destination, budget, or dates, and you need them to specify it
    rather than guessing.

    Args:
        question: The exact text of the question to ask the user.

    Returns:
        A dict containing the user's response.
    """
    # Note: Execution logic for this tool is intercepted by the agent loop
    # in app/agent/loop.py, which actually suspends execution and waits for input.
    # This function is just a dummy implementation for the registry to read the signature.
    return {"user_response": ""}
