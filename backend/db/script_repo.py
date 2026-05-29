"""
Repository functions for managing the interview script state.
"""

import logging
from .supabase_client import supabase

logger = logging.getLogger("course_architect.script_repo")

def get_script_for_session(session_id: str, user_id: str):
    script_res = supabase.table("interview_scripts").select("*").eq("session_id", session_id).eq("user_id", user_id).execute()
    if script_res.data:
        return script_res.data[0]
    return None

def save_new_script(session_id: str, user_id: str, script_obj: dict, themes_obj: list):
    """Insert a new script into the database."""
    total_q = (
        len(script_obj.get("interview_arc", {}).get("phase_1_genesis_audience", {}).get("questions", [])) +
        len(script_obj.get("interview_arc", {}).get("phase_2_module_breakdown", {}).get("questions", [])) +
        len(script_obj.get("interview_arc", {}).get("phase_3_deep_dives", {}).get("questions", []))
    )
    
    supabase.table("interview_scripts").insert({
        "session_id": session_id,
        "user_id": user_id,
        "full_script": script_obj,
        "themes": themes_obj,
        "questions_completed": 0,
        "total_questions": total_q,
        "status": "active",
        "current_followup_count": 0
    }).execute()
    return total_q

def update_script_progress(session_id: str, user_id: str, completed_count: int, followup_count: int = 0):
    """Update the progress counts on the script."""
    supabase.table("interview_scripts").update({
        "questions_completed": completed_count,
        "current_followup_count": followup_count
    }).eq("session_id", session_id).eq("user_id", user_id).execute()

def mark_script_completed(session_id: str, user_id: str, status: str = "completed"):
    supabase.table("interview_scripts").update({
        "status": status
    }).eq("session_id", session_id).eq("user_id", user_id).execute()
