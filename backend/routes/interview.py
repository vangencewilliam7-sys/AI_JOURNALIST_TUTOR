"""
Interview orchestration routes.
"""

import logging
import json
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from models import PrepareRequest, InterviewRequest
from auth import get_current_user
from db.supabase_client import supabase
from db.session_repo import ensure_session, save_message
from db.script_repo import get_script_for_session, save_new_script
from services.rag_service import research_scan
from services.llm_service import invoke_llm_json
from services.interview_engine import process_interview_turn
from prompts import THEME_EXTRACTION_PROMPT, SCRIPT_CRAFTING_PROMPT, FINAL_STRUCTURING_PROMPT, SAMPLE_QUESTIONNAIRE_GUIDELINE

logger = logging.getLogger("course_architect.routes.interview")
router = APIRouter()

@router.post("/prepare-interview")
async def prepare_interview(request: PrepareRequest, user_id: str = Depends(get_current_user)):
    try:
        session_id = request.user_session_id
        db_uuid = ensure_session(session_id, request.topic or "Course Planning", user_id)
        if not db_uuid:
            raise HTTPException(status_code=500, detail="Failed to initialize session in DB")
            
        research_briefing = research_scan(request.topic, user_id)
        
        # 1. Theme Extraction
        theme_res = invoke_llm_json(THEME_EXTRACTION_PROMPT.format(
            course_title=request.course_title,
            target_audience=request.target_audience,
            north_star_outcome=request.north_star_outcome,
            research_briefing=research_briefing
        ))
        
        if not isinstance(theme_res, list):
            theme_res = []
            
        # 2. Script Crafting
        script_res = invoke_llm_json(SCRIPT_CRAFTING_PROMPT.format(
            course_title=request.course_title,
            tutor_name=request.tutor_name,
            tutor_role=request.tutor_role,
            tutor_experience=request.tutor_experience,
            target_audience=request.target_audience,
            prerequisites=request.prerequisites,
            completion_time=request.completion_time,
            north_star_outcome=request.north_star_outcome,
            themes=json.dumps(theme_res, indent=2),
            research_briefing=research_briefing,
            sample_questionnaire=SAMPLE_QUESTIONNAIRE_GUIDELINE
        ))
        
        # Attach metadata
        script_res["metadata"] = request.model_dump()
        
        total_q = save_new_script(session_id, user_id, script_res, theme_res)
        
        first_q = script_res.get("interview_arc", {}).get("phase_1_genesis_audience", {}).get("questions", [{}])[0].get("question_text", "Let's start! Tell me about the course.")
        
        save_message(db_uuid, "ai", first_q, "system", {"action": "started_interview"})
        
        return {
            "status": "ready",
            "session_id": session_id,
            "total_questions": total_q,
            "first_question": first_q,
            "themes": theme_res,
            "script": script_res
        }
    except Exception as e:
        logger.error(f"Prepare interview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-question")
async def generate_question(request: InterviewRequest, user_id: str = Depends(get_current_user)):
    try:
        session_id = request.user_session_id
        db_uuid = ensure_session(session_id, request.topic or "Course Planning", user_id)
        
        save_message(db_uuid, "expert", request.expert_answer, request.input_source)
        
        script_record = get_script_for_session(session_id, user_id)
        if not script_record:
            raise HTTPException(status_code=400, detail="No active interview script found for this session.")
            
        if script_record.get("status") == "completed":
            return {"question": "We are already done! Check out your course blueprint.", "script_progress": "Complete", "decision": {}}
            
        return process_interview_turn(request.expert_answer, user_id, session_id, db_uuid, script_record)
        
    except Exception as e:
        logger.error(f"Generate question error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/end-interview/{session_id}")
async def end_interview(session_id: str, user_id: str = Depends(get_current_user)):
    try:
        script_record = get_script_for_session(session_id, user_id)
        if not script_record:
            raise HTTPException(status_code=404, detail="No interview script found")
            
        completed = script_record.get("questions_completed", 0)
        total = script_record.get("total_questions", 0)
        
        supabase.table("interview_scripts").update({"status": "ended_early"}).eq("session_id", session_id).eq("user_id", user_id).execute()
        
        session_res = supabase.table("conversation_sessions").select("id").eq("session_id", session_id).eq("user_id", user_id).execute()
        if session_res.data:
            supabase.table("conversation_sessions").update({"status": "completed"}).eq("id", session_res.data[0]["id"]).execute()
            
        # Trigger synthesis logic internally (not an HTTP call)
        # Using a helper func here or just redirect to synthesize route internally
        from .synthesis import run_synthesis
        report = await run_synthesis(session_id, user_id)
        
        return {
            "status": "success",
            "message": f"Interview ended at question {completed}/{total}. Knowledge synthesized.",
            "report": report
        }
    except Exception as e:
        logger.error(f"End interview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
