import json
import logging
from typing import Dict, Any
from fastapi import HTTPException

from domains.base import BaseDomain
from prompts import (
    ARCHETYPE_RULES,
    get_base_persona,
    get_archetype_rules,
    DAY_ONE_OPENER_PROMPT,
    ITERATION_SCRIPT_PROMPT,
    LIVE_COPILOT_PROMPT,
    GENERAL_SYNTHESIS_PROMPT,
    TUTOR_SYNTHESIS_PROMPT,
    HOMEWORK_GENERATOR_PROMPT,
    FLYWHEEL_BRIDGE_PROMPT,
    ARCHETYPE_CLASSIFIER_PROMPT
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
        
        # 1. Zero-Click Auto-Calibration: Determine Archetype
        arch_res = self.llm.invoke(ARCHETYPE_CLASSIFIER_PROMPT.format(
            domain=expert.get('domain', ''),
            title=expert.get('current_title', ''),
            short_bio=expert.get('short_bio', '')
        ))
        cleaned_arch = arch_res.content.strip()
        if "```json" in cleaned_arch:
            cleaned_arch = cleaned_arch.split("```json")[1].split("```")[0].strip()
        
        try:
            arch_data = json.loads(cleaned_arch)
            archetype = arch_data.get('archetype', 'the_tactician')
        except Exception:
            archetype = 'the_tactician'
            
        # Update the database with the chosen archetype
        self.supabase.table("experts").update({"archetype": archetype}).eq("id", expert_id).execute()
        
        # Fire Day 1 Opener prompt with full expert profile
        res = self.llm.invoke(DAY_ONE_OPENER_PROMPT.format(
            expert_name=expert.get('name', ''),
            expert_title=expert.get('current_title', ''),
            expert_domain=expert.get('domain', ''),
            years_of_experience=expert.get('years_of_experience', 'Unknown'),
            short_bio=expert.get('short_bio', ''),
            target_audience=expert.get('target_audience', ''),
            stream_type=expert.get('stream_type', 'general'),
            archetype_rules=get_archetype_rules(archetype)
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
        
        archetype = expert.get('archetype', 'balanced')
        res = self.llm.invoke(ITERATION_SCRIPT_PROMPT.format(
            expert_name=expert.get('name', ''),
            expert_title=expert.get('current_title', ''),
            expert_domain=expert.get('domain', ''),
            years_of_experience=expert.get('years_of_experience', 'Unknown'),
            short_bio=expert.get('short_bio', ''),
            stream_type=expert.get('stream_type', 'general'),
            iteration_number=iteration_number,
            archetype_rules=get_archetype_rules(archetype),
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
        archetype = expert.get('archetype', 'balanced')
        
        # Append answer to transcript
        current_transcript = session.get("raw_transcript", "")
        new_transcript = current_transcript + f"\n\n[EXPERT]: {expert_answer}"
        
        # 2. Get active script question and context from frontend
        current_script_question = (request_data or {}).get("current_script_question", "")
        if not current_script_question:
            current_script_question = "General domain exploration."
            
        active_block = (request_data or {}).get("active_block", "Block 1: Personal Origin & Persona")
        tangent_count = int((request_data or {}).get("tangent_count", 0))
        
        # Dynamic tangent limits based on the block
        # Block 4 is the massive drill-down for course extraction, so it gets a much higher limit.
        tangent_limit = 6 if "Block 4" in active_block else 2
        
        pacing_warning = ""
        if tangent_count >= tangent_limit:
            pacing_warning = f"WARNING: You have exhausted the tangent limit ({tangent_limit}) for this specific topic. You MUST wrap up and return intent='skip' to advance the interview."
        
        # 3. Build conversation history sliding window (last 3 turns)
        conversation_history = self._build_conversation_history(current_transcript, max_turns=3)
            
        # 4. Single-pass: Intent Classification + Follow-up Generation
        copilot_res = self.llm.invoke(LIVE_COPILOT_PROMPT.format(
            active_block=active_block,
            active_script_question=current_script_question,
            conversation_history=conversation_history,
            expert_answer=expert_answer,
            archetype_rules=get_archetype_rules(archetype),
            pacing_warning=pacing_warning
        ))
        
        copilot_data = {"intent": "substantive", "follow_up": None}
        try:
            cl = copilot_res.content.strip()
            if "```json" in cl: cl = cl.split("```json")[1].split("```")[0].strip()
            copilot_data = json.loads(cl)
        except Exception:
            logger.warning("Failed to parse copilot response, defaulting to substantive.")
            
        action = "follow_tangent"
        next_question = copilot_data.get("follow_up")
        
        if copilot_data.get("intent") == "skip" or not next_question:
            action = "next_script_question"
            next_question = None  # Frontend advances teleprompter
        elif copilot_data.get("intent") == "off_topic":
            action = "redirect_to_script"
            
        # Append AI question to transcript (if we generated one)
        if next_question:
            new_transcript += f"\n\n[AI JOURNALIST]: {next_question}"
        self.supabase.table("interview_sessions").update({"raw_transcript": new_transcript}).eq("id", session_id).execute()
        
        return {
            "question": next_question,
            "decision": {
                "action": action, 
                "intent": copilot_data.get("intent"),
                "reasoning": copilot_data.get("internal_reasoning", "")
            }
        }

    def _build_conversation_history(self, transcript: str, max_turns: int = 3) -> str:
        """Build a sliding window of the last N HOST+EXPERT turn pairs."""
        if not transcript:
            return "(No conversation history yet)"
        
        lines = transcript.strip().split("\n")
        turns = []
        current_turn = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("[EXPERT]:") or line.startswith("[AI JOURNALIST]:"):
                if current_turn:
                    turns.append("\n".join(current_turn))
                current_turn = [line]
            else:
                current_turn.append(line)
        
        if current_turn:
            turns.append("\n".join(current_turn))
        
        # Take the last N turns
        recent = turns[-max_turns:] if len(turns) > max_turns else turns
        return "\n\n".join(recent) if recent else "(No conversation history yet)"

    async def synthesize(self, session_id: str) -> Dict[str, Any]:
        session_res = self.supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Session not found.")
        session = session_res.data[0]
        
        expert = await self._get_expert(session["expert_id"])
        iteration_number = session.get("iteration_number", 1)
        
        transcript = session.get("raw_transcript", "")
        
        # 1. General Synthesis (Applies to ALL streams) — with expert context
        gen_res = self.llm.invoke(GENERAL_SYNTHESIS_PROMPT.format(
            expert_name=expert.get('name', ''),
            expert_domain=expert.get('domain', ''),
            iteration_number=iteration_number,
            transcript=transcript
        ))
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
            tut_res = self.llm.invoke(TUTOR_SYNTHESIS_PROMPT.format(
                expert_name=expert.get('name', ''),
                expert_domain=expert.get('domain', ''),
                iteration_number=iteration_number,
                transcript=transcript
            ))
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
        
        expert = await self._get_expert(session["expert_id"])
        iteration_number = session.get("iteration_number", 1)
        
        transcript = session.get("raw_transcript", "")
        # Read the newly synthesized data
        session_synthesis_str = json.dumps(session.get("session_synthesis", {}), indent=2)
        
        res = self.llm.invoke(HOMEWORK_GENERATOR_PROMPT.format(
            expert_name=expert.get('name', ''),
            expert_domain=expert.get('domain', ''),
            iteration_number=iteration_number,
            transcript=transcript,
            extracted_session_data=session_synthesis_str
        ))
        cl = res.content.strip()
        if "```json" in cl: cl = cl.split("```json")[1].split("```")[0].strip()
        hw_data = json.loads(cl)
        
        self.supabase.table("homework_ledger").insert({
            "expert_id": session["expert_id"],
            "session_id": session_id,
            "iteration_number": iteration_number,
            "ai_open_loops": hw_data.get("ai_open_loops", [])
        }).execute()
        
        return {"status": "success", "homework": hw_data}

    async def flywheel_bridge(self, expert_id: str) -> Dict[str, Any]:
        expert = await self._get_expert(expert_id)
        archetype = expert.get('archetype', 'balanced')
        
        # Fetch latest homework
        hw_res = self.supabase.table("homework_ledger").select("*").eq("expert_id", expert_id).order("created_at", desc=True).limit(1).execute()
        if not hw_res.data:
            return {"bridge_opener": "Welcome back! What should we dive into today?", "internal_reasoning": "No homework ledger found."}
            
        hw = hw_res.data[0]
        previous_day = hw.get("iteration_number", 1)
        current_day = previous_day + 1
        
        res = self.llm.invoke(FLYWHEEL_BRIDGE_PROMPT.format(
            expert_name=expert.get('name', ''),
            expert_domain=expert.get('domain', ''),
            previous_day=previous_day,
            current_day=current_day,
            archetype_rules=get_archetype_rules(archetype),
            ai_open_loops=json.dumps(hw.get("ai_open_loops", []), indent=2),
            human_manual_notes=hw.get("human_manual_notes", "")
        ))
        cl = res.content.strip()
        if "```json" in cl: cl = cl.split("```json")[1].split("```")[0].strip()
        bridge_data = json.loads(cl)
        
        return bridge_data
