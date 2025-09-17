import os
import json
from datetime import datetime


class Logger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    def log(self, filename: str, data: dict):
        """Append a JSON object to a .jsonl file with timestamp."""
        data["timestamp"] = datetime.utcnow().isoformat()
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
