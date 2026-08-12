"""
Shared utilities used by both the MCP server and the agent layer -
kept in a common module so both sides can import them independently,
without one depending on the other's internal files (important once
they run as separate Docker containers).
"""

import json
import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

anthropic_client = anthropic.Anthropic()


def parse_json_response(raw_text: str) -> dict:
    """
    Parse a JSON object from an LLM response, tolerating the common case
    where the model wraps it in markdown code fences despite instructions
    not to.
    """
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        cleaned = cleaned.rsplit("```", 1)[0]
    return json.loads(cleaned.strip())