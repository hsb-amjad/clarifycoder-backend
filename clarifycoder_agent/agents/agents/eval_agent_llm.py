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

    def run(self, code: str) -> Dict[str, str]:
        if not isinstance(code, str):
            raise TypeError("Code must be a string")

        # Case 0: non-Python stub
        if code.strip().startswith("# Non-Python language requested"):
            return {"status": "unsupported", "function": None, "details": "Non-Python language requested"}

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system",
                 "content": (
                     "You are EvalAgent. Review the given Python code and decide if it correctly solves the task. "
                     "Reply with 'pass' or 'fail' and give a short reason."
                 )},
                {"role": "user", "content": code}
            ],
            temperature=0
        )

        text = response.choices[0].message.content.strip().lower()
        if text.startswith("pass"):
            status = "pass"
        elif text.startswith("fail"):
            status = "fail"
        else:
            status = "fail"

        return {
            "status": status,
            "function": None,
            "details": text
        }
