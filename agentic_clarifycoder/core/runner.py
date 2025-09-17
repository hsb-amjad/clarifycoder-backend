# clarifycoder-agent/runner.py

from .demo.demo import run_single_prompt


def run_clarifycoder(prompt: str, mode: str, answers: list = None, answer_mode: str = "auto"):
    """
    Bridge function for backend → ClarifyCoder pipeline.

    Args:
        prompt (str): user input
        mode (str): "baseline" or "llm"
        answers (list): optional answers (from frontend in human mode)
    Returns:
        dict with clarifications, answers, output, status, metrics
    """
    return run_single_prompt(prompt, mode, answers=answers, answer_mode=answer_mode)
