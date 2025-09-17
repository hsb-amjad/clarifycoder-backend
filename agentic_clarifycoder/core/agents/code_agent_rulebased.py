"""
code_agent_rulebased.py
-------------
Rule-based CodeAgent v4 (extended + language awareness)

This agent generates simple Python code templates
based on clarified task descriptions.

If a non-Python language is requested, generates a polite stub instead.

Reproducibility:
- Purely deterministic (no randomness).
- Same clarified prompt → same code output.
"""

from typing import Dict


class CodeAgent:
    def __init__(self):
        self.templates = {
            # === Existing ===
            "factorial": """def factorial(n):\n    if n == 0 or n == 1:\n        return 1\n    return n * factorial(n-1)""",
            "save file": """def save_results(data, filename="results.txt"):\n    with open(filename, "w") as f:\n        f.write(str(data))""",
            "sort": """def sort_list(items):\n    return sorted(items)""",
            "classifier": """def train_classifier(X, y):\n    # Placeholder for classifier training\n    pass""",
            "fibonacci": """def fibonacci(n):\n    seq = [0, 1]\n    for i in range(2, n):\n        seq.append(seq[-1] + seq[-2])\n    return seq[:n]""",
            "prime": """def is_prime(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True""",
            "reverse": """def reverse_string(s):\n    return s[::-1]""",

            # === Math extensions ===
            "gcd": """def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a""",
            "lcm": """def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a\n\ndef lcm(a, b):\n    return abs(a*b) // gcd(a, b) if a and b else 0""",
            "power": """def power(base, exp):\n    return base ** exp""",

            # === Data structures ===
            "stack push": """def stack_push(stack, item):\n    stack.append(item)\n    return stack""",
            "stack pop": """def stack_pop(stack):\n    return stack.pop() if stack else None""",
            "merge dict": """def merge_dicts(d1, d2):\n    merged = d1.copy()\n    merged.update(d2)\n    return merged""",

            # === File handling ===
            "read file": """def read_file(filename):\n    with open(filename, "r") as f:\n        return f.read()""",
            "append file": """def append_to_file(data, filename="results.txt"):\n    with open(filename, "a") as f:\n        f.write(str(data))""",

            # === String ops ===
            "palindrome": """def is_palindrome(s):\n    return s == s[::-1]""",
            "word count": """def word_count(s):\n    return len(s.split())""",

            # === Regex ===
            "regex extract": """import re\ndef extract_numbers(text):\n    return re.findall(r'\\d+', text)""",
            "validate email": """import re\ndef validate_email(s):\n    return bool(re.match(r'^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$', s))""",

            # === Networking ===
            "http get": """import requests\ndef fetch_page(url):\n    resp = requests.get(url)\n    return resp.status_code""",
            "http post": """import requests\ndef send_post(url, payload):\n    resp = requests.post(url, json=payload)\n    return resp.status_code""",

            # === Database (SQLite) ===
            "sqlite select": """import sqlite3\ndef run_query(db_path):\n    conn = sqlite3.connect(db_path)\n    cur = conn.cursor()\n    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")\n    rows = cur.fetchall()\n    conn.close()\n    return rows""",
            "sqlite insert": """import sqlite3\ndef insert_user(db_path, user_id, name):\n    conn = sqlite3.connect(db_path)\n    cur = conn.cursor()\n    cur.execute("INSERT INTO users VALUES (?, ?)", (user_id, name))\n    conn.commit()\n    conn.close()""",

            # === System utilities ===
            "current time": """import datetime\ndef current_time():\n    return datetime.datetime.now().strftime("%Y-%m-%d")""",
            "list files": """import os\ndef list_files():\n    return os.listdir('.')""",
            "sleep": """import time\ndef pause(seconds):\n    time.sleep(seconds)\n    return True""",

            # === Stress/unsupported (dummy stubs) ===
            "opengl": """# OpenGL tasks not supported in baseline""",
            "tensorflow": """# TensorFlow tasks not supported in baseline""",
        }
        self.non_python_langs = ["c++", "java", "c#",
                                 "javascript", "ruby", "go", "rust", "c "]

    def run(self, clarified_prompt: str) -> Dict[str, str]:
        if not isinstance(clarified_prompt, str):
            raise TypeError("Clarified prompt must be a string")

        prompt_lower = clarified_prompt.lower()

        # === Non-Python language awareness ===
        if any(lang in prompt_lower for lang in self.non_python_langs):
            return {
                "clarified_prompt": clarified_prompt,
                "code": "# Non-Python language requested, but this system only supports Python."
            }

        # Special handling: if both "save" and "file" appear anywhere
        if "save" in prompt_lower and "file" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["save file"]}

        # Multi-keyword matching
        if "push" in prompt_lower and "stack" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["stack push"]}
        if "pop" in prompt_lower and "stack" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["stack pop"]}
        if "merge" in prompt_lower and "dict" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["merge dict"]}
        if "read" in prompt_lower and "file" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["read file"]}
        if "append" in prompt_lower and "file" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["append file"]}
        if "palindrome" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["palindrome"]}
        if "word" in prompt_lower and "count" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["word count"]}

        # Extended categories
        if "regex" in prompt_lower or "extract number" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["regex extract"]}
        if "email" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["validate email"]}
        if "http get" in prompt_lower or "fetch" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["http get"]}
        if "http post" in prompt_lower or "send post" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["http post"]}
        if "select" in prompt_lower and "sqlite" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["sqlite select"]}
        if "insert" in prompt_lower and "sqlite" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["sqlite insert"]}
        if "time" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["current time"]}
        if "list files" in prompt_lower or "directory" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["list files"]}
        if "sleep" in prompt_lower or "pause" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["sleep"]}
        if "opengl" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["opengl"]}
        if "tensorflow" in prompt_lower:
            return {"clarified_prompt": clarified_prompt, "code": self.templates["tensorflow"]}

        # Normal keyword matching
        for keyword, code in self.templates.items():
            if keyword in prompt_lower:
                return {"clarified_prompt": clarified_prompt, "code": code}

        # Default fallback if no template found
        return {"clarified_prompt": clarified_prompt, "code": "# Code template not found for this task"}
