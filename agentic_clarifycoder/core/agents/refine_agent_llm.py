"""
refine_agent_llm.py
-------------------
RefineAgent (LLM-only version)

Uses an LLM to repair broken or incorrect code
based on evaluation feedback.
"""

from typing import Dict
from openai import OpenAI


class RefineAgentLLM:
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Args:
            model (str): LLM model name to use.
        """
        self.client = OpenAI()
        self.model = model

    def run(self, code: str, eval_feedback: Dict[str, str]) -> Dict[str, str]:
        """
        Use LLM to refine code given EvalAgent feedback.

        Args:
            code (str): The generated code snippet.
            eval_feedback (dict): Feedback from EvalAgent.

        Returns:
            dict: {
                "refined_code": str,
                "action": str
            }
        """
        feedback_text = eval_feedback.get("details", "No feedback provided.")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system",
                 "content": "You are RefineAgent. Fix Python code using feedback from EvalAgent. Return only corrected code."},
                {"role": "user", "content": f"Code:\n{code}\n\nFeedback:\n{feedback_text}"}
            ],
            temperature=0
        )

        refined_code = response.choices[0].message.content.strip()

        return {
            "refined_code": refined_code,
            "action": f"Refined with LLM using feedback: {feedback_text}"
        }
