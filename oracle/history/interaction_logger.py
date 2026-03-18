import json
import os
from datetime import datetime
from typing import Optional
from oracle.models.data_models import InteractionLog

class InteractionLogger:
    def __init__(self, log_path: str = os.path.expanduser("~/.oracle-ai/oracle_history.jsonl")):
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

    def get_history(self, from_dt: Optional[datetime] = None, to_dt: Optional[datetime] = None, thread_id: Optional[str] = None) -> list[InteractionLog]:
        """
        Reads and filters interaction log entries from the JSONL file.
        """
        history = []
        if not os.path.exists(self.log_path):
            return history

        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        entry = InteractionLog.model_validate_json(line)
                        
                        # Apply filters
                        if from_dt and entry.timestamp < from_dt:
                            continue
                        if to_dt and entry.timestamp > to_dt:
                            continue
                        if thread_id and entry.thread_id != thread_id:
                            continue
                            
                        history.append(entry)
                    except Exception as e:
                        print(f"Warning: Failed to parse history entry: {e}")
        except Exception as e:
            print(f"Warning: Failed to read interaction log: {e}")
            
        return history
