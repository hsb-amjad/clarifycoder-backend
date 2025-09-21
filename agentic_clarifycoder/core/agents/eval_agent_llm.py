"""
eval_agent_llm.py
-----------------
EvalAgent (LLM-only version + language awareness)

Uses an LLM to review code for correctness.
If the code is a non-Python stub, marks as 'unsupported'.
"""

from typing import Dict
from openai import OpenAI


class EvalAgentLLM:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = OpenAI()
        self.model = model

    def _clean_code(self, code: str) -> str:
        """
        Remove markdown fences (```python ... ```).
        """
        if not isinstance(code, str):
            raise TypeError("Code must be a string")
        return code.replace("```python", "").replace("```", "").strip()

    def run(self, code: str, task: str = None) -> Dict[str, str]:
        """
        Review Python code for correctness with respect to the given task.
        Returns a dict with status ('pass'/'fail'/'unsupported') and details.
        """
        # Case 0: non-Python stub
        if code.strip().startswith("# Non-Python language requested"):
            return {
                "status": "unsupported",
                "function": None,
                "details": "Non-Python language requested"
            }

        clean_code = self._clean_code(code)

        # Build conversation
        if task:
            user_content = f"Task: {task}\n\nCode:\n{clean_code}"
        else:
            user_content = f"Code:\n{clean_code}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are EvalAgent. Review the given Python code "
                        "and decide if it correctly solves the task. "
                        "Reply strictly with 'pass' or 'fail' followed by a short reason."
                    )
                },
                {"role": "user", "content": user_content}
            ],
            temperature=0
        )

        text = response.choices[0].message.content.strip().lower()

        # Flexible parsing
        if text.startswith("pass") or text.split()[0] == "pass":
            status = "pass"
        elif text.startswith("fail") or text.split()[0] == "fail":
            status = "fail"
        else:
            status = "fail"

        return {
            "status": status,
            "function": None,
            "details": text
        }
