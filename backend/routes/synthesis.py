"""
Synthesis route logic.
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from db.supabase_client import supabase
from services.llm_service import invoke_llm_json
from prompts import FINAL_STRUCTURING_PROMPT

logger = logging.getLogger("course_architect.routes.synthesis")
router = APIRouter()

async def run_synthesis(session_id: str, user_id: str) -> dict:
    session_res = supabase.table("conversation_sessions").select("id").eq("session_id", session_id).eq("user_id", user_id).execute()
    if not session_res.data:
        raise HTTPException(status_code=404, detail="Session not found")
    db_uuid = session_res.data[0]["id"]
    
    messages_res = supabase.table("conversation_messages").select("role, content, message_index").eq("session_id", db_uuid).order("message_index").execute()
    messages = messages_res.data or []
    if len(messages) < 2:
        raise HTTPException(status_code=400, detail="Not enough interview data to synthesize.")
        
    transcript_lines = []
    for msg in messages:
        role_label = "AI STUDENT ARCHITECT" if msg["role"] == "ai" else "EXPERT"
        transcript_lines.append(f"[{role_label}]: {msg['content']}")
    transcript_text = "\n\n".join(transcript_lines)
    
    script_res = supabase.table("interview_scripts").select("themes, questions_completed, total_questions, full_script").eq("session_id", session_id).eq("user_id", user_id).execute()
    
    questions_completed = 0
    total_questions = 0
    metadata = {}
    if script_res.data:
        questions_completed = script_res.data[0].get("questions_completed", 0)
        total_questions = script_res.data[0].get("total_questions", 0)
        metadata = script_res.data[0].get("full_script", {}).get("metadata", {})
        
    course_title = metadata.get("course_title", "Domain Course")
    tutor_name = metadata.get("tutor_name", "Expert")
    
    report_data = invoke_llm_json(FINAL_STRUCTURING_PROMPT.format(
        course_title=course_title,
        tutor_name=tutor_name,
        tutor_role=metadata.get("tutor_role", ""),
        tutor_experience=metadata.get("tutor_experience", ""),
        target_audience=metadata.get("target_audience", ""),
        north_star_outcome=metadata.get("north_star_outcome", ""),
        completion_time=metadata.get("completion_time", ""),
        prerequisites=metadata.get("prerequisites", ""),
        transcript=transcript_text
    ))
    
    # Store in DB
    supabase.table("course_blueprints").delete().eq("session_id", session_id).execute()
    supabase.table("course_blueprints").insert({
        "session_id": session_id,
        "user_id": user_id,
        "course_title": report_data.get("course_title", course_title),
        "target_audience": report_data.get("target_audience", metadata.get("target_audience")),
        "total_modules": report_data.get("total_modules", 0),
        "summary": report_data.get("summary", ""),
        "course_modules": report_data.get("course_modules", []),
        "marketing_hooks": report_data.get("marketing_hooks", []),
        "messages_analyzed": len(messages),
        "questions_completed": questions_completed,
        "total_questions": total_questions,
        "tutor_name": report_data.get("tutor_name", tutor_name),
        "tutor_motivation": report_data.get("tutor_motivation", ""),
        "north_star_outcome": report_data.get("north_star_outcome", metadata.get("north_star_outcome")),
        "learning_format": report_data.get("learning_format", ""),
        "friction_points": report_data.get("friction_points", []),
        "teaching_frameworks": report_data.get("teaching_frameworks", []),
        "edge_cases": report_data.get("edge_cases", []),
        "evaluation_methods": report_data.get("evaluation_methods", []),
        "anti_patterns": report_data.get("anti_patterns", []),
        "learning_outcomes": report_data.get("learning_outcomes", [])
    }).execute()
    
    supabase.table("interview_scripts").update({"status": "completed"}).eq("session_id", session_id).eq("user_id", user_id).execute()
    
    return report_data

@router.post("/synthesize-knowledge/{session_id}")
async def synthesize_knowledge_endpoint(session_id: str, user_id: str = Depends(get_current_user)):
    try:
        report = await run_synthesis(session_id, user_id)
        return {
            "status": "success",
            "report": report
        }
    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-report/{session_id}")
async def get_knowledge_report(session_id: str, user_id: str = Depends(get_current_user)):
    try:
        report_res = supabase.table("course_blueprints").select("*").eq("session_id", session_id).eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
        if not report_res.data:
            return {"status": "not_synthesized"}
        return {
            "status": "success",
            "report": report_res.data[0]
        }
    except Exception as e:
        logger.error(f"Get report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
