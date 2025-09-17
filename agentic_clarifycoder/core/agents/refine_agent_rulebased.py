"""
refine_agent_rulebased.py
---------------
RefineAgent v1.3 (improved)

This agent attempts to fix failed code based on EvalAgent feedback.
Rule-based with simple text substitutions:
- Insert missing 'return' in factorial
- Add missing colon in function definitions
"""

from typing import Dict


class RefineAgent:
    def __init__(self):
        pass

    def run(self, code: str, eval_feedback: Dict[str, str]) -> Dict[str, str]:
        """
        Try to refine the code based on evaluation feedback.

        Args:
            code (str): The generated code snippet.
            eval_feedback (dict): Output from EvalAgent (status + details).

        Returns:
            dict: {
                "refined_code": str,
                "action": str
            }
        """
        status = eval_feedback.get("status", "")
        details = eval_feedback.get("details", "").lower()

        # --- Rule 1: Fix missing return in factorial ---
        if status == "fail":
            if "got none" in details:
                lines = code.splitlines()
                fixed_lines = []
                for line in lines:
                    # if line is just "1" (with indentation), replace with "return 1"
                    if line.strip() == "1":
                        indent = line[:len(line) - len(line.lstrip())]
                        fixed_lines.append(indent + "return 1")
                    else:
                        fixed_lines.append(line)
                refined_code = "\n".join(fixed_lines)
                return {"refined_code": refined_code, "action": "Inserted missing return"}
            return {"refined_code": code, "action": "No simple fix available"}

        # --- Rule 2: Fix missing colon in function definition ---
        if status == "error" and "invalid syntax" in details:
            if "def " in code and not code.strip().startswith("#"):
                lines = code.splitlines()
                fixed_lines = []
                for line in lines:
                    if line.strip().startswith("def ") and not line.strip().endswith(":"):
                        fixed_lines.append(line.rstrip() + ":")
                    else:
                        fixed_lines.append(line)
                refined_code = "\n".join(fixed_lines)
                return {"refined_code": refined_code, "action": "Added missing colon in function definition"}

            return {"refined_code": code, "action": "Execution error - no fix"}

        # --- Unsupported functions ---
        if status == "unsupported":
            return {"refined_code": code, "action": "Unsupported function - no fix"}

        # --- Default ---
        return {"refined_code": code, "action": "No refinement needed"}
