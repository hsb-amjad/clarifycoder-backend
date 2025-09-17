"""
code_agent_llm.py
-----------------
CodeAgent (LLM-only version + language awareness)

Uses an OpenAI model to generate Python code
from clarified coding prompts.

If a non-Python language is requested, generates a polite stub instead.
"""

import re
from typing import Dict
from openai import OpenAI


class CodeAgentLLM:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = OpenAI()
        self.model = model
        self.non_python_langs = ["c++", "java", "c#",
                                 "javascript", "ruby", "go", "rust", "c"]

    def contains_non_python_lang(self, text: str) -> bool:
        text_l = text.lower()
        for lang in self.non_python_langs:
            # Use regex to match whole words only
            if re.search(rf"\b{re.escape(lang)}\b", text_l):
                return True
        return False

    def generate_code(self, clarified_prompt: str) -> str:
        if self.contains_non_python_lang(clarified_prompt):
            return "# Non-Python language requested, but this system only supports Python."

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system",
                 "content": "You are CodeAgent. Write correct, minimal Python code only. Do not explain."},
                {"role": "user", "content": clarified_prompt}
            ],
            temperature=0
        )
        return response.choices[0].message.content.strip()

    def run(self, clarified_prompt: str) -> Dict[str, str]:
        if not isinstance(clarified_prompt, str):
            raise TypeError("Clarified prompt must be a string")

        code = self.generate_code(clarified_prompt)
        return {"clarified_prompt": clarified_prompt, "code": code}
