"""
Wrapper for LLM calls with standardized parsing and error handling.
"""

import json
import logging
from db.supabase_client import llm, llm_fast

logger = logging.getLogger("course_architect.llm_service")

def parse_json_from_llm(content: str) -> dict:
    """Safely parse a JSON block out of an LLM response."""
    cleaned = content.strip()
    if "```json" in cleaned:
        try:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        except IndexError:
            pass
    elif "```" in cleaned:
        try:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        except IndexError:
            pass
            
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM: {cleaned}\nError: {e}")
        return {}

def invoke_llm_json(prompt: str, fast: bool = False) -> dict:
    """Invoke the LLM and return parsed JSON."""
    model = llm_fast if fast else llm
    res = model.invoke(prompt)
    return parse_json_from_llm(res.content)

def invoke_llm_text(prompt: str, fast: bool = False) -> str:
    """Invoke the LLM and return raw text."""
    model = llm_fast if fast else llm
    res = model.invoke(prompt)
    return res.content.strip()
