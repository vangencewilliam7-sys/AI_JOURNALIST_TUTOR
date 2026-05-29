"""
Core orchestration logic for the interview loop.
Handles script traversal, follow-ups, and answer evaluation.
"""

import logging
from config import MAX_FOLLOWUPS_PER_QUESTION
from prompts import (
    COURSE_ARCHITECT_PERSONA,
    INTENT_CLASSIFIER_PROMPT,
    ANSWER_COMPLETENESS_PROMPT,
    FOLLOW_UP_PROMPT,
    GENERATION_PHASE_PROMPT
)
from db.session_repo import save_message
from db.script_repo import update_script_progress, mark_script_completed
from services.rag_service import hybrid_rag_fetch
from services.llm_service import invoke_llm_json, invoke_llm_text

logger = logging.getLogger("course_architect.interview_engine")

def get_current_question_from_script(script_obj: dict, completed: int):
    """Find the specific scripted question based on how many are completed."""
    arc = script_obj.get("interview_arc", {})
    all_qs = []
    all_qs.extend(arc.get("phase_1_genesis_audience", {}).get("questions", []))
    all_qs.extend(arc.get("phase_2_module_breakdown", {}).get("questions", []))
    all_qs.extend(arc.get("phase_3_deep_dives", {}).get("questions", []))
    
    if completed < len(all_qs):
        return all_qs[completed]
    return None

def build_persona(script_metadata: dict) -> str:
    return COURSE_ARCHITECT_PERSONA.format(
        course_title=script_metadata.get("course_title", "Unknown"),
        tutor_name=script_metadata.get("tutor_name", "Tutor"),
        tutor_role=script_metadata.get("tutor_role", ""),
        tutor_experience=script_metadata.get("tutor_experience", ""),
        target_audience=script_metadata.get("target_audience", "Students"),
        north_star_outcome=script_metadata.get("north_star_outcome", "Outcome")
    )

def process_interview_turn(expert_answer: str, user_id: str, session_id: str, db_uuid: str, script_record: dict) -> dict:
    """
    Core loop:
    1. Check intent (skip vs substantive)
    2. Check completeness
    3. Generate follow-up OR advance to next script question
    """
    script_obj = script_record["full_script"]
    completed = script_record.get("questions_completed", 0)
    total_q = script_record.get("total_questions", 0)
    followup_count = script_record.get("current_followup_count", 0)
    metadata = script_obj.get("metadata", {})
    
    tutor_name = metadata.get("tutor_name", "Tutor")
    persona = build_persona(metadata)
    
    current_q_obj = get_current_question_from_script(script_obj, completed)
    if not current_q_obj:
        return _handle_interview_complete(tutor_name, session_id, user_id, db_uuid, completed, total_q)
        
    current_q_text = current_q_obj.get("question_text", "Could you elaborate?")
    
    # 1. Intent Classification
    intent_res = invoke_llm_json(INTENT_CLASSIFIER_PROMPT.format(
        current_question=current_q_text,
        expert_answer=expert_answer
    ), fast=True)
    
    if intent_res.get("intent") == "skip":
        return _advance_to_next_question(
            session_id, user_id, db_uuid, script_obj, completed, total_q, persona
        )
        
    # 2. RAG fetch for grounded context
    rag_data = hybrid_rag_fetch(expert_answer, user_id)
    
    # 3. Completeness Evaluation
    eval_res = invoke_llm_json(ANSWER_COMPLETENESS_PROMPT.format(
        current_script_question=current_q_text,
        expert_answer=expert_answer
    ))
    
    resolved = eval_res.get("scripted_question_resolved", False)
    
    # Auto-advance if we hit the followup limit to prevent infinite loops
    if not resolved and followup_count >= MAX_FOLLOWUPS_PER_QUESTION:
        logger.info(f"Force resolving Q{completed+1} due to MAX_FOLLOWUPS ({MAX_FOLLOWUPS_PER_QUESTION})")
        resolved = True
        
    if resolved:
        return _advance_to_next_question(
            session_id, user_id, db_uuid, script_obj, completed, total_q, persona
        )
    else:
        return _generate_followup(
            session_id, user_id, db_uuid, completed, total_q, followup_count,
            current_q_text, expert_answer, eval_res, rag_data, persona
        )

def _handle_interview_complete(tutor_name, session_id, user_id, db_uuid, completed, total_q):
    end_msg = f"Wow, thank you so much, {tutor_name}! We've gone through all the modules and details. I feel like I have a really clear picture of how to build this course now."
    decision = {"next_action": "interview_complete"}
    save_message(db_uuid, "ai", end_msg, "system", decision)
    mark_script_completed(session_id, user_id)
    return {
        "question": end_msg,
        "script_progress": f"{total_q}/{total_q}",
        "decision": decision
    }

def _advance_to_next_question(session_id, user_id, db_uuid, script_obj, completed, total_q, persona):
    next_completed = completed + 1
    update_script_progress(session_id, user_id, next_completed, followup_count=0)
    
    next_q_obj = get_current_question_from_script(script_obj, next_completed)
    if not next_q_obj:
        return _handle_interview_complete("Tutor", session_id, user_id, db_uuid, next_completed, total_q)
        
    next_q_text = next_q_obj.get("question_text", "What's next?")
    
    # Hardcode transition to prevent drift
    ai_resp = f"Got it. {next_q_text}"
    
    decision = {
        "action": "advanced_script",
        "internal_monologue": "Answer was substantive or user skipped. Moving to next scripted question.",
        "scripted_question_resolved": True
    }
    
    save_message(db_uuid, "ai", ai_resp, "system", decision)
    
    return {
        "question": ai_resp,
        "script_progress": f"{next_completed}/{total_q}",
        "decision": decision
    }

def _generate_followup(session_id, user_id, db_uuid, completed, total_q, followup_count, current_q_text, expert_answer, eval_res, rag_data, persona):
    reason = eval_res.get("follow_up_reason", "needs clarification")
    
    follow_up_q = invoke_llm_text(FOLLOW_UP_PROMPT.format(
        persona=persona,
        current_question=current_q_text,
        expert_answer=expert_answer,
        follow_up_reason=reason
    ))
    
    # Increment followup counter
    update_script_progress(session_id, user_id, completed, followup_count + 1)
    
    decision = {
        "action": "follow_up",
        "internal_monologue": eval_res.get("internal_monologue", "Digging deeper for details."),
        "scripted_question_resolved": False,
        "follow_up_reason": reason
    }
    
    save_message(db_uuid, "ai", follow_up_q, "system", decision)
    
    return {
        "question": follow_up_q,
        "script_progress": f"{completed}/{total_q} (Follow-up {followup_count + 1})",
        "decision": decision,
        "chunks_used": rag_data["chunks_used"]
    }
