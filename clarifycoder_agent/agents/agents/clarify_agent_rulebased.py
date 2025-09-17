"""
clarify_agent_rulebased.py
----------------
Rule-based ClarifyAgent v5 (fair baseline + language awareness).

Detects ambiguities in coding prompts using regex/keyword rules
and generates clarifying questions.

Now also detects non-Python language requests and clarifies that
only Python is supported.
"""

import re
from typing import List


class ClarifyAgent:
    def __init__(self):
        self.rules = {
            # === File I/O ===
            "save_file": ("save file", "What file format should I use (txt, csv, json)?"),
            "read_file": ("read file", "From which file and in what format?"),
            "append_file": ("append file", "Should I append or overwrite the file?"),

            # === Sorting / Data structures ===
            "sort": ("sort", "What type of data do you want to sort (list, dictionary, dataframe)?"),
            "find_max": ("find max", "Find maximum in what (list, dict, matrix)?"),
            "traverse_graph": ("traverse graph", "Which algorithm should I use (BFS, DFS)?"),
            "depth": ("depth", "Do you want maximum depth, minimum depth, or all levels?"),

            # === Math ===
            "factorial": ("factorial", "Should I implement factorial iteratively or recursively?"),
            "fibonacci": ("fibonacci", "Do you want first n terms or up to a maximum value?"),
            "prime": ("prime", "Check primality for a single number or a range of numbers?"),
            "gcd": ("gcd", "Find gcd of how many numbers?"),
            "lcm": ("lcm", "Should I use gcd-based formula or brute force?"),
            "power": ("power", "Do you want integer exponentiation or floating power?"),

            # === ML ===
            "classifier": ("classifier", "Which classification algorithm should I use (SVM, Random Forest, Logistic Regression)?"),

            # === Printing / Results ===
            "print_results": ("print results", "Should I print all results or just summary statistics?"),

            # === Strings ===
            "reverse": ("reverse", "Do you want to reverse characters or words?"),
            "palindrome": ("palindrome", "Should I ignore case and spaces when checking palindrome?"),
            "frequency": ("frequency", "Do you want word frequency or character frequency?"),
            "substring": ("substring", "Which substring should I search for?"),
            "replace": ("replace", "Which word should I replace, and with what?"),
            "anagram": ("anagram", "Which two words should I compare for being anagrams?"),

            # === Networking ===
            "network": ("request", "Do you want a GET or POST request? What URL and payload?"),
            "headers": ("header", "Should I include authentication or custom headers?"),
            "timeout": ("timeout", "What timeout duration should I use for the request?"),

            # === Database / SQL ===
            "query": ("query", "Which database and table should I use?"),
            "create_table": ("create table", "What schema should the new table have?"),
            "drop_table": ("drop table", "Do you want a safe check before dropping the table?"),

            # === Regex ===
            "extract_numbers": ("extract numbers", "Extract numbers from where (string, file)?"),
            "email": ("email", "Should I use strict or simple regex for email validation?"),
            "phone": ("phone", "What phone number format should I expect?"),
            "hashtag": ("hashtag", "Do you want to extract hashtags including the '#' symbol or without it?"),

            # === System utilities ===
            "time": ("time", "Do you want current system time, execution time, or formatted date?"),
            "list_files": ("list files", "From which directory should I list files?"),
            "env": ("env", "Which environment variable should I fetch?"),
            "sleep": ("sleep", "How many seconds should I pause?"),
            "directory": ("directory", "Do you want the current working directory or to change it?"),

            # === Stress / Unsupported ===
            "cube": ("cube", "Do you mean a 2D ASCII cube or 3D OpenGL rendering?"),
            "game": ("game", "Which game do you want to build (chess, tic-tac-toe, etc.)?"),
            "large_factorial": ("factorial large", "Do you want the exact value or just approximate size?"),
            "recursion": ("recursion", "How deep should the recursion go?"),
            "big_list": ("big list", "How many elements do you want in the list?"),
            "tensorflow": ("tensorflow", "Are you sure you want to use TensorFlow here? (unsupported in baseline)"),
            "opengl": ("opengl", "Are you sure you want to use OpenGL here? (unsupported in baseline)"),
        }
        # Keywords for non-Python languages
        self.non_python_langs = ["c++", "java", "c#", "javascript", "ruby", "go", "rust", "c "]

    def detect_ambiguities(self, prompt: str) -> List[str]:
        prompt_l = prompt.lower()
        questions = []

        # === Language awareness ===
        if any(lang in prompt_l for lang in self.non_python_langs):
            return ["Currently only Python is supported. Do you want me to proceed in Python?"]

        # === Regular rules with context checks ===
        for key, (trigger, question) in self.rules.items():
            if trigger in prompt_l:
                if key == "replace" and "with" in prompt_l:
                    continue
                if key == "game" and any(g in prompt_l for g in ["chess", "tic-tac-toe", "sudoku", "snake"]):
                    continue
                if key == "find_max" and any(x in prompt_l for x in ["list", "dict", "array", "matrix"]):
                    continue
                if key == "prime" and any(x.isdigit() for x in prompt_l):
                    continue
                if key == "fibonacci" and any(x.isdigit() for x in prompt_l):
                    continue
                if key == "factorial" and any(x.isdigit() for x in prompt_l):
                    continue
                if key == "gcd" and len(re.findall(r"\d+", prompt_l)) >= 2:
                    continue
                if key == "lcm" and len(re.findall(r"\d+", prompt_l)) >= 2:
                    continue
                if key == "power" and "of" in prompt_l or "^" in prompt_l:
                    continue
                if key == "extract_numbers" and re.search(r"\d+", prompt_l):
                    continue
                if key == "email" and re.search(r"[^@\s]+@[^@\s]+\.[^@\s]+", prompt_l):
                    continue
                if key == "phone" and re.search(r"\d{3}[-\s]?\d{3}[-\s]?\d{4}", prompt_l):
                    continue
                if key == "hashtag" and "#" in prompt_l:
                    continue
                if key == "time" and any(x in prompt_l for x in ["yyyy", "hh", "mm", "format"]):
                    continue
                if key == "list_files" and any(x in prompt_l for x in ["current", "directory", ".", "folder"]):
                    continue
                if key == "env" and any(x in prompt_l for x in ["path", "home", "pythonpath"]):
                    continue
                if key == "sleep" and re.search(r"\d+", prompt_l):
                    continue
                if key == "directory" and any(x in prompt_l for x in ["current", "working", "cwd"]):
                    continue

                questions.append(question)

        return questions

    def run(self, prompt: str) -> dict:
        if not isinstance(prompt, str):
            raise TypeError("Prompt must be a string")

        clarifications = self.detect_ambiguities(prompt)
        status = "ambiguous" if clarifications else "clear"

        return {
            "original_prompt": prompt,
            "clarifications": clarifications,
            "status": status
        }
