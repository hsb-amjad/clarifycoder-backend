# clarify_agent_clarifycoder.py

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel


class ClarifyAgentClarifyCoder:
    """
    Wrapper for Wu et al.'s ClarifyCoder model (fine-tuned DeepSeek Coder 6.7B).
    This agent decides whether to ask clarification questions or generate code directly.
    """

    def __init__(self,
                 base_model: str = "deepseek-ai/deepseek-coder-6.7b-instruct",
                 adapter_model: str = "jie-jw-wu/clarify-coder",
                 device: str = None):
        """
        Initialize the ClarifyCoder agent.

        Args:
            base_model: Hugging Face ID of the base model.
            adapter_model: Hugging Face ID of the fine-tuned adapter.
            device: "cuda" or "cpu". If None, auto-detects.
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        print(f"[ClarifyCoder] Loading base model: {base_model}")
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None
        )

        print(f"[ClarifyCoder] Loading adapter: {adapter_model}")
        self.model = PeftModel.from_pretrained(
            model,
            adapter_model,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        ).to(self.device)

        print(f"[ClarifyCoder] Model ready on {self.device}")

    def run(self, prompt: str, max_new_tokens: int = 200) -> str:
        """
        Run the ClarifyCoder model on a prompt.

        Args:
            prompt: User input (task description).
            max_new_tokens: Maximum number of tokens to generate.

        Returns:
            Model output (clarifying question or code).
        """
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return result


if __name__ == "__main__":
    # Quick test
    agent = ClarifyAgentClarifyCoder()

    test_prompts = [
        "Write a function that increments a list.",
        "Return a list with elements incremented by a number."  # ambiguous
    ]

    for p in test_prompts:
        print("\n=== Prompt ===")
        print(p)
        print("\n=== ClarifyCoder Response ===")
        print(agent.run(p))