"""
answer_agent.py
---------------
AnswerAgent for ClarifyCoder

Takes ClarifyAgent's clarification questions and provides answers:
- Human mode: asks user (frontend or CLI depending on flag)
- Auto mode : uses LLM to generate very short answers (1–3 words)

Also returns Q/A pairs for logging into answer.jsonl
"""

from typing import List, Dict
from openai import OpenAI


class AnswerAgent:
    def __init__(self, mode: str = "auto", model: str = "gpt-4o-mini", cli: bool = False):
        """
        Args:
            mode (str): "human" or "auto"
            model (str): LLM model name (default: gpt-4o-mini)
            cli (bool): If True, enable interactive Q&A for terminal runs
        """
        if mode not in ["human", "auto"]:
            raise ValueError("AnswerAgent supports only 'human' or 'auto' mode")
        self.mode = mode
        self.model = model
        self.cli = cli
        self.client = OpenAI()

    def run(self, clarifications: List[str], prompt: str, answers: List[str] = None) -> Dict[str, any]:
        """
        Provide answers to ClarifyAgent's questions.

        - If auto → query LLM for short, natural answers (1–3 words).
        - If human → use answers provided by frontend (web) or input() (CLI).
        """
        if not clarifications:
            return {"answers": [], "qa_pairs": [], "augmented_prompt": prompt}

        # Human mode
        if self.mode == "human":
            if not answers:
                if self.cli:
                    # CLI interactive Q&A
                    answers = []
                    for q in clarifications:
                        ans = input(f"[ClarifyAgent] {q}\nYour answer: ")
                        answers.append(ans.strip())
                else:
                    # Web/frontend mode → wait for answers to be supplied later
                    return {"answers": [], "qa_pairs": [], "augmented_prompt": prompt}

            qa_pairs = [{"question": q, "answer": a} for q, a in zip(clarifications, answers)]
            augmented_prompt = prompt + "\n" + "\n".join([f"Answer: {a}" for a in answers])
            return {"answers": answers, "qa_pairs": qa_pairs, "augmented_prompt": augmented_prompt}

        # Auto mode (LLM-generated answers)
        auto_answers = []
        for q in clarifications:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a precise assistant. "
                                "Answer in ONLY 1–3 words. "
                                "No explanations, no full sentences."
                            ),
                        },
                        {"role": "user", "content": q},
                    ],
                    max_tokens=10,
                    temperature=0.2
                )
                ans = response.choices[0].message.content.strip()
            except Exception as e:
                ans = "N/A"
                print(f"[AnswerAgent] LLM fallback due to error: {e}")
            auto_answers.append(ans)

        qa_pairs = [{"question": q, "answer": a} for q, a in zip(clarifications, auto_answers)]
        augmented_prompt = prompt + "\n" + "\n".join([f"Answer: {a}" for a in auto_answers])

        return {"answers": auto_answers, "qa_pairs": qa_pairs, "augmented_prompt": augmented_prompt}
