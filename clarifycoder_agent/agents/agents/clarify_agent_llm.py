"""
clarify_agent_llm.py
--------------------
ClarifyAgent (LLM-only version + language awareness)

Uses an OpenAI model to detect ambiguities in coding prompts
and generate clarifying questions.

Now also detects non-Python language requests and clarifies that
only Python is supported.
"""

from typing import List, Dict
from openai import OpenAI


class ClarifyAgentLLM:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = OpenAI()
        self.model = model
        self.non_python_langs = ["c++", "java", "c#",
                                 "javascript", "ruby", "go", "rust", "c "]

    def detect_ambiguities(self, prompt: str) -> List[str]:
        prompt_l = prompt.lower()

        # === Language awareness ===
        if any(lang in prompt_l for lang in self.non_python_langs):
            return ["Currently only Python is supported. Do you want me to proceed in Python?"]

        # === Normal LLM clarification ===
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system",
                 "content": (
                     "You are ClarifyAgent. Detect if the prompt is ambiguous. "
                     "If clear, reply 'none'. "
                     "If ambiguous, return only ONE concise clarifying question that is most important. "
                     "Do NOT list multiple questions. "
                     "This system only supports Python."
                 )},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        text = response.choices[0].message.content.strip()
        if text.lower() in ["none", "clear", "no clarification needed"]:
            return []
        return [text]  # ✅ Always return just one

    def run(self, prompt: str) -> Dict[str, any]:
        if not isinstance(prompt, str):
            raise TypeError("Prompt must be a string")

        clarifications = self.detect_ambiguities(prompt)
        status = "ambiguous" if clarifications else "clear"

        return {
            "original_prompt": prompt,
            "clarifications": clarifications,
            "status": status
        }
