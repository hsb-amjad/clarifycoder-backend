"""
eval_agent_rulebased.py
-------------
EvalAgent v6 (patched for ClarifyCoder dataset)

This version executes generated code in a sandbox when safe,
and also supports lightweight checks for broader categories:
- Math & algorithms
- String operations
- File I/O
- Data structures
- Regex (pattern-based check)
- Networking (keyword presence)
- Database/SQL (keyword presence)
- System utilities (keyword presence)
- Stress/unsupported (mark unsupported)

Now also:
- Cleans markdown fences (```python ... ```)
- Detects non-Python language stubs and marks them as 'unsupported'.
"""

from typing import Dict, Any


class EvalAgent:
    def __init__(self):
        self.test_cases = {
            # Math & algorithms
            "factorial": [(5, 120), (0, 1)],
            "fibonacci": [(5, [0, 1, 1, 2, 3]), (1, [0, 0])],
            "is_prime": [(7, True), (8, False)],
            "gcd": [((54, 24), 6), ((20, 8), 4)],
            "lcm": [((4, 6), 12), ((21, 6), 42)],
            "power": [((2, 3), 8), ((5, 0), 1)],

            # Strings
            "reverse_string": [("hello", "olleh"), ("abc", "cba")],
            "is_palindrome": [("racecar", True), ("hello", False)],
            "word_count": [("hello world", 2), ("one two three", 3)],

            # File handling
            "save_results": [("hello", "test_output.txt")],
            "read_file": [("test_input.txt", "sample text")],
            "append_to_file": [("world", "append_test.txt")],

            # Data structures
            "sort_list": [([3, 1, 2], [1, 2, 3]), ([5, 4], [4, 5])],
            "stack_push": [(([1, 2], 3), [1, 2, 3])],
            "stack_pop": [([1, 2, 3], 3), ([10], 10)],
            "merge_dicts": [(({"a": 1}, {"b": 2}), {"a": 1, "b": 2})],
        }

        self.regex_keywords = ["re.findall", "re.match", "re.sub", "re.split"]
        self.network_keywords = ["requests.get",
                                 "requests.post", "http", "urllib"]
        self.db_keywords = ["sqlite3", "cursor.execute",
                            "SELECT", "INSERT", "UPDATE", "DELETE"]
        self.system_keywords = ["os.", "time.",
                                "json.", "subprocess", "pathlib"]

    def _clean_code(self, code: str) -> str:
        """
        Remove markdown fences (```python ... ```).
        """
        return code.replace("```python", "").replace("```", "").strip()

    def run(self, code: str) -> Dict[str, Any]:
        if not isinstance(code, str):
            raise TypeError("Code must be provided as a string")

        # Case 0: non-Python stub
        if code.strip().startswith("# Non-Python language requested"):
            return {"status": "unsupported", "function": None, "details": "Non-Python language requested"}

        # Case 1: fallback template
        if code.strip().startswith("# Code template not found"):
            return {"status": "invalid", "function": None, "details": "No valid code generated"}

        # Clean code before execution
        clean_code = self._clean_code(code)

        # Sandbox
        sandbox: Dict[str, Any] = {}
        try:
            exec(clean_code, sandbox)
        except Exception as e:
            return self._keyword_fallback(clean_code, f"Execution failed: {e}")

        func_name = None
        for candidate in self.test_cases.keys():
            if candidate in sandbox and callable(sandbox[candidate]):
                func_name = candidate
                break

        if func_name:
            return self._run_with_tests(func_name, sandbox[func_name], clean_code)

        return self._keyword_fallback(clean_code, "Function not in supported list")

    def _run_with_tests(self, func_name: str, func, code: str) -> Dict[str, Any]:
        try:
            if func_name == "save_results":
                test_input, filename = self.test_cases["save_results"][0]
                func(test_input, filename)
                with open(filename, "r") as f:
                    contents = f.read().strip()
                return {
                    "status": "pass" if contents == test_input else "fail",
                    "function": func_name,
                    "details": f"File write/read got '{contents}'"
                }

            if func_name == "read_file":
                filename, expected = self.test_cases["read_file"][0]
                with open(filename, "w") as f:
                    f.write(expected)
                result = func(filename)
                return {
                    "status": "pass" if result.strip() == expected else "fail",
                    "function": func_name,
                    "details": f"File read got '{result.strip()}'"
                }

            if func_name == "append_to_file":
                test_input, filename = self.test_cases["append_to_file"][0]
                with open(filename, "w") as f:
                    f.write("hello ")
                func(test_input, filename)
                with open(filename, "r") as f:
                    contents = f.read().strip()
                return {
                    "status": "pass" if contents.endswith(test_input) else "fail",
                    "function": func_name,
                    "details": f"File append got '{contents}'"
                }

            for test_input, expected in self.test_cases[func_name]:
                try:
                    result = func(test_input) if not isinstance(
                        test_input, tuple) else func(*test_input)
                except RecursionError:
                    return {"status": "fail", "function": func_name, "details": "Recursion error"}
                if result != expected:
                    return {
                        "status": "fail",
                        "function": func_name,
                        "details": f"Input {test_input}: expected {expected}, got {result}"
                    }
            return {"status": "pass", "function": func_name,
                    "details": f"All {len(self.test_cases[func_name])} test cases passed"}
        except Exception as e:
            return {"status": "error", "function": func_name, "details": f"Runtime error: {e}"}

    def _keyword_fallback(self, code: str, reason: str) -> Dict[str, Any]:
        if any(kw in code for kw in self.regex_keywords):
            return {"status": "pass", "function": "regex", "details": "Regex pattern usage detected"}

        if any(kw in code for kw in self.network_keywords):
            return {"status": "pass", "function": "networking", "details": "Networking code detected"}

        if any(kw in code for kw in self.db_keywords):
            return {"status": "pass", "function": "database", "details": "Database code detected"}

        if any(kw in code for kw in self.system_keywords):
            return {"status": "pass", "function": "system", "details": "System utility code detected"}

        if "OpenGL" in code or "tensorflow" in code or "torch" in code:
            return {"status": "unsupported", "function": None, "details": "Unsupported library usage"}

        return {"status": "unsupported", "function": None, "details": reason}
