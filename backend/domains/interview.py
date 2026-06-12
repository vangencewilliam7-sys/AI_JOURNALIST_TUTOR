import json
import logging
from typing import Dict, Any
from fastapi import HTTPException

from domains.base import BaseDomain
from prompts import (
    ARCHETYPE_RULES,
    get_base_persona,
    DAY_ONE_OPENER_PROMPT,
    ITERATION_SCRIPT_PROMPT,
    INTENT_CLASSIFIER_PROMPT,
    LIVE_FOLLOWUP_PROMPT,
    GENERAL_SYNTHESIS_PROMPT,
    TUTOR_SYNTHESIS_PROMPT,
    HOMEWORK_GENERATOR_PROMPT,
    FLYWHEEL_BRIDGE_PROMPT
)

logger = logging.getLogger(__name__)

class InterviewDomain(BaseDomain):
    def __init__(self, llm, supabase):
        self.llm = llm
        self.supabase = supabase

    async def _get_expert(self, expert_id: str) -> Dict[str, Any]:
        res = self.supabase.table("experts").select("*").eq("id", expert_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Expert not found.")
        return res.data[0]

    async def intake(self, expert_id: str) -> Dict[str, Any]:
        expert = await self._get_expert(expert_id)
        
        # Fire Day 1 Opener prompt
        res = self.llm.invoke(DAY_ONE_OPENER_PROMPT.format(
            expert_name=expert['name'],
            expert_domain=expert['domain'],
            stream_type=expert['stream_type']
        ))
        
        cleaned = res.content.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            
        return json.loads(cleaned)

    async def generate_script(self, expert_id: str) -> Dict[str, Any]:
        expert = await self._get_expert(expert_id)
        
        # Fetch current accumulated profile
        profile_res = self.supabase.table("expert_profile").select("*").eq("expert_id", expert_id).execute()
        accumulated_knowledge = profile_res.data[0] if profile_res.data else {}
        
        # Fetch curriculum blueprints if tutor
        if expert['stream_type'] == 'tutor':
            cb_res = self.supabase.table("curriculum_blueprints").select("course_modules").eq("expert_id", expert_id).execute()
            if cb_res.data:
                accumulated_knowledge['course_modules'] = cb_res.data[0].get('course_modules', [])
                
        # Determine iteration number. Check latest session.
        sessions_res = self.supabase.table("interview_sessions").select("iteration_number").eq("expert_id", expert_id).order("iteration_number", desc=True).limit(1).execute()
        iteration_number = 1
        if sessions_res.data:
            # We are generating a script for the *current* or *new* session. 
            # If the session is already active, we use its iteration number.
            # Usually, /generate-script is called for the active session.
            iteration_number = sessions_res.data[0]['iteration_number']

        # Fetch open loops from homework ledger for this expert (latest pending)
        hw_res = self.supabase.table("homework_ledger").select("*").eq("expert_id", expert_id).order("created_at", desc=True).limit(1).execute()
        homework_gaps = hw_res.data[0] if hw_res.data else {}

        accumulated_knowledge_str = json.dumps(accumulated_knowledge, indent=2)
        homework_gaps_str = json.dumps(homework_gaps, indent=2)
        
        res = self.llm.invoke(ITERATION_SCRIPT_PROMPT.format(
            expert_name=expert['name'],
            expert_domain=expert['domain'],
            stream_type=expert['stream_type'],
            iteration_number=iteration_number,
            accumulated_knowledge_section=accumulated_knowledge_str,
            homework_gaps_section=homework_gaps_str
        ))
        
        cleaned = res.content.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            
        script_data = json.loads(cleaned)
        
        # Save script to the active session
        session_res = self.supabase.table("interview_sessions").select("id").eq("expert_id", expert_id).eq("status", "active").execute()
        if session_res.data:
            session_id = session_res.data[0]["id"]
            self.supabase.table("interview_sessions").update({"script": script_data}).eq("id", session_id).execute()
            
        return script_data

    async def live_turn(self, session_id: str, expert_answer: str, request_data: Dict[str, Any] = None) -> Dict[str, Any]:
        # 1. Fetch session and expert info
        session_res = self.supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Active session not found.")
        session = session_res.data[0]
        
        expert = await self._get_expert(session["expert_id"])
        topic = expert["domain"]
        stream_type = expert["stream_type"]
        
        # Append answer to transcript
        current_transcript = session.get("raw_transcript", "")
        new_transcript = current_transcript + f"\\n\\n[EXPERT]: {expert_answer}"
        
        persona_prompt = get_base_persona(topic, stream_type)
        
        # 2. Get active script question. We assume the frontend passes `current_script_question`
        current_script_question = request_data.get("current_script_question", "")
        if not current_script_question:
            # Fallback if frontend didn't pass it, just use generic context
            current_script_question = "General domain exploration."
            
        # 3. Intent Classification
        intent_res = self.llm.invoke(INTENT_CLASSIFIER_PROMPT.format(
            current_question=current_script_question,
            expert_answer=expert_answer
        ))
        
        intent_data = {"intent": "substantive"}
        try:
            cl = intent_res.content.strip()
            if "```json" in cl: cl = cl.split("```json")[1].split("```")[0].strip()
            intent_data = json.loads(cl)
        except Exception:
            pass
            
        action = "follow_tangent"
        if intent_data.get("intent") == "skip" or intent_data.get("intent") == "resolved":
            action = "next_script_question"
            
        # 4. Generate follow-up
        if action == "next_script_question":
            # Let the frontend load the next question from the script. We just acknowledge.
            next_question = "Got it. Let's move on to the next topic."
        else:
            # Generate a deep-dive follow-up
            scenario = f"ACTION: follow_tangent\\nTARGET INSTRUCTION: Ask a probing conversational follow-up to dig deeper into their last answer."
            gen_res = self.llm.invoke(LIVE_FOLLOWUP_PROMPT.format(
                persona=persona_prompt,
                scenario_instruction=scenario,
                expert_answer=expert_answer
            ))
            next_question = gen_res.content.strip()
            
        # Append AI question to transcript
        new_transcript += f"\\n\\n[AI JOURNALIST]: {next_question}"
        self.supabase.table("interview_sessions").update({"raw_transcript": new_transcript}).eq("id", session_id).execute()
        
        return {
            "question": next_question,
            "decision": {"action": action, "intent": intent_data.get("intent")}
        }

    async def synthesize(self, session_id: str) -> Dict[str, Any]:
        session_res = self.supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Session not found.")
        session = session_res.data[0]
        
        expert = await self._get_expert(session["expert_id"])
        
        transcript = session.get("raw_transcript", "")
        
        # 1. General Synthesis (Applies to ALL streams)
        gen_res = self.llm.invoke(GENERAL_SYNTHESIS_PROMPT.format(transcript=transcript))
        cl_gen = gen_res.content.strip()
        if "```json" in cl_gen: cl_gen = cl_gen.split("```json")[1].split("```")[0].strip()
        general_data = json.loads(cl_gen)
        
        # Fetch existing profile
        ep_res = self.supabase.table("expert_profile").select("*").eq("expert_id", expert["id"]).execute()
        if not ep_res.data:
            # Create if doesn't exist
            self.supabase.table("expert_profile").insert({"expert_id": expert["id"]}).execute()
            ep_res = self.supabase.table("expert_profile").select("*").eq("expert_id", expert["id"]).execute()
            
        ep = ep_res.data[0]
        
        # APPEND to JSONB arrays in python before updating (or could use Postgres RPC, but doing it in python is easier here)
        new_persona_traits = ep.get("persona_traits", []) + general_data.get("persona_traits", [])
        new_war_stories = ep.get("war_stories", []) + general_data.get("war_stories", [])
        new_mental_models = ep.get("mental_models", []) + general_data.get("mental_models", [])
        new_edge_cases = ep.get("edge_cases", []) + general_data.get("edge_cases", [])
        new_pattern_breaks = ep.get("pattern_breaks", []) + general_data.get("pattern_breaks", [])
        new_tacit_insights = ep.get("tacit_insights", []) + general_data.get("tacit_insights", [])
        
        update_ep = {
            "persona_traits": new_persona_traits,
            "war_stories": new_war_stories,
            "mental_models": new_mental_models,
            "edge_cases": new_edge_cases,
            "pattern_breaks": new_pattern_breaks,
            "tacit_insights": new_tacit_insights
        }
        
        # 2. Tutor Synthesis (If stream_type == 'tutor')
        tutor_data = {}
        if expert["stream_type"] == "tutor":
            tut_res = self.llm.invoke(TUTOR_SYNTHESIS_PROMPT.format(transcript=transcript))
            cl_tut = tut_res.content.strip()
            if "```json" in cl_tut: cl_tut = cl_tut.split("```json")[1].split("```")[0].strip()
            tutor_data = json.loads(cl_tut)
            
            # Extract persona specifics
            update_ep["teaching_style"] = tutor_data.get("teaching_style", ep.get("teaching_style", ""))
            update_ep["linguistic_fingerprint"] = tutor_data.get("linguistic_fingerprint", ep.get("linguistic_fingerprint", {}))
            update_ep["system_prompt"] = tutor_data.get("system_prompt", ep.get("system_prompt", ""))
            
            # Upsert Curriculum Blueprints
            cb_res = self.supabase.table("curriculum_blueprints").select("*").eq("expert_id", expert["id"]).execute()
            if not cb_res.data:
                self.supabase.table("curriculum_blueprints").insert({
                    "expert_id": expert["id"],
                    "course_modules": tutor_data.get("course_modules", [])
                }).execute()
            else:
                cb = cb_res.data[0]
                # Merge or append course_modules
                existing_modules = cb.get("course_modules", [])
                new_modules = tutor_data.get("course_modules", [])
                # Simple append for now. In a real system, we'd merge by module title.
                combined_modules = existing_modules + new_modules
                self.supabase.table("curriculum_blueprints").update({
                    "course_modules": combined_modules,
                    "iteration_last_updated": session["iteration_number"]
                }).eq("id", cb["id"]).execute()
        
        # Save updated expert profile
        self.supabase.table("expert_profile").update(update_ep).eq("id", ep["id"]).execute()
        
        # Update session with synthesis result
        session_synthesis = {"general": general_data, "tutor": tutor_data}
        self.supabase.table("interview_sessions").update({
            "status": "synthesized",
            "session_synthesis": session_synthesis
        }).eq("id", session_id).execute()
        
        return {"status": "success", "session_synthesis": session_synthesis}

    async def generate_homework(self, session_id: str) -> Dict[str, Any]:
        session_res = self.supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Session not found.")
        session = session_res.data[0]
        
        transcript = session.get("raw_transcript", "")
        # Read the newly synthesized data
        session_synthesis_str = json.dumps(session.get("session_synthesis", {}), indent=2)
        
        res = self.llm.invoke(HOMEWORK_GENERATOR_PROMPT.format(
            transcript=transcript,
            extracted_session_data=session_synthesis_str
        ))
        cl = res.content.strip()
        if "```json" in cl: cl = cl.split("```json")[1].split("```")[0].strip()
        hw_data = json.loads(cl)
        
        self.supabase.table("homework_ledger").insert({
            "expert_id": session["expert_id"],
            "session_id": session_id,
            "iteration_number": session["iteration_number"],
            "ai_open_loops": hw_data.get("ai_open_loops", []),
            "status": "pending"
        }).execute()
        
        return {"status": "success", "homework": hw_data}

    async def flywheel_bridge(self, expert_id: str) -> Dict[str, Any]:
        # Fetch latest homework
        hw_res = self.supabase.table("homework_ledger").select("*").eq("expert_id", expert_id).order("created_at", desc=True).limit(1).execute()
        if not hw_res.data:
            return {"opener": "Welcome back! What should we dive into today?"}
            
        hw = hw_res.data[0]
        
        res = self.llm.invoke(FLYWHEEL_BRIDGE_PROMPT.format(
            ai_open_loops=json.dumps(hw.get("ai_open_loops", []), indent=2),
            human_manual_notes=hw.get("human_manual_notes", "")
        ))
        cl = res.content.strip()
        if "```json" in cl: cl = cl.split("```json")[1].split("```")[0].strip()
        bridge_data = json.loads(cl)
        
        return bridge_data
