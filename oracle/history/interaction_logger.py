import json
import os
from datetime import datetime
from oracle.models.data_models import InteractionLog

class InteractionLogger:
    def __init__(self, log_path: str = "oracle_history.jsonl"):
        self.log_path = log_path

    def log(self, entry: InteractionLog):
        """
        Writes an interaction log entry to a local JSONL file.
        """
        try:
            # Ensure the directory exists
            log_dir = os.path.dirname(os.path.abspath(self.log_path))
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Append the entry to the JSONL file
            # Use model_dump_json from Pydantic for easy serialization
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")
        except Exception as e:
            # Don't let logging failures crash the application, but report them
            print(f"Warning: Failed to write interaction log: {e}")
