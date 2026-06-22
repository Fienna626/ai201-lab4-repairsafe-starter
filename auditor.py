import json
import os
from datetime import datetime, timezone
from config import LOG_FILE, LLM_MODEL


def log_interaction(question: str, tier: str, response: str) -> None:
    """
    Append a structured record of this interaction to the audit log.

    TODO — Milestone 3:

    Before writing any code, complete specs/auditor-spec.md. The key decisions
    are what fields to log, how much of the question and response to include,
    and how to handle the logs/ directory not existing yet.

    Each record should be a JSON object written as a single line to LOG_FILE
    (defined in config.py as "logs/audit.jsonl").

    Required fields:
      - "timestamp"        : ISO 8601 datetime string
      - "tier"             : the safety tier assigned to this question
      - "question"         : the user's question (truncate to 300 chars if longer)
      - "response_preview" : first 200 characters of the response

    If the logs/ directory doesn't exist, create it before writing.

    Also print a one-line summary to the terminal so you can see logged
    interactions in real time without opening the file:
      e.g. [LOGGED] tier=caution | "How do I replace a faucet?" → 47 chars

    Design your log entry in specs/auditor-spec.md before implementing here.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)
    
    # Truncate question and response
    question_truncated = question[:300]
    response_preview = response[:200]
    question_length = len(question)
    response_length = len(response)
    
    # Create log entry with ISO 8601 timestamp
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "tier": tier,
        "question": question_truncated,
        "response_preview": response_preview,
        "question_length": question_length,
        "model": LLM_MODEL,
    }
    
    # Append to JSONL file (one JSON object per line, no pretty-printing)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    # Print one-line terminal summary
    print(f"[AUDIT] tier={tier} | q_len={question_length} | response_len={response_length} | logged to {LOG_FILE}")
