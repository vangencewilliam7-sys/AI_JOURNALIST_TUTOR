import json
import re
import logging
from typing import Dict, Any, List, Tuple
from fastapi import HTTPException

from domains.base import BaseDomain
from domains.rules import DRIFT_RULES, TANGENT_BUDGET_RULES
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
    RESOURCE_VALIDATION_PROMPT,
    FLYWHEEL_BRIDGE_PROMPT,
    ARCHETYPE_CLASSIFIER_PROMPT,
    BACKGROUND_EMBED_FILTER_PROMPT,
    RETRIEVAL_GATE_PROMPT,
    SCRATCHPAD_UPDATE_PROMPT,
    OBJECTIVE_SATISFACTION_PROMPT,
    OBJECTIVE_REQUIREMENTS,
    COVERAGE_ENGINE_PROMPT,
    TOPIC_CONTROLLER_PROMPT,
    INSIGHT_DETECTION_PROMPT,
    INSIGHT_PRIORITIZATION_PROMPT,
    KNOWLEDGE_GRAPH_UPDATE_PROMPT,
    COVERAGE_AND_GAP_PROMPT,
    CURRICULUM_EXTRACTOR_PROMPT,
    MASTER_INTERVIEW_ORCHESTRATOR_PROMPT,
    ADAPTIVE_CURIOSITY_PROMPT,
    DRIFT_DETECTOR_PROMPT,
    INSIGHTS_SYNTHESIS_PROMPT,
    COURSE_DISCOVERY_ENGINE_PROMPT,
    COURSE_IDENTITY_SYNTHESIZER_PROMPT,
    COURSE_IDENTITY_FIELD_DETECTOR_PROMPT,
    MODULE_DISCOVERY_ENGINE_PROMPT,
    MODULE_LIST_EXTRACTOR_PROMPT,
    MODULE_SATURATION_CHECK_PROMPT,
    MODULE_ENRICHMENT_ENGINE_PROMPT,
    MODULE_ENRICHMENT_FIELD_DETECTOR_PROMPT,
    MODULE_ENRICHMENT_SYNTHESIZER_PROMPT,
    TOPIC_DISCOVERY_ENGINE_PROMPT,
    TOPIC_LIST_EXTRACTOR_PROMPT,
    TOPIC_COVERAGE_VALIDATOR_PROMPT,
    CURRICULUM_VALIDATION_PROMPT,
    COVERAGE_CONTROLLER_PROMPT,
    MODULE_COVERAGE_CONTROLLER_PROMPT,
    CURRICULUM_CLASSIFICATION_PROMPT,
    MODULE_ENRICHMENT_COVERAGE_CONTROLLER_PROMPT,
    TOPIC_COVERAGE_CONTROLLER_PROMPT,
    TOPIC_INITIALIZATION_PROMPT,
    EXPERT_UNDERSTANDING_PROMPT,
    KNOWLEDGE_COVERAGE_PROMPT,
    TACIT_KNOWLEDGE_EXTRACTION_PROMPT,
    KNOWLEDGE_GAP_MANAGER_PROMPT,
    TOPIC_TRANSITION_PROMPT
)

logger = logging.getLogger(__name__)

class InterviewDomain(BaseDomain):
    def __init__(self, llm, supabase, llm_fast=None, embeddings_model=None):
        self.llm = llm
        self.supabase = supabase
        self.llm_fast = llm_fast or llm
        self.embeddings_model = embeddings_model

    async def _get_expert(self, expert_id: str) -> Dict[str, Any]:
        res = self.supabase.table("experts").select("*").eq("id", expert_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Expert not found.")
        return res.data[0]

    def _parse_json(self, content: str) -> dict:
        if not content:
            return {}
        cl = content.strip()
        if "```json" in cl:
            cl = cl.split("```json")[1].split("```")[0].strip()
        elif "```" in cl:
            cl = cl.split("```")[1].split("```")[0].strip()
        cl = re.sub(r',\s*([}\]])', r'\1', cl)
        # Find start and end of JSON object
        start = cl.find('{')
        end = cl.rfind('}')
        if start != -1 and end != -1:
            cl = cl[start:end+1]
        try:
            return json.loads(cl)
        except Exception:
            # Fallback regex parser for simple key-value booleans or strings
            res = {}
            for m in re.finditer(r'"(\w+)"\s*:\s*(true|false)', cl, re.IGNORECASE):
                res[m.group(1)] = m.group(2).lower() == "true"
            if not res:
                for m in re.finditer(r'"(\w+)"\s*:\s*"([^"]*)"', cl):
                    res[m.group(1)] = m.group(2)
            return res

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
        
        # Save script to the most recent active session
        session_res = self.supabase.table("interview_sessions").select("id").eq("expert_id", expert_id).eq("status", "active").order("created_at", desc=True).limit(1).execute()
        if session_res.data:
            session_id = session_res.data[0]["id"]
            self.supabase.table("interview_sessions").update({"script": script_data}).eq("id", session_id).execute()
            
        return script_data

    # =========================================================================
    # PHASE 1 — COURSE DISCOVERY ENGINE
    # =========================================================================
    # Runs AFTER Modules 1 & 2 (journalistic warm-up), BEFORE Module 3.
    # Discovers: course_context → student_personas → duration_weeks → course_title.
    # Writes results to existing DB columns — zero schema migration required.
    # =========================================================================

    async def course_discovery_turn(
        self,
        session_id: str,
        expert_answer: str
    ) -> Dict[str, Any]:
        """
        Process one turn of the Phase 1 Course Discovery conversation.

        Returns:
          {
            "question":        str   — the next podcast-style question,
            "field_status":    dict  — which of the 4 fields are now confident,
            "phase_complete":  bool  — True when all 4 fields are confident,
            "course_identity": dict  — populated only when phase_complete=True
          }
        """
        # ── 1. Fetch session + expert ──────────────────────────────────────
        session_res = self.supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Session not found.")
        session  = session_res.data[0]
        expert   = await self._get_expert(session["expert_id"])

        # ── 2. Append expert answer to transcript ──────────────────────────
        raw_transcript = session.get("raw_transcript", "").strip()
        raw_transcript += f"\n\n[EXPERT]: {expert_answer}"

        # ── 3. Pull Phase 1 scratchpad state ──────────────────────────────
        scratchpad = session.get("live_scratchpad", {})
        # field_status tracks which of the 4 fields are confident (bool)
        field_status = scratchpad.get("discovery_field_status", {
            "course_context":   False,
            "student_personas": False,
            "duration_weeks":   False,
            "course_title":     False
        })

        conv_history = self._build_conversation_history(raw_transcript, max_turns=6)

        # ── 4. Coverage Controller (Full Transcript Evaluation) ──────────
        try:
            cov_res = await self.llm_fast.ainvoke(
                COVERAGE_CONTROLLER_PROMPT.format(
                    transcript=raw_transcript
                )
            )
            cov_data = self._parse_json(cov_res.content)
            for field in ["course_context", "student_personas", "duration_weeks", "course_title"]:
                field_info = cov_data.get(field, {})
                status = str(field_info.get("status", "")).upper()
                score = float(field_info.get("score", 0.0))
                # Mark True if status is SUFFICIENT/COMPLETE or score >= 0.75
                if status in ["SUFFICIENT", "COMPLETE"] or score >= 0.75:
                    field_status[field] = True
        except Exception as e:
            logger.warning(f"Phase 1 Coverage Controller failed: {e}")

        all_complete = all(field_status.values())

        # ── 5a. COMPLETE: Synthesize all 4 fields and persist ──────────────
        if all_complete:
            course_identity = {}
            try:
                synth_res = await self.llm.ainvoke(
                    COURSE_IDENTITY_SYNTHESIZER_PROMPT.format(
                        expert_name=expert.get("name", ""),
                        expert_domain=expert.get("domain", ""),
                        transcript=raw_transcript
                    )
                )
                course_identity = self._parse_json(synth_res.content)
            except Exception as e:
                logger.warning(f"Phase 1 synthesizer failed: {e}")

            # Persist to existing DB columns — zero new columns needed:
            try:
                expert_update = {}
                if course_identity.get("course_title"):
                    expert_update["course_title"] = course_identity["course_title"]
                if course_identity.get("course_context"):
                    expert_update["course_description"] = course_identity["course_context"]
                if course_identity.get("student_personas"):
                    expert_update["target_audience"] = course_identity["student_personas"]
                if expert_update:
                    self.supabase.table("experts").update(expert_update).eq("id", session["expert_id"]).execute()

                # Merge duration_weeks into session_synthesis
                existing_synthesis = session.get("session_synthesis") or {}
                existing_synthesis["duration_weeks"] = course_identity.get("duration_weeks")
                existing_synthesis["course_identity_complete"] = True

                scratchpad["discovery_field_status"] = field_status
                scratchpad["phase1_complete"] = True

                self.supabase.table("interview_sessions").update({
                    "raw_transcript":   raw_transcript,
                    "live_scratchpad":  scratchpad,
                    "session_synthesis": existing_synthesis
                }).eq("id", session_id).execute()

                logger.info(f"Phase 1 complete for session {session_id}. Persisted course identity.")
            except Exception as e:
                logger.error(f"Phase 1 DB persist failed: {e}")

            return {
                "question":        None,   # Signal to frontend: phase is done
                "field_status":    field_status,
                "phase_complete":  True,
                "course_identity": course_identity
            }

        # ── 5b. IN PROGRESS: Transition & Conversation Diversity Controllers ──
        current_stage = self._get_discovery_stage(field_status)
        stage_names = {1: "course_context", 2: "student_personas", 3: "duration_weeks", 4: "course_title"}
        stage_name = stage_names.get(current_stage, "course_context")

        discovery_state = {
            "fields_confident": {k: v for k, v in field_status.items()},
            "current_stage":    current_stage,
            "still_needed":     [k for k, v in field_status.items() if not v]
        }

        # Dynamic Reflection Style Rotation (Diversity Controller)
        reflection_styles = [
            "Insight reflection: Reflect and highlight the core conceptual insight they just shared in a fresh way.",
            "Mindset reflection: Focus on the learner's struggles, frustrations, or shift in perspective.",
            "Contrast reflection: Contrast their statement with standard courses or superficial code tutorials.",
            "Surprise reflection: Acknowledge a unique, specific, or unexpected point they raised.",
            "Connection reflection: Connect their answer to their previous statement about feature developers vs system engineers."
        ]
        turn_count = len([l for l in raw_transcript.split("\n") if l.startswith("[EXPERT]:")])
        selected_style = reflection_styles[turn_count % len(reflection_styles)]

        next_question = "Can you tell me more about the transformation you want your learners to experience?"
        try:
            prompt_content = COURSE_DISCOVERY_ENGINE_PROMPT.format(
                expert_name=expert.get("name", ""),
                expert_domain=expert.get("domain", ""),
                years_of_experience=expert.get("years_of_experience", ""),
                short_bio=expert.get("short_bio", ""),
                discovery_state=json.dumps(discovery_state, indent=2),
                conversation_history=conv_history,
                expert_answer=expert_answer
            )

            # Enforce transition target & reflection style via prompt suffix injection
            prompt_content += f"""

TRANSITION & DIVERSITY CONTROLS:
- You are strictly in Stage {current_stage} ({stage_name}). You MUST focus your single follow-up question entirely on discovering {stage_name}. Do NOT ask about any other field.
- If {stage_name} is 'duration_weeks', ask how long this learning journey takes in weeks/months.
- If {stage_name} is 'course_title', ask what they would name this course.
- Use this reflection style: {selected_style}.
- CRITICAL: Never start your reflection with generic template phrases (e.g. 'You've highlighted...', 'You've beautifully described...'). Make it sound like a natural, unique conversational bridge.
"""
            disc_res = await self.llm.ainvoke(prompt_content)
            disc_data = self._parse_json(disc_res.content)
            reflection = disc_data.get("reflection", "").strip()
            question   = disc_data.get("question", "").strip()
            if reflection and question:
                next_question = f"{reflection} {question}"
            elif question:
                next_question = question
        except Exception as e:
            logger.warning(f"Phase 1 question generation failed: {e}")

        # Append AI question to transcript
        raw_transcript += f"\n\n[AI JOURNALIST]: {next_question}"

        # Persist scratchpad + transcript
        scratchpad["discovery_field_status"] = field_status
        self.supabase.table("interview_sessions").update({
            "raw_transcript":  raw_transcript,
            "live_scratchpad": scratchpad
        }).eq("id", session_id).execute()

        return {
            "question":       next_question,
            "field_status":   field_status,
            "phase_complete": False,
            "course_identity": None
        }

    def _get_discovery_stage(self, field_status: dict) -> int:
        """Map field completion state to current discovery stage (1-4)."""
        if not field_status.get("course_context"):
            return 1
        if not field_status.get("student_personas"):
            return 2
        if not field_status.get("duration_weeks"):
            return 3
        return 4

    # =========================================================================
    # PHASE 2 — MODULE DISCOVERY ENGINE
    # =========================================================================
    # Runs AFTER Phase 1 (course_identity confirmed), BEFORE Phase 3+
    # (per-module topic extraction).
    #
    # Discovers ONLY module_titles through natural conversation.
    # Includes a Curriculum Saturation Check before exit.
    # Writes to: curriculum_blueprints.course_modules (existing table/column).
    # =========================================================================

    async def module_discovery_turn(
        self,
        session_id: str,
        expert_answer: str
    ) -> Dict[str, Any]:
        """
        Process one turn of the Phase 2 Module Discovery conversation.

        Returns:
          {
            "question":          str | None  — next question, or None when phase done,
            "discovered_modules": list        — all module titles found so far,
            "phase_complete":    bool,
            "saturation_passed": bool | None  — None until saturation check runs
          }
        """
        # ── 1. Fetch session + expert ─────────────────────────────────────
        session_res = self.supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Session not found.")
        session = session_res.data[0]
        expert  = await self._get_expert(session["expert_id"])

        # ── 2. Append expert answer to transcript ─────────────────────────
        raw_transcript = session.get("raw_transcript", "").strip()
        raw_transcript += f"\n\n[EXPERT]: {expert_answer}"

        # ── 3. Pull Phase 2 scratchpad state ──────────────────────────────
        scratchpad       = session.get("live_scratchpad", {})
        discovered_modules: List[str] = scratchpad.get("discovered_modules", [])
        reflection_asked: bool        = scratchpad.get("module_reflection_asked", False)

        conv_history = self._build_conversation_history(raw_transcript, max_turns=6)
        conv_context = self._build_conversation_history(raw_transcript, max_turns=2)

        # ── 3.5. Curriculum Classification (Phase 2.5) ──────────────────
        classification = "OTHER"
        confidence = 0.0
        extracted_items = []
        clarifying_q = ""
        try:
            class_res = await self.llm_fast.ainvoke(
                CURRICULUM_CLASSIFICATION_PROMPT.format(
                    expert_answer=expert_answer,
                    transcript=raw_transcript
                )
            )
            class_data = self._parse_json(class_res.content)
            classification = str(class_data.get("classification", "OTHER")).upper()
            confidence = float(class_data.get("confidence", 0.0))
            extracted_items = class_data.get("extracted_items", [])
            clarifying_q = class_data.get("clarifying_question_suggestion", "")
        except Exception as e:
            logger.warning(f"Phase 2.5 Curriculum Classification failed: {e}")

        # If candidates are detected, apply strict validation/steering checks (Candidate Buffer)
        if extracted_items:
            if classification == "LEARNING_JOURNEY":
                steer_q = "I really like that progression—it describes the transformation beautifully. Now, if we were to translate that journey into the actual structure of the course, what would the major teaching modules be?"
                raw_transcript += f"\n\n[AI JOURNALIST]: {steer_q}"
                self.supabase.table("interview_sessions").update({
                    "raw_transcript": raw_transcript
                }).eq("id", session["id"]).execute()
                return {
                    "question": steer_q,
                    "discovered_modules": discovered_modules,
                    "phase_complete": False,
                    "saturation_passed": None
                }
            elif classification == "PREREQUISITE":
                steer_q = "Those sound like the foundational areas learners need before starting the course. Would you treat these as prerequisites that prepare students for the rest of the course, or are these actually the major modules of the course itself?"
                raw_transcript += f"\n\n[AI JOURNALIST]: {steer_q}"
                self.supabase.table("interview_sessions").update({
                    "raw_transcript": raw_transcript
                }).eq("id", session["id"]).execute()
                return {
                    "question": steer_q,
                    "discovered_modules": discovered_modules,
                    "phase_complete": False,
                    "saturation_passed": None
                }
            elif classification == "TOPIC":
                steer_q = "Those feel like specific, detailed lessons or topics rather than high-level modules. What would be the broader module or milestone that these lessons fit under?"
                raw_transcript += f"\n\n[AI JOURNALIST]: {steer_q}"
                self.supabase.table("interview_sessions").update({
                    "raw_transcript": raw_transcript
                }).eq("id", session["id"]).execute()
                return {
                    "question": steer_q,
                    "discovered_modules": discovered_modules,
                    "phase_complete": False,
                    "saturation_passed": None
                }
            elif classification == "MODULE" and confidence >= 0.85:
                # If they listed a group (>= 3 items), overwrite to prevent transcript duplication loops
                if len(extracted_items) >= 3:
                    discovered_modules = [m.strip() for m in extracted_items if m.strip()]
                    # Persist immediately to database so Phase 3 has the clean list
                    modules_payload = [{"module_title": m} for m in discovered_modules]
                    try:
                        cb_res = self.supabase.table("curriculum_blueprints").select("*").eq("expert_id", session["expert_id"]).execute()
                        if cb_res.data:
                            self.supabase.table("curriculum_blueprints").update({
                                "course_modules": modules_payload,
                                "iteration_last_updated": session.get("iteration_number", 1)
                            }).eq("expert_id", session["expert_id"]).execute()
                        else:
                            self.supabase.table("curriculum_blueprints").insert({
                                "expert_id":  session["expert_id"],
                                "session_id": session["id"],
                                "course_modules": modules_payload,
                                "iteration_last_updated": session.get("iteration_number", 1)
                            }).execute()
                        logger.info(f"Phase 2.5: Overwrote modules list in database with {len(discovered_modules)} clean modules.")
                    except Exception as e:
                        logger.error(f"Phase 2.5 blueprint overwrite failed: {e}")
                else:
                    # Append new items avoiding duplicates
                    existing_lower = {m.lower() for m in discovered_modules}
                    for m in extracted_items:
                        if m.strip() and m.strip().lower() not in existing_lower:
                            discovered_modules.append(m.strip())
            elif confidence < 0.85:
                steer_q = clarifying_q or "To make sure I capture this correctly — are these the major teaching modules of the course, or are they prerequisites/pacing stages?"
                raw_transcript += f"\n\n[AI JOURNALIST]: {steer_q}"
                self.supabase.table("interview_sessions").update({
                    "raw_transcript": raw_transcript
                }).eq("id", session["id"]).execute()
                return {
                    "question": steer_q,
                    "discovered_modules": discovered_modules,
                    "phase_complete": False,
                    "saturation_passed": None
                }


        # ── 4. Coverage Controller (Full Transcript Module Extraction) ──
        expert_signaled_complete = False
        try:
            cov_res = await self.llm_fast.ainvoke(
                MODULE_COVERAGE_CONTROLLER_PROMPT.format(
                    transcript=raw_transcript
                )
            )
            cov_data = self._parse_json(cov_res.content)
            extracted_mods = cov_data.get("modules", [])
            expert_signaled_complete = bool(cov_data.get("expert_signaled_complete", False))

            # Merge deduplicated
            existing_lower = {m.lower() for m in discovered_modules}
            for mod in extracted_mods:
                if mod.strip() and mod.strip().lower() not in existing_lower:
                    discovered_modules.append(mod.strip())
                    existing_lower.add(mod.strip().lower())

            # Transition Controller: if we already have >= 4 modules extracted, we can trigger the saturation flow
            if len(discovered_modules) >= 4 and not reflection_asked:
                expert_signaled_complete = True
        except Exception as e:
            logger.warning(f"Phase 2 Coverage Controller failed: {e}")

        # ── 5. SATURATION CHECK ──
        should_check_saturation = False
        if expert_signaled_complete and discovered_modules:
            should_check_saturation = True
        elif reflection_asked and discovered_modules:
            should_check_saturation = True
            
        if should_check_saturation:
            course_identity = expert.get("course_description", "")
            saturation_passed = False
            recovery_question = None
            try:
                sat_res = await self.llm.ainvoke(
                    MODULE_SATURATION_CHECK_PROMPT.format(
                        course_context=course_identity,
                        student_personas=expert.get("target_audience", ""),
                        duration_weeks=scratchpad.get("phase1_duration_weeks", "Unknown"),
                        discovered_modules=json.dumps(
                            [{"module_title": m} for m in discovered_modules],
                            indent=2
                        )
                    )
                )
                sat_data = self._parse_json(sat_res.content)
                saturation_passed  = bool(sat_data.get("saturation_passed", False))
                recovery_question  = sat_data.get("recovery_question", "")
            except Exception as e:
                logger.warning(f"Phase 2 saturation check failed: {e}")
                saturation_passed = True  # fail-safe: don't block forever

            if saturation_passed:
                # ── COMPLETE: Persist modules to curriculum_blueprints ──────
                modules_payload = [{"module_title": m} for m in discovered_modules]
                try:
                    cb_res = self.supabase.table("curriculum_blueprints").select("*").eq("expert_id", session["expert_id"]).execute()
                    if cb_res.data:
                        self.supabase.table("curriculum_blueprints").update({
                            "course_modules": modules_payload,
                            "iteration_last_updated": session.get("iteration_number", 1)
                        }).eq("expert_id", session["expert_id"]).execute()
                    else:
                        self.supabase.table("curriculum_blueprints").insert({
                            "expert_id":  session["expert_id"],
                            "session_id": session_id,
                            "course_modules": modules_payload,
                            "iteration_last_updated": session.get("iteration_number", 1)
                        }).execute()
                except Exception as e:
                    logger.error(f"Phase 2 curriculum_blueprints persist failed: {e}")

                scratchpad["discovered_modules"]    = discovered_modules
                scratchpad["phase2_complete"]        = True
                scratchpad["module_reflection_asked"] = True

                self.supabase.table("interview_sessions").update({
                    "raw_transcript":  raw_transcript,
                    "live_scratchpad": scratchpad
                }).eq("id", session_id).execute()

                logger.info(f"Phase 2 complete for session {session_id}. {len(discovered_modules)} modules persisted.")
                return {
                    "question":          None,
                    "discovered_modules": discovered_modules,
                    "phase_complete":    True,
                    "saturation_passed": True
                }

            else:
                # Saturation failed — ask the recovery question
                recovery_q = recovery_question or (
                    "Looking at the whole journey from start to finish — "
                    "is there any important stage a learner would need that we haven't named yet?"
                )
                raw_transcript += f"\n\n[AI JOURNALIST]: {recovery_q}"
                scratchpad["discovered_modules"]    = discovered_modules
                scratchpad["module_reflection_asked"] = True
                self.supabase.table("interview_sessions").update({
                    "raw_transcript":  raw_transcript,
                    "live_scratchpad": scratchpad
                }).eq("id", session_id).execute()

                return {
                    "question":          recovery_q,
                    "discovered_modules": discovered_modules,
                    "phase_complete":    False,
                    "saturation_passed": False
                }

        # ── 6. IN PROGRESS: Generate next discovery question ───────────────
        # Pull course identity to ground the prompt
        course_identity_synthesis = session.get("session_synthesis", {})
        course_title    = expert.get("course_title", "this course")
        course_context  = expert.get("course_description", "")
        student_personas = expert.get("target_audience", "")
        duration_weeks  = course_identity_synthesis.get("duration_weeks", "")

        # Store duration_weeks in scratchpad for saturation check later
        if duration_weeks:
            scratchpad["phase1_duration_weeks"] = duration_weeks

        next_question = (
            "Once learners finish that stage, what major milestone comes next in the journey?"
        )
        phase_ready_for_saturation = False
        try:
            # Dynamic Reflection Style Rotation (Diversity Controller)
            reflection_styles = [
                "Insight reflection: Highlight the conceptual shift between the chapters you've named.",
                "Contrast reflection: Contrast these modules with traditional, purely academic curriculum frameworks.",
                "Surprise reflection: Acknowledge a unique or highly practical stage they decided to include.",
                "Connection reflection: Connect how these chapters will specifically address the learner personas defined in Phase 1."
            ]
            turn_count = len([l for l in raw_transcript.split("\n") if l.startswith("[EXPERT]:")])
            selected_style = reflection_styles[turn_count % len(reflection_styles)]

            prompt_content = MODULE_DISCOVERY_ENGINE_PROMPT.format(
                course_title=course_title,
                course_context=course_context,
                student_personas=student_personas,
                duration_weeks=duration_weeks or "Not specified",
                discovered_modules=json.dumps(
                    [{"module_title": m} for m in discovered_modules],
                    indent=2
                ) if discovered_modules else "[]",
                module_count=len(discovered_modules),
                conversation_history=conv_history,
                expert_answer=expert_answer
            )

            # Suffix injection for transition & diversity controls
            prompt_content += f"""

TRANSITION & DIVERSITY CONTROLS:
- Your target: Discover the next major modules of this learning journey.
- Use this reflection style: {selected_style}.
- CRITICAL: Never start your reflection with generic template phrases (e.g. 'You've highlighted...', 'You've beautifully described...'). Make it sound like a natural, unique conversational bridge.
"""
            disc_res = await self.llm.ainvoke(prompt_content)
            disc_data = self._parse_json(disc_res.content)

            # Pick up any modules the conversational engine also detected
            for mod in disc_data.get("new_modules_detected", []):
                if mod.strip() and mod.strip().lower() not in {m.lower() for m in discovered_modules}:
                    discovered_modules.append(mod.strip())

            reflection  = disc_data.get("reflection", "").strip()
            question    = disc_data.get("question", "").strip()
            phase_ready_for_saturation = bool(disc_data.get("phase_ready_for_saturation_check", False))

            if reflection and question:
                next_question = f"{reflection} {question}"
            elif question:
                next_question = question
        except Exception as e:
            logger.warning(f"Phase 2 question generation failed: {e}")

        # If expert_signaled_complete but reflection not yet asked → ask reflection first
        if expert_signaled_complete and not reflection_asked:
            next_question = (
                "That's really helpful. Just to make sure we haven't missed anything — "
                "looking at the whole journey from beginning to end, is there any important "
                "stage a learner would need that we haven't named yet?"
            )
            scratchpad["module_reflection_asked"] = True

        raw_transcript += f"\n\n[AI JOURNALIST]: {next_question}"

        scratchpad["discovered_modules"]    = discovered_modules
        scratchpad["module_reflection_asked"] = scratchpad.get("module_reflection_asked", False)

        self.supabase.table("interview_sessions").update({
            "raw_transcript":  raw_transcript,
            "live_scratchpad": scratchpad
        }).eq("id", session_id).execute()

        return {
            "question":          next_question,
            "discovered_modules": discovered_modules,
            "phase_complete":    False,
            "saturation_passed": None
        }

    # =========================================================================
    # PHASE 3 — MODULE ENRICHMENT ENGINE
    # =========================================================================
    # Runs AFTER Phase 2 (module titles complete), module-by-module.
    # Enriches ONE module per pass through all turns until all 3 fields done,
    # then advances to the next module. Exits when all modules are enriched.
    #
    # Owns ONLY: module_context, learning_outcomes, module_constraints
    # Writes to: curriculum_blueprints.course_modules (in-place, per module)
    # =========================================================================

    async def module_enrichment_turn(
        self,
        session_id: str,
        expert_answer: str
    ) -> Dict[str, Any]:
        """
        Process one turn of Phase 3 Module Enrichment.

        Enriches modules one at a time in sequence.
        When a module's 3 fields are complete, synthesizes + persists it,
        then advances to the next module automatically.

        Returns:
          {
            "question":           str | None,
            "current_module":     str,
            "current_module_idx": int,
            "total_modules":      int,
            "field_status":       {module_context, learning_outcomes, module_constraints},
            "module_complete":    bool,
            "phase_complete":     bool
          }
        """
        # ── 1. Fetch session + expert ─────────────────────────────────────
        session_res = self.supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Session not found.")
        session = session_res.data[0]
        expert  = await self._get_expert(session["expert_id"])

        # ── 2. Load curriculum_blueprints ─────────────────────────────────
        cb_res = self.supabase.table("curriculum_blueprints").select("*").eq("expert_id", session["expert_id"]).execute()
        if not cb_res.data:
            raise HTTPException(status_code=404, detail="No curriculum blueprints found. Complete Phase 2 first.")
        blueprint      = cb_res.data[0]
        course_modules: List[Dict] = blueprint.get("course_modules", [])
        total_modules  = len(course_modules)

        # ── Self-Healing Curriculum Dedup & Reordering Block ──────────────
        needs_dedup = False
        if len(course_modules) > 8:
            needs_dedup = True
            
        if needs_dedup:
            logger.info("Self-healing: duplicate curriculum modules detected. Cleaning up and merging...")
            MAP = {
                "backend foundations": "Backend Engineering Foundations",
                "backend engineering foundations": "Backend Engineering Foundations",
                "building reliable services": "Building Production-Ready Services",
                "building production-ready services": "Building Production-Ready Services",
                "operating production systems": "Operating Backend Systems",
                "operating backend systems": "Operating Backend Systems",
                "system design & distributed architecture": "System Design & Distributed Systems",
                "system design & distributed systems": "System Design & Distributed Systems",
                "performance, scalability & reliability": "Performance, Scalability & Reliability",
                "engineering judgment": "Engineering Judgment & Architecture",
                "engineering judgment & architecture": "Engineering Judgment & Architecture",
                "owning production systems": "Production Ownership",
                "production ownership": "Production Ownership",
                "technical leadership & professional engineering": "Technical Leadership & Professional Engineering"
            }
            ORDER = [
                "Backend Engineering Foundations",
                "Building Production-Ready Services",
                "Operating Backend Systems",
                "System Design & Distributed Systems",
                "Performance, Scalability & Reliability",
                "Engineering Judgment & Architecture",
                "Production Ownership",
                "Technical Leadership & Professional Engineering"
            ]
            
            # Group and merge by mapped title
            merged_modules = {}
            for mod in course_modules:
                orig_title = mod.get("module_title", "")
                mapped_title = MAP.get(orig_title.lower().strip(), orig_title)
                
                if mapped_title not in merged_modules:
                    merged_modules[mapped_title] = {
                        "module_title": mapped_title,
                        "module_context": mod.get("module_context", ""),
                        "learning_outcomes": mod.get("learning_outcomes", []),
                        "module_constraints": mod.get("module_constraints", []),
                        "topics": mod.get("topics", [])
                    }
                else:
                    # Merge fields if they have content
                    curr = merged_modules[mapped_title]
                    if not curr["module_context"] and mod.get("module_context"):
                        curr["module_context"] = mod["module_context"]
                    if not curr["learning_outcomes"] and mod.get("learning_outcomes"):
                        curr["learning_outcomes"] = mod["learning_outcomes"]
                    if not curr["module_constraints"] and mod.get("module_constraints"):
                        curr["module_constraints"] = mod["module_constraints"]
                    if not curr["topics"] and mod.get("topics"):
                        curr["topics"] = mod["topics"]
            
            # Reconstruct list in exact ORDER
            new_modules_list = []
            for title in ORDER:
                if title in merged_modules:
                    new_modules_list.append(merged_modules[title])
                else:
                    new_modules_list.append({
                        "module_title": title,
                        "module_context": "",
                        "learning_outcomes": [],
                        "module_constraints": [],
                        "topics": []
                    })
            
            # Persist clean list
            try:
                self.supabase.table("curriculum_blueprints").update({
                    "course_modules": new_modules_list
                }).eq("expert_id", session["expert_id"]).execute()
                
                # Replace our local reference
                course_modules = new_modules_list
                total_modules = len(course_modules)
                
                # Find first incomplete module index
                first_incomplete = 0
                for idx, mod in enumerate(course_modules):
                    if not mod.get("module_context") or not mod.get("learning_outcomes"):
                        first_incomplete = idx
                        break
                
                # Update scratchpad pointer
                scratchpad = session.get("live_scratchpad", {})
                enrich_idx = first_incomplete
                scratchpad["enrichment_module_idx"] = enrich_idx
                scratchpad["enrichment_field_status"] = {
                    "module_context": bool(course_modules[enrich_idx].get("module_context")),
                    "learning_outcomes": bool(course_modules[enrich_idx].get("learning_outcomes")),
                    "module_constraints": bool(course_modules[enrich_idx].get("module_constraints"))
                }
                
                self.supabase.table("interview_sessions").update({
                    "live_scratchpad": scratchpad
                }).eq("id", session_id).execute()
                
                logger.info(f"Self-healing complete. Resuming at module index {enrich_idx}: '{course_modules[enrich_idx]['module_title']}'")
            except Exception as e:
                logger.error(f"Self-healing cleanup failed: {e}")

        # ── 3. Pull Phase 3 scratchpad state ──────────────────────────────
        scratchpad  = session.get("live_scratchpad", {})
        enrich_idx  = scratchpad.get("enrichment_module_idx", 0)   # which module we're on
        field_status = scratchpad.get("enrichment_field_status", {
            "module_context":    False,
            "learning_outcomes": False,
            "module_constraints": False
        })

        if total_modules == 0:
            raise HTTPException(status_code=400, detail="No modules discovered yet. Complete Phase 2 first.")

        # Safety: if we've somehow advanced past the end, mark phase done
        if enrich_idx >= total_modules:
            return {
                "question":           None,
                "current_module":     "",
                "current_module_idx": enrich_idx,
                "total_modules":      total_modules,
                "field_status":       field_status,
                "module_complete":    True,
                "phase_complete":     True
            }

        current_module = course_modules[enrich_idx]
        current_module_title = current_module.get("module_title", f"Module {enrich_idx + 1}")

        # ── 4. Append expert answer to transcript ─────────────────────────
        raw_transcript = session.get("raw_transcript", "").strip()
        raw_transcript += f"\n\n[EXPERT]: {expert_answer}"

        def _parse_json(content: str) -> dict:
            cl = content.strip()
            if "```json" in cl:
                cl = cl.split("```json")[1].split("```")[0].strip()
            cl = re.sub(r',\s*([}\]])', r'\1', cl)
            try:
                return json.loads(cl)
            except Exception:
                return {}

        conv_history = self._build_conversation_history(raw_transcript, max_turns=6)

        # ── 4.5. Curriculum Classification (Phase 2.5) ──────────────────
        classification = "OTHER"
        confidence = 0.0
        extracted_items = []
        try:
            class_res = await self.llm_fast.ainvoke(
                CURRICULUM_CLASSIFICATION_PROMPT.format(
                    expert_answer=expert_answer,
                    transcript=raw_transcript
                )
            )
            class_data = self._parse_json(class_res.content)
            classification = str(class_data.get("classification", "OTHER")).upper()
            confidence = float(class_data.get("confidence", 0.0))
            extracted_items = class_data.get("extracted_items", [])
        except Exception as e:
            logger.warning(f"Phase 2.5 Curriculum Classification in Phase 3 failed: {e}")

        if extracted_items and confidence >= 0.85:
            if classification == "PREREQUISITE":
                steer_q = f"Those foundational areas like {', '.join(extracted_items[:3])} are excellent prerequisites. But looking back at our current module, '{current_module_title}' itself: why does this specific milestone exist in the overall learning journey?"
                raw_transcript += f"\n\n[AI JOURNALIST]: {steer_q}"
                self.supabase.table("interview_sessions").update({
                    "raw_transcript": raw_transcript
                }).eq("id", session["id"]).execute()
                return {
                    "question":           steer_q,
                    "current_module":     current_module_title,
                    "current_module_idx": enrich_idx,
                    "total_modules":      total_modules,
                    "field_status":       field_status,
                    "module_complete":    False,
                    "phase_complete":     False
                }
            elif classification == "MODULE":
                steer_q = f"That is a helpful outline of modules. But staying focused on our current milestone, '{current_module_title}': what is the core learning outcome or purpose of this specific stage in the learner's journey?"
                raw_transcript += f"\n\n[AI JOURNALIST]: {steer_q}"
                self.supabase.table("interview_sessions").update({
                    "raw_transcript": raw_transcript
                }).eq("id", session["id"]).execute()
                return {
                    "question":           steer_q,
                    "current_module":     current_module_title,
                    "current_module_idx": enrich_idx,
                    "total_modules":      total_modules,
                    "field_status":       field_status,
                    "module_complete":    False,
                    "phase_complete":     False
                }
            elif classification == "TOPIC":
                steer_q = f"Those are great lessons that we will definitely map out later. But first, what is the high-level educational context or intent of the '{current_module_title}' module itself?"
                raw_transcript += f"\n\n[AI JOURNALIST]: {steer_q}"
                self.supabase.table("interview_sessions").update({
                    "raw_transcript": raw_transcript
                }).eq("id", session["id"]).execute()
                return {
                    "question":           steer_q,
                    "current_module":     current_module_title,
                    "current_module_idx": enrich_idx,
                    "total_modules":      total_modules,
                    "field_status":       field_status,
                    "module_complete":    False,
                    "phase_complete":     False
                }


        # ── 5. Coverage Controller (Full Transcript Evaluation) ──────────
        try:
            cov_res = await self.llm_fast.ainvoke(
                MODULE_ENRICHMENT_COVERAGE_CONTROLLER_PROMPT.format(
                    current_module_title=current_module_title,
                    transcript=raw_transcript
                )
            )
            cov_data = self._parse_json(cov_res.content)
            for field in ["module_context", "learning_outcomes", "module_constraints"]:
                field_info = cov_data.get(field, {})
                status = str(field_info.get("status", "")).upper()
                score = float(field_info.get("score", 0.0))
                if status in ["SUFFICIENT", "COMPLETE"] or score >= 0.75:
                    field_status[field] = True
        except Exception as e:
            logger.warning(f"Phase 3 Coverage Controller failed: {e}")

        all_fields_done = all(field_status.values())

        # ── 6a. MODULE COMPLETE: Synthesize + persist this module ──────────
        if all_fields_done:
            enriched_data = {}
            try:
                synth_res = await self.llm.ainvoke(
                    MODULE_ENRICHMENT_SYNTHESIZER_PROMPT.format(
                        current_module_title=current_module_title,
                        transcript=raw_transcript
                    )
                )
                enriched_data = self._parse_json(synth_res.content)
            except Exception as e:
                logger.warning(f"Phase 3 synthesizer failed for '{current_module_title}': {e}")

            # Merge enrichment into the module object in-place
            course_modules[enrich_idx]["module_context"]    = enriched_data.get("module_context", "")
            course_modules[enrich_idx]["learning_outcomes"] = enriched_data.get("learning_outcomes", [])
            course_modules[enrich_idx]["module_constraints"] = enriched_data.get("module_constraints", [])
            if "topics" not in course_modules[enrich_idx]:
                course_modules[enrich_idx]["topics"] = []

            # Persist updated modules back to curriculum_blueprints
            try:
                self.supabase.table("curriculum_blueprints").update({
                    "course_modules": course_modules
                }).eq("expert_id", session["expert_id"]).execute()
                logger.info(f"Phase 3: enriched '{current_module_title}' (module {enrich_idx + 1}/{total_modules})")
            except Exception as e:
                logger.error(f"Phase 3 blueprint persist failed: {e}")

            # Advance to next module
            next_idx = enrich_idx + 1
            phase_complete = (next_idx >= total_modules)

            # Reset field status for the next module
            next_field_status = {
                "module_context":    False,
                "learning_outcomes": False,
                "module_constraints": False
            }
            scratchpad["enrichment_module_idx"]   = next_idx
            scratchpad["enrichment_field_status"] = next_field_status

            self.supabase.table("interview_sessions").update({
                "raw_transcript":  raw_transcript,
                "live_scratchpad": scratchpad
            }).eq("id", session_id).execute()

            if phase_complete:
                # Mark phase 3 done in session_synthesis
                existing_synthesis = session.get("session_synthesis") or {}
                existing_synthesis["phase3_enrichment_complete"] = True
                self.supabase.table("interview_sessions").update({
                    "session_synthesis": existing_synthesis
                }).eq("id", session_id).execute()
                logger.info(f"Phase 3 fully complete for session {session_id}.")
                return {
                    "question":           None,
                    "current_module":     current_module_title,
                    "current_module_idx": enrich_idx,
                    "total_modules":      total_modules,
                    "field_status":       field_status,
                    "module_complete":    True,
                    "phase_complete":     True
                }

            # Not done yet — generate opener for the next module
            next_module_title = course_modules[next_idx].get("module_title", f"Module {next_idx + 1}")
            transition_q = (
                f"Great. That gives us a really clear picture of what \"{current_module_title}\" "
                f"is all about. Let's move to the next module: \"{next_module_title}\". "
                f"In the context of the overall course, what role does this stage play "
                f"in the learner's journey?"
            )
            raw_transcript += f"\n\n[AI JOURNALIST]: {transition_q}"
            self.supabase.table("interview_sessions").update({
                "raw_transcript":  raw_transcript,
                "live_scratchpad": scratchpad
            }).eq("id", session_id).execute()

            return {
                "question":           transition_q,
                "current_module":     next_module_title,
                "current_module_idx": next_idx,
                "total_modules":      total_modules,
                "field_status":       next_field_status,
                "module_complete":    True,
                "phase_complete":     False
            }

        # ── 6b. IN PROGRESS: Transition & Conversation Diversity Controllers ──
        # Find next field to discover
        current_enrich_field = "module_context"
        if field_status.get("module_context"):
            current_enrich_field = "learning_outcomes"
        if field_status.get("module_context") and field_status.get("learning_outcomes"):
            current_enrich_field = "module_constraints"

        next_question = f"What role does \"{current_module_title}\" play in the overall learning journey?"
        try:
            # Dynamic Reflection Style Rotation (Diversity Controller)
            reflection_styles = [
                "Insight reflection: Reflect conceptually on the purpose and outcomes of this module.",
                "Mindset reflection: Focus on how this module reduces the developer's stress or shifts their confidence.",
                "Contrast reflection: Contrast this module's goals with the typical tutorials that fail in production.",
                "Connection reflection: Connect this module to the overall transformation of 'programmer to systems engineer'."
            ]
            turn_count = len([l for l in raw_transcript.split("\n") if l.startswith("[EXPERT]:")])
            selected_style = reflection_styles[turn_count % len(reflection_styles)]

            prompt_content = MODULE_ENRICHMENT_ENGINE_PROMPT.format(
                course_title=expert.get("course_title", "this course"),
                course_context=expert.get("course_description", ""),
                student_personas=expert.get("target_audience", ""),
                current_module_idx=enrich_idx + 1,
                total_modules=total_modules,
                current_module_title=current_module_title,
                field_status=json.dumps({
                    "module_context":    field_status["module_context"],
                    "learning_outcomes": field_status["learning_outcomes"],
                    "module_constraints": field_status["module_constraints"]
                }, indent=2),
                conversation_history=conv_history,
                expert_answer=expert_answer
            )

            # Suffix injection for transition & diversity controls
            prompt_content += f"""

TRANSITION & DIVERSITY CONTROLS:
- You are strictly discovering '{current_enrich_field}' for module '{current_module_title}'. You MUST focus your single follow-up question entirely on discovering '{current_enrich_field}'. Do NOT ask about any other field.
- If target is 'learning_outcomes', ask what concrete skills they will prove or build.
- If target is 'module_constraints', ask about boundaries, rules, or what is deliberately left out.
- Use this reflection style: {selected_style}.
- CRITICAL: Never start your reflection with generic template phrases (e.g. 'You've highlighted...', 'You've beautifully described...'). Make it sound like a natural, unique conversational bridge.
"""
            enrich_res = await self.llm.ainvoke(prompt_content)
            enrich_data = self._parse_json(enrich_res.content)
            reflection  = enrich_data.get("reflection", "").strip()
            question    = enrich_data.get("question", "").strip()
            if reflection and question:
                next_question = f"{reflection} {question}"
            elif question:
                next_question = question
        except Exception as e:
            logger.warning(f"Phase 3 question generation failed: {e}")

        raw_transcript += f"\n\n[AI JOURNALIST]: {next_question}"
        scratchpad["enrichment_field_status"] = field_status
        scratchpad["enrichment_module_idx"]   = enrich_idx

        self.supabase.table("interview_sessions").update({
            "raw_transcript":  raw_transcript,
            "live_scratchpad": scratchpad
        }).eq("id", session_id).execute()

        return {
            "question":           next_question,
            "current_module":     current_module_title,
            "current_module_idx": enrich_idx,
            "total_modules":      total_modules,
            "field_status":       field_status,
            "module_complete":    False,
            "phase_complete":     False
        }

    # =========================================================================
    # PHASE 4 — TOPIC DISCOVERY ENGINE
    # =========================================================================
    # Runs AFTER Phase 3 (all modules enriched). Operates module-by-module.
    #
    # Owns ONLY: topics[].topic_title
    # Exit gate: Learning Outcome Coverage Validator must confirm all outcomes
    # are supported before advancing to next module.
    # Writes to: curriculum_blueprints.course_modules[idx]["topics"]
    # =========================================================================

    async def topic_discovery_turn(
        self,
        session_id: str,
        expert_answer: str
    ) -> Dict[str, Any]:
        """
        Process one turn of Phase 4 Topic Discovery.

        Discovers topic_titles module-by-module.
        Exit gate: TOPIC_COVERAGE_VALIDATOR ensures every learning_outcome
        is supported by at least one topic before advancing.

        Returns:
          {
            "question":           str | None,
            "current_module":     str,
            "current_module_idx": int,
            "total_modules":      int,
            "discovered_topics":  list of str,
            "coverage_map":       dict (populated after validator runs),
            "module_complete":    bool,
            "phase_complete":     bool
          }
        """
        # ── 1. Fetch session + expert ─────────────────────────────────────
        session_res = self.supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Session not found.")
        session = session_res.data[0]
        expert  = await self._get_expert(session["expert_id"])

        # ── 2. Load curriculum_blueprints ─────────────────────────────────
        cb_res = self.supabase.table("curriculum_blueprints").select("*").eq("expert_id", session["expert_id"]).execute()
        if not cb_res.data:
            raise HTTPException(status_code=404, detail="No curriculum blueprints found. Complete Phase 3 first.")
        blueprint      = cb_res.data[0]
        course_modules: List[Dict] = blueprint.get("course_modules", [])
        total_modules  = len(course_modules)

        if total_modules == 0:
            raise HTTPException(status_code=400, detail="No modules found. Complete Phase 3 first.")

        # ── 3. Pull Phase 4 scratchpad state ──────────────────────────────
        scratchpad       = session.get("live_scratchpad", {})
        topic_mod_idx    = scratchpad.get("topic_discovery_module_idx", 0)
        discovered_topics: List[str] = scratchpad.get("topic_discovery_topics", [])
        reflection_asked: bool       = scratchpad.get("topic_reflection_asked", False)

        # Safety: already past end
        if topic_mod_idx >= total_modules:
            return {
                "question":           None,
                "current_module":     "",
                "current_module_idx": topic_mod_idx,
                "total_modules":      total_modules,
                "discovered_topics":  discovered_topics,
                "coverage_map":       {},
                "module_complete":    True,
                "phase_complete":     True
            }

        current_module       = course_modules[topic_mod_idx]
        current_module_title = current_module.get("module_title", f"Module {topic_mod_idx + 1}")
        learning_outcomes    = current_module.get("learning_outcomes", [])

        # ── 4. Append expert answer ────────────────────────────────────────
        raw_transcript = session.get("raw_transcript", "").strip()
        raw_transcript += f"\n\n[EXPERT]: {expert_answer}"
        conv_history = self._build_conversation_history(raw_transcript, max_turns=6)
        conv_context = self._build_conversation_history(raw_transcript, max_turns=2)

        # ── 4.5. Curriculum Classification (Phase 2.5) ──────────────────
        classification = "OTHER"
        confidence = 0.0
        extracted_items = []
        try:
            class_res = await self.llm_fast.ainvoke(
                CURRICULUM_CLASSIFICATION_PROMPT.format(
                    expert_answer=expert_answer,
                    transcript=raw_transcript
                )
            )
            class_data = self._parse_json(class_res.content)
            classification = str(class_data.get("classification", "OTHER")).upper()
            confidence = float(class_data.get("confidence", 0.0))
            extracted_items = class_data.get("extracted_items", [])
        except Exception as e:
            logger.warning(f"Phase 2.5 Curriculum Classification in Phase 4 failed: {e}")

        if extracted_items and confidence >= 0.85:
            if classification == "PREREQUISITE":
                steer_q = f"Those sound like foundational prerequisites. For the '{current_module_title}' module itself, what are the actual lessons or topics we should teach?"
                raw_transcript += f"\n\n[AI JOURNALIST]: {steer_q}"
                self.supabase.table("interview_sessions").update({
                    "raw_transcript": raw_transcript
                }).eq("id", session["id"]).execute()
                return {
                    "question":           steer_q,
                    "current_module":     current_module_title,
                    "current_module_idx": topic_mod_idx,
                    "total_modules":      total_modules,
                    "discovered_topics":  discovered_topics,
                    "coverage_map":       {},
                    "module_complete":    False,
                    "phase_complete":     False
                }
            elif classification == "MODULE":
                steer_q = f"Those feel like high-level course modules. For our current module, '{current_module_title}', what are the specific topics or lessons that belong inside it?"
                raw_transcript += f"\n\n[AI JOURNALIST]: {steer_q}"
                self.supabase.table("interview_sessions").update({
                    "raw_transcript": raw_transcript
                }).eq("id", session["id"]).execute()
                return {
                    "question":           steer_q,
                    "current_module":     current_module_title,
                    "current_module_idx": topic_mod_idx,
                    "total_modules":      total_modules,
                    "discovered_topics":  discovered_topics,
                    "coverage_map":       {},
                    "module_complete":    False,
                    "phase_complete":     False
                }
            elif classification == "TOPIC":
                # If they listed a group (>= 2 items), overwrite to prevent transcript duplication loops
                if len(extracted_items) >= 2:
                    discovered_topics = [t.strip() for t in extracted_items if t.strip()]
                    logger.info(f"Phase 4.5: Overwrote topics list in scratchpad with {len(discovered_topics)} clean topics.")
                else:
                    # Append new items avoiding duplicates
                    existing_lower = {t.lower() for t in discovered_topics}
                    for t in extracted_items:
                        if t.strip() and t.strip().lower() not in existing_lower:
                            discovered_topics.append(t.strip())

        # ── 5. Coverage Controller (Full Transcript Topic Extraction) ──
        expert_signaled_complete = False
        try:
            cov_res = await self.llm_fast.ainvoke(
                TOPIC_COVERAGE_CONTROLLER_PROMPT.format(
                    current_module_title=current_module_title,
                    transcript=raw_transcript
                )
            )
            cov_data = self._parse_json(cov_res.content)
            extracted_topics = cov_data.get("topics", [])
            expert_signaled_complete = bool(cov_data.get("expert_signaled_complete", False))

            # Merge deduplicated
            existing_lower = {t.lower() for t in discovered_topics}
            for t in extracted_topics:
                if t.strip() and t.strip().lower() not in existing_lower:
                    discovered_topics.append(t.strip())
                    existing_lower.add(t.strip().lower())

            # Transition Controller: only trigger validation if the expert explicitly signaled completion
            # (or if we have asked the reflection/recovery question and they replied).
            # Do NOT force validation automatically just because we have >= 3 topics.
            pass
        except Exception as e:
            logger.warning(f"Phase 4 Coverage Controller failed: {e}")

        # ── 6. COVERAGE VALIDATOR ──
        should_validate = False
        if expert_signaled_complete and discovered_topics:
            should_validate = True
        elif reflection_asked and discovered_topics:
            should_validate = True
            
        if should_validate:
            coverage_map      = {}
            coverage_complete = False
            recovery_question = None
            try:
                val_res = await self.llm.ainvoke(
                    TOPIC_COVERAGE_VALIDATOR_PROMPT.format(
                        current_module_title=current_module_title,
                        learning_outcomes=json.dumps(learning_outcomes, indent=2),
                        discovered_topics=json.dumps(
                            [{"topic_title": t} for t in discovered_topics],
                            indent=2
                        )
                    )
                )
                val_data         = self._parse_json(val_res.content)
                coverage_complete = bool(val_data.get("coverage_complete", False))
                coverage_map      = val_data.get("coverage_map", {})
                recovery_question = val_data.get("recovery_question", "")
            except Exception as e:
                logger.warning(f"Phase 4 coverage validator failed: {e}")
                coverage_complete = True  # fail-safe

            if coverage_complete:
                # ── WRITE topics into this module's entry ─────────────────
                topics_payload = [{"topic_title": t} for t in discovered_topics]
                course_modules[topic_mod_idx]["topics"] = topics_payload

                try:
                    self.supabase.table("curriculum_blueprints").update({
                        "course_modules": course_modules
                    }).eq("expert_id", session["expert_id"]).execute()
                    logger.info(f"Phase 4: {len(discovered_topics)} topics written for '{current_module_title}'")
                except Exception as e:
                    logger.error(f"Phase 4 blueprint persist failed: {e}")

                # Advance to next module
                next_idx      = topic_mod_idx + 1
                phase_complete = (next_idx >= total_modules)

                scratchpad["topic_discovery_module_idx"] = next_idx
                scratchpad["topic_discovery_topics"]     = []   # reset for next module
                scratchpad["topic_reflection_asked"]     = False

                self.supabase.table("interview_sessions").update({
                    "raw_transcript":  raw_transcript,
                    "live_scratchpad": scratchpad
                }).eq("id", session_id).execute()

                if phase_complete:
                    existing_synthesis = session.get("session_synthesis") or {}
                    existing_synthesis["phase4_topic_discovery_complete"] = True
                    self.supabase.table("interview_sessions").update({
                        "session_synthesis": existing_synthesis
                    }).eq("id", session_id).execute()
                    logger.info(f"Phase 4 fully complete for session {session_id}.")
                    return {
                        "question":           None,
                        "current_module":     current_module_title,
                        "current_module_idx": topic_mod_idx,
                        "total_modules":      total_modules,
                        "discovered_topics":  discovered_topics,
                        "coverage_map":       coverage_map,
                        "module_complete":    True,
                        "phase_complete":     True
                    }

                # Transition to next module
                next_module_title = course_modules[next_idx].get("module_title", f"Module {next_idx + 1}")
                transition_q = (
                    f"Perfect. We've mapped out the lessons inside \"{current_module_title}\". "
                    f"Let's move to \"{next_module_title}\". "
                    f"How would you naturally break this module into its major lessons?"
                )
                raw_transcript += f"\n\n[AI JOURNALIST]: {transition_q}"
                self.supabase.table("interview_sessions").update({
                    "raw_transcript":  raw_transcript,
                    "live_scratchpad": scratchpad
                }).eq("id", session_id).execute()

                return {
                    "question":           transition_q,
                    "current_module":     next_module_title,
                    "current_module_idx": next_idx,
                    "total_modules":      total_modules,
                    "discovered_topics":  [],
                    "coverage_map":       coverage_map,
                    "module_complete":    True,
                    "phase_complete":     False
                }

            else:
                # Coverage incomplete — ask recovery question
                fallback_q = (
                    f"Looking at what learners should be able to do after this module — "
                    f"is there any important lesson we haven't included yet?"
                )
                rq = recovery_question or fallback_q
                raw_transcript += f"\n\n[AI JOURNALIST]: {rq}"
                scratchpad["topic_discovery_topics"]     = discovered_topics
                scratchpad["topic_discovery_module_idx"] = topic_mod_idx
                scratchpad["topic_reflection_asked"]     = True
                self.supabase.table("interview_sessions").update({
                    "raw_transcript":  raw_transcript,
                    "live_scratchpad": scratchpad
                }).eq("id", session_id).execute()

                return {
                    "question":           rq,
                    "current_module":     current_module_title,
                    "current_module_idx": topic_mod_idx,
                    "total_modules":      total_modules,
                    "discovered_topics":  discovered_topics,
                    "coverage_map":       coverage_map,
                    "module_complete":    False,
                    "phase_complete":     False
                }

        # ── 7. IN PROGRESS: Generate next topic discovery question ─────────
        # If expert just signaled complete but reflection not yet asked → ask it
        if expert_signaled_complete and not reflection_asked:
            reflection_q = (
                f"That's really helpful. Before we move on — looking at what "
                f"learners need to achieve from \"{current_module_title}\", "
                f"is there any lesson we've missed that would make the difference?"
            )
            raw_transcript += f"\n\n[AI JOURNALIST]: {reflection_q}"
            scratchpad["topic_reflection_asked"]     = True
            scratchpad["topic_discovery_topics"]     = discovered_topics
            scratchpad["topic_discovery_module_idx"] = topic_mod_idx
            self.supabase.table("interview_sessions").update({
                "raw_transcript":  raw_transcript,
                "live_scratchpad": scratchpad
            }).eq("id", session_id).execute()
            return {
                "question":           reflection_q,
                "current_module":     current_module_title,
                "current_module_idx": topic_mod_idx,
                "total_modules":      total_modules,
                "discovered_topics":  discovered_topics,
                "coverage_map":       {},
                "module_complete":    False,
                "phase_complete":     False
            }

        # Standard: generate next conversational question
        last_topic = discovered_topics[-1] if discovered_topics else ""
        next_question = (
            f"After {last_topic}, what other major lessons naturally belong inside "
            f"\"{current_module_title}\"?" if last_topic
            else f"If \"{current_module_title}\" were divided into its major lessons, what would naturally come first?"
        )
        try:
            # Dynamic Reflection Style Rotation (Diversity Controller)
            reflection_styles = [
                "Insight reflection: Acknowledge the logical progression of these topics inside this module.",
                "Contrast reflection: Contrast these practical topic areas with dry theoretical exercises.",
                "Surprise reflection: Acknowledge a non-obvious, highly operational lesson they decided to include.",
                "Connection reflection: Connect how these topics will enable the specific outcomes of this module."
            ]
            turn_count = len([l for l in raw_transcript.split("\n") if l.startswith("[EXPERT]:")])
            selected_style = reflection_styles[turn_count % len(reflection_styles)]

            prompt_content = TOPIC_DISCOVERY_ENGINE_PROMPT.format(
                course_title=expert.get("course_title", "this course"),
                current_module_idx=topic_mod_idx + 1,
                total_modules=total_modules,
                current_module_title=current_module_title,
                learning_outcomes=json.dumps(learning_outcomes, indent=2),
                discovered_topics=json.dumps(
                    [{"topic_title": t} for t in discovered_topics],
                    indent=2
                ) if discovered_topics else "[]",
                topic_count=len(discovered_topics),
                conversation_history=conv_history,
                expert_answer=expert_answer
            )

            # Suffix injection for transition & diversity controls
            prompt_content += f"""

TRANSITION & DIVERSITY CONTROLS:
- Your target: Discover the next major lesson/topic inside the module '{current_module_title}'.
- Use this reflection style: {selected_style}.
- CRITICAL: Never start your reflection with generic template phrases (e.g. 'You've highlighted...', 'You've beautifully described...'). Make it sound like a natural, unique conversational bridge.
"""
            disc_res = await self.llm.ainvoke(prompt_content)
            disc_data  = self._parse_json(disc_res.content)

            # Pick up any additional topics the engine spotted
            for t in disc_data.get("new_topics_detected", []):
                if t.strip() and t.strip().lower() not in {x.lower() for x in discovered_topics}:
                    discovered_topics.append(t.strip())

            reflection = disc_data.get("reflection", "").strip()
            question   = disc_data.get("question", "").strip()
            if reflection and question:
                next_question = f"{reflection} {question}"
            elif question:
                next_question = question
        except Exception as e:
            logger.warning(f"Phase 4 question generation failed: {e}")

        raw_transcript += f"\n\n[AI JOURNALIST]: {next_question}"
        scratchpad["topic_discovery_topics"]     = discovered_topics
        scratchpad["topic_discovery_module_idx"] = topic_mod_idx
        scratchpad["topic_reflection_asked"]     = reflection_asked

        self.supabase.table("interview_sessions").update({
            "raw_transcript":  raw_transcript,
            "live_scratchpad": scratchpad
        }).eq("id", session_id).execute()

        return {
            "question":           next_question,
            "current_module":     current_module_title,
            "current_module_idx": topic_mod_idx,
            "total_modules":      total_modules,
            "discovered_topics":  discovered_topics,
            "coverage_map":       {},
            "module_complete":    False,
            "phase_complete":     False
        }

    # =========================================================================
    # PHASE 5 — CURRICULUM VALIDATION & LOCK ENGINE
    # =========================================================================
    # Validates structural completeness of the entire curriculum before
    # unlocking Block 4 (Topic Knowledge Exploration).
    # Does NOT ask interview questions. Returns lock decision + validation report.
    # =========================================================================

    async def validate_and_lock_curriculum(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Validate curriculum structure and decide whether to lock.

        Returns:
          {
            "curriculum_locked": bool,
            "validation_report": dict,
            "next_state":        str
          }
        """
        # ── 1. Fetch session + expert ─────────────────────────────────────
        session_res = self.supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Session not found.")
        session = session_res.data[0]
        expert  = await self._get_expert(session["expert_id"])

        # ── 2. Load curriculum_blueprints ─────────────────────────────────
        cb_res = self.supabase.table("curriculum_blueprints").select("*").eq("expert_id", session["expert_id"]).execute()
        course_modules = []
        if cb_res.data:
            course_modules = cb_res.data[0].get("course_modules", [])

        # ── 3. Build evaluation payloads ──────────────────────────────────
        course_identity = {
            "course_title": expert.get("course_title", ""),
            "course_context": expert.get("course_description", ""),
            "student_personas": expert.get("target_audience", ""),
            "duration_weeks": session.get("session_synthesis", {}).get("duration_weeks")
        }

        def _parse_json(content: str) -> dict:
            cl = content.strip()
            if "```json" in cl:
                cl = cl.split("```json")[1].split("```")[0].strip()
            cl = re.sub(r',\s*([}\]])', r'\1', cl)
            try:
                return json.loads(cl)
            except Exception:
                return {}

        # ── 4. Call Validation LLM ────────────────────────────────────────
        validation_data = {
            "curriculum_locked": False,
            "validation_report": {
                "course_complete": False,
                "modules_complete": False,
                "module_enrichment_complete": False,
                "topic_discovery_complete": False,
                "missing_components": [{"module": "General", "missing": ["Could not run validation engine"]}]
            },
            "next_state": "COURSE_DISCOVERY"
        }

        try:
            val_res = await self.llm.ainvoke(
                CURRICULUM_VALIDATION_PROMPT.format(
                    course_identity=json.dumps(course_identity, indent=2),
                    modules=json.dumps(course_modules, indent=2)
                )
            )
            validation_data = _parse_json(val_res.content)
        except Exception as e:
            logger.warning(f"Phase 5 validation failed: {e}")

        # ── 5. Update session states with results ──────────────────────────
        scratchpad = session.get("live_scratchpad", {})
        scratchpad["curriculum_locked"] = bool(validation_data.get("curriculum_locked", False))

        existing_synthesis = session.get("session_synthesis") or {}
        existing_synthesis["curriculum_locked"] = bool(validation_data.get("curriculum_locked", False))
        existing_synthesis["validation_report"] = validation_data.get("validation_report", {})

        try:
            self.supabase.table("interview_sessions").update({
                "live_scratchpad": scratchpad,
                "session_synthesis": existing_synthesis
            }).eq("id", session_id).execute()
        except Exception as e:
            logger.error(f"Phase 5 status persist failed: {e}")

        return validation_data

    # =========================================================================
    # PHASE 6 — TOPIC INITIALIZATION ENGINE
    # =========================================================================
    # Selects the highest-priority incomplete topic and introduces it.
    # Sets current_module and current_topic state. Does not extract knowledge.
    # =========================================================================

    async def topic_initialization_turn(
        self,
        session_id: str,
        expert_answer: str = None
    ) -> Dict[str, Any]:
        """
        Scan curriculum blueprint for the next incomplete topic,
        and generate a warm transition question to start exploring it.

        Returns:
          {
            "question":           str | None,
            "current_module":     str,
            "current_topic":      str,
            "topic_ready":        bool,
            "next_engine":        str,
            "phase_complete":     bool
          }
        """
        # ── 1. Fetch session + expert ─────────────────────────────────────
        session_res = self.supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Session not found.")
        session = session_res.data[0]
        expert  = await self._get_expert(session["expert_id"])

        # ── 2. Load curriculum_blueprints ─────────────────────────────────
        cb_res = self.supabase.table("curriculum_blueprints").select("*").eq("expert_id", session["expert_id"]).execute()
        if not cb_res.data:
            raise HTTPException(status_code=404, detail="No curriculum blueprints found.")
        blueprint      = cb_res.data[0]
        course_modules: List[Dict] = blueprint.get("course_modules", [])

        # ── 3. Find first incomplete topic ────────────────────────────────
        selected_module = None
        selected_topic  = None
        current_module_idx = 0
        current_topic_idx = 0

        for m_idx, module in enumerate(course_modules):
            for t_idx, topic in enumerate(module.get("topics", [])):
                # Unexplored/incomplete topic has no concept field populated
                if not topic.get("concept"):
                    selected_module = module
                    selected_topic  = topic
                    current_module_idx = m_idx
                    current_topic_idx = t_idx
                    break
            if selected_topic:
                break

        # If all topics are completed
        if not selected_topic:
            return {
                "question":           None,
                "current_module":     "",
                "current_topic":      "",
                "topic_ready":        False,
                "next_engine":        "COMPLETE",
                "phase_complete":     True
            }

        current_module_title = selected_module.get("module_title", "")
        current_topic_title  = selected_topic.get("topic_title", "")

        # ── 4. Append expert answer to transcript if provided ─────────────
        raw_transcript = session.get("raw_transcript", "").strip()
        if expert_answer:
            raw_transcript += f"\n\n[EXPERT]: {expert_answer}"
        else:
            expert_answer = "(Transitioning to topic exploration)"

        def _parse_json(content: str) -> dict:
            cl = content.strip()
            if "```json" in cl:
                cl = cl.split("```json")[1].split("```")[0].strip()
            cl = re.sub(r',\s*([}\]])', r'\1', cl)
            try:
                return json.loads(cl)
            except Exception:
                return {}

        conv_history = self._build_conversation_history(raw_transcript, max_turns=6)

        # ── 5. Generate Opener Question ───────────────────────────────────
        next_question = f"Let's dive into {current_topic_title} under {current_module_title}."
        init_data = {}
        try:
            init_res = await self.llm.ainvoke(
                TOPIC_INITIALIZATION_PROMPT.format(
                    course_title=expert.get("course_title", ""),
                    course_description=expert.get("course_description", ""),
                    current_module_title=current_module_title,
                    module_context=selected_module.get("module_context", ""),
                    learning_outcomes=json.dumps(selected_module.get("learning_outcomes", []), indent=2),
                    current_topic_title=current_topic_title,
                    conversation_history=conv_history,
                    expert_answer=expert_answer
                )
            )
            init_data = _parse_json(init_res.content)
            next_question = init_data.get("question", next_question)
        except Exception as e:
            logger.warning(f"Phase 6 question generation failed: {e}")

        # ── 6. Update Scratchpad + Transcript ──────────────────────────────
        raw_transcript += f"\n\n[AI JOURNALIST]: {next_question}"
        scratchpad = session.get("live_scratchpad", {})
        scratchpad["current_module"]     = current_module_title
        scratchpad["current_topic"]      = current_topic_title
        scratchpad["current_module_idx"] = current_module_idx
        scratchpad["current_topic_idx"]  = current_topic_idx
        scratchpad["topic_status"]       = "IN_PROGRESS"
        # Reset lens tracking for the new topic
        scratchpad["topic_lens"]         = "understanding"

        self.supabase.table("interview_sessions").update({
            "raw_transcript":  raw_transcript,
            "live_scratchpad": scratchpad
        }).eq("id", session_id).execute()

        return {
            "question":           next_question,
            "current_module":     current_module_title,
            "current_topic":      current_topic_title,
            "topic_ready":        True,
            "next_engine":        "TOPIC_KNOWLEDGE_EXPLORATION",
            "phase_complete":     False
        }

        return {
            "question":           next_question,
            "current_module":     current_module_title,
            "current_topic":      current_topic_title,
            "topic_ready":        True,
            "next_engine":        "TOPIC_KNOWLEDGE_EXPLORATION",
            "phase_complete":     False
        }

    # =========================================================================
    # PHASE 7-11 — TOPIC EXPLORATION & TRANSITION ENGINE (DEPTH-FIRST)
    # =========================================================================
    # Guides the expert through 5 natural educational lenses per topic:
    #   1. understanding (Concept & Breakdown)
    #   2. teaching      (Action Items & References)
    #   3. failure       (Common Mistakes & Edge Cases)
    #   4. experience    (Stories & Heuristics)
    #   5. mastery       (Evaluation Path)
    #
    # Evaluates coverage per turn, checks gaps, transitions, and extracts
    # structured JSON on topic completion.
    # =========================================================================

    async def topic_exploration_turn(
        self,
        session_id: str,
        expert_answer: str
    ) -> Dict[str, Any]:
        """
        Process one turn of Block 4 Topic Exploration.
        Evaluates coverage, manages gaps, transitions lenses, and extracts knowledge on completion.

        Returns:
          {
            "question":           str | None,
            "current_module":     str,
            "current_topic":      str,
            "current_lens":       str,
            "lens_complete":      bool,
            "topic_complete":     bool,
            "phase_complete":     bool
          }
        """
        # ── 1. Fetch session + expert ─────────────────────────────────────
        session_res = self.supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Session not found.")
        session = session_res.data[0]
        expert  = await self._get_expert(session["expert_id"])

        # ── 2. Append answer & load state ─────────────────────────────────
        raw_transcript = session.get("raw_transcript", "").strip()
        raw_transcript += f"\n\n[EXPERT]: {expert_answer}"

        scratchpad       = session.get("live_scratchpad", {})
        current_module   = scratchpad.get("current_module", "")
        current_topic    = scratchpad.get("current_topic", "")
        current_lens     = scratchpad.get("topic_lens", "understanding")

        LENS_SEQUENCE = ["understanding", "teaching", "failure", "experience", "mastery"]

        def _parse_json(content: str) -> dict:
            cl = content.strip()
            if "```json" in cl:
                cl = cl.split("```json")[1].split("```")[0].strip()
            cl = re.sub(r',\s*([}\]])', r'\1', cl)
            try:
                return json.loads(cl)
            except Exception:
                return {}

        conv_history = self._build_conversation_history(raw_transcript, max_turns=6)

        # ── 3. PHASE 8: Check Knowledge Coverage (FAST) ────────────────────
        lens_complete = False
        coverage_data = {}
        try:
            cov_res = await self.llm_fast.ainvoke(
                KNOWLEDGE_COVERAGE_PROMPT.format(
                    current_topic=current_topic,
                    current_lens=current_lens,
                    conversation_history=conv_history,
                    expert_answer=expert_answer
                )
            )
            coverage_data = _parse_json(cov_res.content)
            lens_complete = bool(coverage_data.get("lens_complete", False))
        except Exception as e:
            logger.warning(f"Phase 8 coverage check failed: {e}")

        # ── 4. PHASE 10: Double check for gaps if coverage says complete ──
        gap_detected = False
        gap_question = None
        if lens_complete:
            try:
                gap_res = await self.llm.ainvoke(
                    KNOWLEDGE_GAP_MANAGER_PROMPT.format(
                        current_topic_title=current_topic,
                        current_lens=current_lens,
                        transcript=raw_transcript,
                        coverage_status=json.dumps(coverage_data)
                    )
                )
                gap_data     = _parse_json(gap_res.content)
                gap_detected = bool(gap_data.get("gap_detected", False))
                gap_question = gap_data.get("recovery_question", "")
            except Exception as e:
                logger.warning(f"Phase 10 gap check failed: {e}")

        # ── 5. PROCESS OUTCOMES ───────────────────────────────────────────
        
        # Scenario A: Lens has a gap -> Ask gap question, stay on lens
        if lens_complete and gap_detected and gap_question:
            raw_transcript += f"\n\n[AI JOURNALIST]: {gap_question}"
            self.supabase.table("interview_sessions").update({
                "raw_transcript": raw_transcript
            }).eq("id", session_id).execute()

            return {
                "question":           gap_question,
                "current_module":     current_module,
                "current_topic":      current_topic,
                "current_lens":       current_lens,
                "lens_complete":      False,
                "topic_complete":     False,
                "phase_complete":     False
            }

        # Scenario B: Lens is complete & no gaps -> Transition lens or topic
        if lens_complete and not gap_detected:
            current_lens_idx = LENS_SEQUENCE.index(current_lens)
            
            # Sub-Scenario B1: Move to next lens of the same topic
            if current_lens_idx + 1 < len(LENS_SEQUENCE):
                next_lens = LENS_SEQUENCE[current_lens_idx + 1]
                scratchpad["topic_lens"] = next_lens

                # Phase 11 transition prompt
                transition_q = f"Let's move to the next lens: {next_lens}."
                try:
                    trans_res = await self.llm.ainvoke(
                        TOPIC_TRANSITION_PROMPT.format(
                            course_title=expert.get("course_title", ""),
                            completed_module=current_module,
                            completed_topic=current_topic,
                            completed_stage=current_lens,
                            next_module=current_module,
                            next_topic=current_topic,
                            next_stage=next_lens,
                            conversation_history=self._build_conversation_history(raw_transcript, max_turns=4)
                        )
                    )
                    trans_data = _parse_json(trans_res.content)
                    reflection  = trans_data.get("reflection", "").strip()
                    question    = trans_data.get("question", "").strip()
                    if reflection and question:
                        transition_q = f"{reflection} {question}"
                    elif question:
                        transition_q = question
                except Exception as e:
                    logger.warning(f"Phase 11 lens transition generation failed: {e}")

                raw_transcript += f"\n\n[AI JOURNALIST]: {transition_q}"
                self.supabase.table("interview_sessions").update({
                    "raw_transcript":  raw_transcript,
                    "live_scratchpad": scratchpad
                }).eq("id", session_id).execute()

                return {
                    "question":           transition_q,
                    "current_module":     current_module,
                    "current_topic":      current_topic,
                    "current_lens":       next_lens,
                    "lens_complete":      True,
                    "topic_complete":     False,
                    "phase_complete":     False
                }

            # Sub-Scenario B2: All lenses complete -> Extract knowledge + complete topic!
            else:
                # Phase 9: Tacit Knowledge Extraction
                extracted_knowledge = {}
                try:
                    ext_res = await self.llm.ainvoke(
                        TACIT_KNOWLEDGE_EXTRACTION_PROMPT.format(
                            current_topic_title=current_topic,
                            transcript=raw_transcript
                        )
                    )
                    extracted_knowledge = _parse_json(ext_res.content)
                except Exception as e:
                    logger.warning(f"Phase 9 knowledge extraction failed: {e}")

                # Load current blueprint and write extracted knowledge to this topic in-place
                cb_res = self.supabase.table("curriculum_blueprints").select("*").eq("expert_id", session["expert_id"]).execute()
                if cb_res.data:
                    blueprint = cb_res.data[0]
                    course_modules = blueprint.get("course_modules", [])
                    
                    # Search and update in-place
                    for module in course_modules:
                        for topic in module.get("topics", []):
                            if topic.get("topic_title", "").lower() == current_topic.lower():
                                topic["concept"]          = extracted_knowledge.get("concept", "")
                                topic["breakdown"]        = extracted_knowledge.get("breakdown", "")
                                topic["constraints"]      = extracted_knowledge.get("constraints", "")
                                topic["edge_cases"]       = extracted_knowledge.get("edge_cases", "")
                                topic["action_items"]     = extracted_knowledge.get("action_items", [])
                                topic["common_mistakes"]   = extracted_knowledge.get("common_mistakes", [])
                                topic["evaluation_path"]   = extracted_knowledge.get("evaluation_path", "")
                                topic["expert_heuristic"] = extracted_knowledge.get("expert_heuristic", "")
                                topic["reference_guides"]  = extracted_knowledge.get("reference_guides", [])
                                topic["expert_story"]     = extracted_knowledge.get("expert_story", "")
                                break

                    # Persist blueprint
                    try:
                        self.supabase.table("curriculum_blueprints").update({
                            "course_modules": course_modules
                        }).eq("expert_id", session["expert_id"]).execute()
                        logger.info(f"Phase 9: saved fully enriched topic '{current_topic}'")
                    except Exception as e:
                        logger.error(f"Failed to persist topic enrichment: {e}")

                # Clear topic status and initialize next topic
                scratchpad["topic_status"] = "COMPLETE"
                self.supabase.table("interview_sessions").update({
                    "raw_transcript":  raw_transcript,
                    "live_scratchpad": scratchpad
                }).eq("id", session_id).execute()

                # Trigger auto-initialization for the next topic
                next_init = await self.topic_initialization_turn(session_id=session_id)
                return {
                    "question":           next_init["question"],
                    "current_module":     next_init["current_module"],
                    "current_topic":      next_init["current_topic"],
                    "current_lens":       "understanding",
                    "lens_complete":      True,
                    "topic_complete":     True,
                    "phase_complete":     next_init["phase_complete"]
                }

        # Scenario C: Lens not complete -> generate standard follow-up question
        next_question = f"Can you expand on the {current_lens} side of {current_topic}?"
        try:
            exp_res = await self.llm.ainvoke(
                EXPERT_UNDERSTANDING_PROMPT.format(
                    course_title=expert.get("course_title", ""),
                    current_module_title=current_module,
                    current_topic_title=current_topic,
                    current_lens=current_lens,
                    conversation_history=conv_history,
                    expert_answer=expert_answer
                )
            )
            exp_data = _parse_json(exp_res.content)
            reflection = str(exp_data.get("reflection", "")).strip()
            question   = str(exp_data.get("next_question") or exp_data.get("question") or "").strip()
            if reflection and question:
                next_question = f"{reflection} {question}"
            elif question:
                next_question = question
            elif reflection:
                next_question = reflection
        except Exception as e:
            logger.warning(f"Phase 7 Expert Understanding Engine failed: {e}")

        raw_transcript += f"\n\n[AI JOURNALIST]: {next_question}"
        self.supabase.table("interview_sessions").update({
            "raw_transcript":  raw_transcript,
            "live_scratchpad": scratchpad
        }).eq("id", session_id).execute()

        return {
            "question":           next_question,
            "current_module":     current_module,
            "current_topic":      current_topic,
            "current_lens":       current_lens,
            "lens_complete":      False,
            "topic_complete":     False,
            "phase_complete":     False
        }

    async def _handle_lock_transition(
        self,
        session_id: str,
        script: dict,
        module_backlog: list,
        current_scratchpad: dict
    ) -> dict:
        # 1. Load blueprint from DB
        session_res = self.supabase.table("interview_sessions").select("expert_id").eq("id", session_id).execute()
        expert_id = session_res.data[0]["expert_id"]
        cb_res = self.supabase.table("curriculum_blueprints").select("*").eq("expert_id", expert_id).execute()
        course_modules = cb_res.data[0].get("course_modules", [])

        # 2. Extract preserved journalistic modules (Module 1, 2) and Philosophy (Module 4)
        preserved_backlog = []
        philosophy_module = None
        for mod in module_backlog:
            m_title = mod.get("module_title", "")
            if "Personal Stories" in m_title or "Challenges" in m_title:
                preserved_backlog.append(mod)
            elif "Philosophy" in m_title:
                philosophy_module = mod

        # 3. Construct dynamic modules
        dynamic_modules = []
        for idx, module_data in enumerate(course_modules):
            topics_list = []
            for t_idx, topic_data in enumerate(module_data.get("topics", [])):
                topics_list.append({
                    "topic_id": f"m_dynamic_{idx}_t{t_idx}",
                    "topic_title": topic_data["topic_title"],
                    "opener_question": "",  # Will be dynamically populated
                    "exploration_vectors": [],
                    "target_objectives": ["concept", "breakdown", "edge_cases", "constraints", "action_items", "evaluation_path", "common_mistakes", "expert_story", "expert_heuristic"],
                    "estimated_minutes": 10
                })
            dynamic_modules.append({
                "module_id": f"m_dynamic_{idx}",
                "module_title": module_data["module_title"],
                "tracking_mode": "extraction",
                "topics": topics_list
            })

        # 4. Initialize first topic opener question
        init_res = await self.topic_initialization_turn(session_id)
        if init_res.get("topic_ready") and dynamic_modules:
            dynamic_modules[0]["topics"][0]["opener_question"] = init_res["question"]

        # 5. Save updated script
        new_backlog = preserved_backlog + dynamic_modules
        if philosophy_module:
            new_backlog.append(philosophy_module)
        script["module_backlog"] = new_backlog

        # 6. Update scratchpad pointers to point to the first dynamic module
        current_scratchpad["current_module_idx"] = len(preserved_backlog)
        current_scratchpad["current_topic_idx"] = 0
        current_scratchpad["curriculum_locked"] = True
        # Reset topic status for the new topic
        current_scratchpad["topic_status"] = "IN_PROGRESS"
        current_scratchpad["topic_lens"] = "understanding"

        self.supabase.table("interview_sessions").update({
            "script": script,
            "live_scratchpad": current_scratchpad
        }).eq("id", session_id).execute()

        # Advance pointer on frontend
        return {
            "question": init_res["question"],
            "decision": {
                "action": "next_script_question",
                "intent": "advance",
                "reasoning": "Curriculum locked! Initializing the first topic."
            },
            "updated_script": script
        }

    async def live_turn(self, session_id: str, expert_answer: str, request_data: Dict[str, Any] = None) -> Dict[str, Any]:




        session_res = self.supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Active session not found.")
        session = session_res.data[0]
        expert = await self._get_expert(session["expert_id"])
        
        # 1. Update Transcript
        current_transcript = session.get("raw_transcript", "").strip()
        new_transcript = current_transcript
        
        if request_data and request_data.get("tangent_count", -1) == 0:
            script_q = request_data.get("current_script_question", "").strip()
            if script_q and not new_transcript.endswith(script_q):
                new_transcript += f"\n\n[AI JOURNALIST]: {script_q}"
                
        new_transcript += f"\n\n[EXPERT]: {expert_answer}"
        
        # Pull State
        current_scratchpad = session.get("live_scratchpad", {})
        knowledge_nodes = current_scratchpad.get("knowledge_nodes", [])
        
        tangent_depth = current_scratchpad.get("tangent_depth", 0)
        tangent_budget = current_scratchpad.get("tangent_budget", 2)
        extra_budget_used = current_scratchpad.get("extra_budget_used", 0)
        
        # ── MODULE / TOPIC POINTER (replaces old current_block string) ──
        # These integer indices are the authoritative position in the interview arc.
        # They are stored in live_scratchpad and advanced here when a topic is complete.
        script = session.get("script", {})
        module_backlog = script.get("module_backlog", [])
        
        m_idx = current_scratchpad.get("current_module_idx", 0)
        t_idx = current_scratchpad.get("current_topic_idx", 0)
        
        # ── SYNC WITH FRONTEND OVERRIDE ──
        # If the frontend sent an active_block, verify if it aligns with the internal indices.
        # If there is a mismatch (e.g. manual skip/jump), search for the matching indices.
        if request_data and request_data.get("active_block"):
            req_block = request_data["active_block"]
            found_match = False
            for m_i, mod in enumerate(module_backlog):
                mod_title = mod.get("module_title", "")
                for t_i, top in enumerate(mod.get("topics", [])):
                    top_title = top.get("topic_title", "")
                    combined_title = f"{mod_title} - {top_title}"
                    # Match clean combined strings
                    if req_block == combined_title or req_block in combined_title or combined_title in req_block:
                        if m_i != m_idx or t_i != t_idx:
                            logger.info(f"Syncing internal index pointer: frontend={req_block} -> indices({m_i}, {t_i})")
                            m_idx = m_i
                            t_idx = t_i
                            # Reset tangent counters for the new block
                            tangent_depth = 0
                            extra_budget_used = 0
                        found_match = True
                        break
                if found_match:
                    break
        
        # Resolve current module and topic objects
        current_module_obj = module_backlog[m_idx] if m_idx < len(module_backlog) else {}
        current_topic_obj = current_module_obj.get("topics", [])[t_idx] if t_idx < len(current_module_obj.get("topics", [])) else {}
        
        current_module = current_module_obj.get("module_title", "Unknown Module")
        current_topic = current_topic_obj.get("topic_title", "General Exploration")
        topic_id = current_topic_obj.get("topic_id", f"m{m_idx}_t{t_idx}")
        
        # target_objectives = the 7-slot component names that must be extracted for this topic
        target_objectives = current_topic_obj.get("target_objectives") or ["concept", "expert_story", "expert_heuristic"]
        
        # tracking_mode: "journalistic" = free-flowing, no rigid component gates
        #                "extraction"   = strict 7-slot coverage tracking (Module 3 + Day 2+)
        tracking_mode = current_module_obj.get("tracking_mode", "journalistic")
        
        # Keep backward-compat current_block string for legacy prompts that still use it
        current_block = f"{current_module} - {current_topic}"
        
        block_rules = {
            "required": target_objectives,
            "exit_requirements": target_objectives,
            "minimum_completion": len(target_objectives)
        }
        
        # Helpers
        def _parse_json(content):
            cl = content.strip()
            if "```json" in cl:
                cl = cl.split("```json")[1].split("```")[0].strip()
            cl = re.sub(r',\s*([}\]])', r'\1', cl)
            try:
                return json.loads(cl)
            except Exception:
                return {}

        # ── DYNAMIC CURRICULUM DISCOVERY & EXPLORATION INTERCEPTION ──
        is_curriculum_discovery = "curriculum discovery" in current_module.lower() or "curriculum discovery" in current_topic.lower()
        if is_curriculum_discovery:
            phase1_complete = current_scratchpad.get("phase1_complete", False)
            phase2_complete = current_scratchpad.get("phase2_complete", False)
            phase3_complete = current_scratchpad.get("phase3_complete", False)
            phase4_complete = current_scratchpad.get("phase4_complete", False)
            curriculum_locked = current_scratchpad.get("curriculum_locked", False)

            if not phase1_complete:
                res = await self.course_discovery_turn(session_id, expert_answer)
                if res.get("phase_complete"):
                    current_scratchpad["phase1_complete"] = True
                    bridge_question = (
                        "I think we've got a really clear picture of the journey you're taking learners on and who it's designed for. "
                        "Now I'm curious about how you would naturally organize that journey. "
                        "If you stepped back and looked at the entire course, what would you say are the major stages or modules that learners progress through?"
                    )
                    # Append bridge question to transcript
                    new_transcript = session.get("raw_transcript", "").strip()
                    new_transcript += f"\n\n[AI JOURNALIST]: {bridge_question}"
                    
                    self.supabase.table("interview_sessions").update({
                        "live_scratchpad": current_scratchpad,
                        "raw_transcript": new_transcript
                    }).eq("id", session_id).execute()
                    
                    return {
                        "question": bridge_question,
                        "decision": {
                            "action": "follow_tangent",
                            "intent": "substantive",
                            "reasoning": "Transitioning from CDA Phase 1 to Phase 2 (Module Discovery)"
                        },
                        "updated_script": script
                    }
                else:
                    return {
                        "question": res.get("question"),
                        "decision": {
                            "action": "follow_tangent",
                            "intent": "substantive",
                            "reasoning": "CDA Phase 1: Course Discovery"
                        },
                        "updated_script": script
                    }

            elif not phase2_complete:
                res = await self.module_discovery_turn(session_id, expert_answer)
                if res.get("phase_complete"):
                    current_scratchpad["phase2_complete"] = True
                    discovered_mods = res.get("discovered_modules", [])
                    modules_str = ", ".join([f'"{m}"' for m in discovered_mods])
                    first_module = discovered_mods[0] if discovered_mods else "the first module"
                    
                    bridge_question = (
                        f"Excellent. We have mapped out the core modules of the course: {modules_str}. "
                        f"Now, before we decide what lessons belong inside them, I want to explore why each module exists. "
                        f"Let's start with the first milestone: \"{first_module}\". "
                        f"In the context of the overall course, what role does this stage play in the learner's journey?"
                    )
                    # Append bridge question to transcript
                    new_transcript = session.get("raw_transcript", "").strip()
                    new_transcript += f"\n\n[AI JOURNALIST]: {bridge_question}"
                    
                    self.supabase.table("interview_sessions").update({
                        "live_scratchpad": current_scratchpad,
                        "raw_transcript": new_transcript
                    }).eq("id", session_id).execute()
                    
                    return {
                        "question": bridge_question,
                        "decision": {
                            "action": "follow_tangent",
                            "intent": "substantive",
                            "reasoning": "Transitioning from CDA Phase 2 to Phase 3 (Module Enrichment)"
                        },
                        "updated_script": script
                    }
                else:
                    return {
                        "question": res.get("question"),
                        "decision": {
                            "action": "follow_tangent",
                            "intent": "substantive",
                            "reasoning": "CDA Phase 2: Module Discovery"
                        },
                        "updated_script": script
                    }

            elif not phase3_complete:
                res = await self.module_enrichment_turn(session_id, expert_answer)
                if res.get("phase_complete"):
                    current_scratchpad["phase3_complete"] = True
                    # Find first module title
                    cb_res = self.supabase.table("curriculum_blueprints").select("course_modules").eq("expert_id", expert["id"]).execute()
                    first_module_title = "the first module"
                    if cb_res.data and cb_res.data[0].get("course_modules"):
                        first_module_title = cb_res.data[0]["course_modules"][0].get("module_title", "the first module")
                    
                    bridge_question = (
                        f"That gives us a really rich context for why these modules exist and what outcomes they deliver. "
                        f"Let's now map out the specific lessons. "
                        f"For our first module, \"{first_module_title}\": if you were to divide it into its major topics or lessons, what would naturally come first?"
                    )
                    # Append bridge question to transcript
                    new_transcript = session.get("raw_transcript", "").strip()
                    new_transcript += f"\n\n[AI JOURNALIST]: {bridge_question}"
                    
                    self.supabase.table("interview_sessions").update({
                        "live_scratchpad": current_scratchpad,
                        "raw_transcript": new_transcript
                    }).eq("id", session_id).execute()
                    
                    # Initialize topic discovery scratchpad states
                    current_scratchpad["topic_discovery_module_idx"] = 0
                    current_scratchpad["topic_discovery_topics"] = []
                    current_scratchpad["topic_reflection_asked"] = False
                    self.supabase.table("interview_sessions").update({
                        "live_scratchpad": current_scratchpad
                    }).eq("id", session_id).execute()
                    
                    return {
                        "question": bridge_question,
                        "decision": {
                            "action": "follow_tangent",
                            "intent": "substantive",
                            "reasoning": "Transitioning from CDA Phase 3 to Phase 4 (Topic Discovery)"
                        },
                        "updated_script": script
                    }
                else:
                    return {
                        "question": res.get("question"),
                        "decision": {
                            "action": "follow_tangent",
                            "intent": "substantive",
                            "reasoning": "CDA Phase 3: Module Enrichment"
                        },
                        "updated_script": script
                    }

            elif not phase4_complete:
                res = await self.topic_discovery_turn(session_id, expert_answer)
                if res.get("phase_complete"):
                    current_scratchpad["phase4_complete"] = True
                    self.supabase.table("interview_sessions").update({
                        "live_scratchpad": current_scratchpad
                    }).eq("id", session_id).execute()
                    val_res = await self.validate_and_lock_curriculum(session_id)
                    if val_res.get("curriculum_locked"):
                        return await self._handle_lock_transition(session_id, script, module_backlog, current_scratchpad)
                    else:
                        question = val_res.get("validation_report", {}).get("recovery_question", "Let's review the curriculum layout.")
                        return {
                            "question": question,
                            "decision": {
                                "action": "follow_tangent",
                                "intent": "substantive",
                                "reasoning": "CDA Phase 5: Validation Failed"
                            },
                            "updated_script": script
                        }
                return {
                    "question": res.get("question"),
                    "decision": {
                        "action": "follow_tangent",
                        "intent": "substantive",
                        "reasoning": "CDA Phase 4: Topic Discovery"
                    },
                    "updated_script": script
                }

            elif not curriculum_locked:
                val_res = await self.validate_and_lock_curriculum(session_id)
                if val_res.get("curriculum_locked"):
                    return await self._handle_lock_transition(session_id, script, module_backlog, current_scratchpad)
                else:
                    next_state = val_res.get("next_state", "COURSE_DISCOVERY")
                    recovery_q = val_res.get("validation_report", {}).get("recovery_question", "Let's review the curriculum layout.")
                    
                    if next_state == "COURSE_DISCOVERY":
                        current_scratchpad["phase1_complete"] = False
                        current_scratchpad["phase2_complete"] = False
                        current_scratchpad["phase3_complete"] = False
                        current_scratchpad["phase4_complete"] = False
                    elif next_state == "MODULE_DISCOVERY":
                        current_scratchpad["phase2_complete"] = False
                        current_scratchpad["phase3_complete"] = False
                        current_scratchpad["phase4_complete"] = False
                    elif next_state == "MODULE_ENRICHMENT":
                        current_scratchpad["phase3_complete"] = False
                        current_scratchpad["phase4_complete"] = False
                    elif next_state == "TOPIC_DISCOVERY":
                        current_scratchpad["phase4_complete"] = False

                    self.supabase.table("interview_sessions").update({
                        "live_scratchpad": current_scratchpad
                    }).eq("id", session_id).execute()

                    return {
                        "question": recovery_q,
                        "decision": {
                            "action": "follow_tangent",
                            "intent": "substantive",
                            "reasoning": f"CDA Phase 5: Validation Failed. Routing to {next_state}"
                        },
                        "updated_script": script
                    }

        # ── BLOCK 4 INTERCEPTION (DYNAMIC MODULES) ──
        is_dynamic_module = current_module_obj.get("module_id", "").startswith("m_dynamic_")
        if is_dynamic_module:
            topic_status = current_scratchpad.get("topic_status")
            if topic_status != "IN_PROGRESS":
                init_res = await self.topic_initialization_turn(session_id, expert_answer)
                if init_res.get("phase_complete"):
                    # All dynamic topics complete! Transition to Philosophy.
                    preserved_count = 2
                    dynamic_count = len([m for m in module_backlog if m.get("module_id", "").startswith("m_dynamic_")])
                    next_m_idx = preserved_count + dynamic_count
                    
                    current_scratchpad["current_module_idx"] = next_m_idx
                    current_scratchpad["current_topic_idx"] = 0
                    self.supabase.table("interview_sessions").update({
                        "live_scratchpad": current_scratchpad
                    }).eq("id", session_id).execute()
                    
                    return {
                        "question": "Great job covering all curriculum topics! Let's reflect on your core philosophy.",
                        "decision": {
                            "action": "next_script_question",
                            "intent": "advance",
                            "reasoning": "All dynamic topics completed. Advancing to Philosophy."
                        },
                        "updated_script": script
                    }
                return {
                    "question": init_res.get("question"),
                    "decision": {
                        "action": "follow_tangent",
                        "intent": "substantive",
                        "reasoning": "Initializing topic"
                    },
                    "updated_script": script
                }
            else:
                exp_res = await self.topic_exploration_turn(session_id, expert_answer)
                if exp_res.get("topic_complete"):
                    if exp_res.get("phase_complete"):
                        # Transition to Philosophy
                        preserved_count = 2
                        dynamic_count = len([m for m in module_backlog if m.get("module_id", "").startswith("m_dynamic_")])
                        next_m_idx = preserved_count + dynamic_count
                        
                        current_scratchpad["current_module_idx"] = next_m_idx
                        current_scratchpad["current_topic_idx"] = 0
                        self.supabase.table("interview_sessions").update({
                            "live_scratchpad": current_scratchpad
                        }).eq("id", session_id).execute()
                        
                        return {
                            "question": "Great job covering all curriculum topics! Let's reflect on your core philosophy.",
                            "decision": {
                                "action": "next_script_question",
                                "intent": "advance",
                                "reasoning": "All dynamic topics completed. Advancing to Philosophy."
                            },
                            "updated_script": script
                        }
                    
                    # Read the updated pointers and return next_script_question
                    new_m_idx = current_scratchpad.get("current_module_idx", m_idx)
                    new_t_idx = current_scratchpad.get("current_topic_idx", t_idx)
                    
                    session_res = self.supabase.table("interview_sessions").select("script").eq("id", session_id).execute()
                    updated_script = session_res.data[0]["script"] if session_res.data else script
                    
                    return {
                        "question": exp_res.get("question"),
                        "decision": {
                            "action": "next_script_question",
                            "intent": "advance",
                            "reasoning": "Topic completed. Advancing to next topic."
                        },
                        "updated_script": updated_script
                    }
                
                return {
                    "question": exp_res.get("question"),
                    "decision": {
                        "action": "follow_tangent",
                        "intent": "substantive",
                        "reasoning": f"Exploring lens: {exp_res.get('current_lens')}"
                    },
                    "updated_script": script
                }

        # ── PHASE 1.5: DRIFT DETECTOR ──
        drift_score = 1.0
        try:

            # Prioritize the actual question currently displayed on the frontend
            last_question = "Unknown"
            if request_data and request_data.get("current_script_question"):
                last_question = request_data["current_script_question"].strip()
            elif current_transcript:
                lines = current_transcript.split("\n")
                ai_lines = [l for l in lines if l.startswith("[AI JOURNALIST]:")]
                if ai_lines:
                    last_question = ai_lines[-1].replace("[AI JOURNALIST]:", "").strip()

            res_drift = await self.llm_fast.ainvoke(DRIFT_DETECTOR_PROMPT.format(
                current_topic=current_topic,
                current_question=last_question,
                expert_answer=expert_answer
            ))
            drift_data = _parse_json(res_drift.content)
            drift_score = float(drift_data.get("alignment_score", 1.0))
        except Exception as e:
            logger.warning(f"Phase 1.5 failed: {e}")

        # ── PHASE 2: INSIGHT DETECTION ──
        try:
            res_detect = await self.llm_fast.ainvoke(INSIGHT_DETECTION_PROMPT.format(expert_answer=expert_answer))
            detected_insights = _parse_json(res_detect.content)
            if isinstance(detected_insights, dict):
                detected_insights = [detected_insights]
        except Exception as e:
            logger.warning(f"Phase 2 failed: {e}")
            detected_insights = []

        # ── PHASE 3: INSIGHT PRIORITIZATION ──
        try:
            res_prioritize = await self.llm_fast.ainvoke(INSIGHT_PRIORITIZATION_PROMPT.format(
                current_block=current_block,
                current_topic=current_topic,
                detected_insights=json.dumps(detected_insights),
                coverage_status="Unknown",
                previous_follow_ups="[]"
            ))
            ranked_insights = _parse_json(res_prioritize.content)
            if isinstance(ranked_insights, dict):
                ranked_insights = [ranked_insights]
            top_insight = ranked_insights[0] if ranked_insights else {}
        except Exception as e:
            logger.warning(f"Phase 3 failed: {e}")
            top_insight = {}

        # ── PHASE 4: KNOWLEDGE GRAPH UPDATE ──
        try:
            if top_insight:
                res_kg = await self.llm_fast.ainvoke(KNOWLEDGE_GRAPH_UPDATE_PROMPT.format(
                    current_module=current_module,
                    current_topic=current_topic,
                    detected_insight=top_insight.get("evidence", ""),
                    insight_type=top_insight.get("insight_type", ""),
                    confidence_score=top_insight.get("score", 0.0),
                    existing_nodes=json.dumps([n.get("content") for n in knowledge_nodes[-5:]])
                ))
                new_node = _parse_json(res_kg.content)
                if new_node and isinstance(new_node, dict):
                    knowledge_nodes.append(new_node)
        except Exception as e:
            logger.warning(f"Phase 4 failed: {e}")

        # ── PHASE 5: DETERMINISTIC COVERAGE (extraction mode only) ──
        topic_completion_count = 0
        block_completion_count = 0
        coverage_map = {}
        if tracking_mode == "extraction":
            # Journalistic modules (1/2/4) flow naturally — no slot-by-slot gating.

            # ── PHASE 5A: CURRICULUM EXTRACTOR (runs for Curriculum Discovery module) ──
            # When the expert is in the Curriculum Discovery module, detect if they
            # just listed modules or topics and update curriculum_blueprint in scratchpad.
            is_curriculum_discovery = "curriculum discovery" in current_module.lower()
            curriculum_blueprint = current_scratchpad.get("curriculum_blueprint", {
                "modules_listed": False,
                "modules": [],
                "current_module_being_drilled": 0,
                "all_topics_extracted": False
            })

            if is_curriculum_discovery:
                try:
                    last_question = ""
                    lines = new_transcript.strip().split("\n")
                    ai_lines = [l for l in lines if l.startswith("[AI JOURNALIST]:")]
                    if ai_lines:
                        last_question = ai_lines[-1].replace("[AI JOURNALIST]:", "").strip()

                    res_curr = await self.llm_fast.ainvoke(CURRICULUM_EXTRACTOR_PROMPT.format(
                        expert_answer=expert_answer,
                        conversation_history=self._build_conversation_history(new_transcript, max_turns=4),
                        curriculum_blueprint=json.dumps(curriculum_blueprint),
                        last_question=last_question
                    ))
                    curr_data = _parse_json(res_curr.content)

                    if curr_data.get("confidence") in ["HIGH", "MEDIUM"]:
                        if curr_data.get("extracted_type") == "modules" and curr_data.get("modules"):
                            # 1. Update Curriculum Blueprint in Scratchpad
                            new_modules = [
                                {"title": m, "topics": [], "topics_done": False}
                                for m in curr_data["modules"]
                            ]
                            curriculum_blueprint["modules"] = new_modules
                            curriculum_blueprint["modules_listed"] = True
                            curriculum_blueprint["current_module_being_drilled"] = 0

                            # 2. Dynamic Backlog Insertion
                            preserved_backlog = []
                            philosophy_module = None
                            for mod in module_backlog:
                                m_id = mod.get("module_id", "")
                                if m_id.startswith("m_dynamic_"):
                                    continue
                                if "Philosophy" in mod.get("module_title", "") or "Philosophy & Mental Models" in mod.get("module_title", ""):
                                    philosophy_module = mod
                                    continue
                                preserved_backlog.append(mod)

                            dynamic_modules = []
                            for idx, m in enumerate(curr_data["modules"]):
                                dynamic_modules.append({
                                    "module_id": f"m_dynamic_{idx}",
                                    "module_title": f"CURRICULUM: {m}",
                                    "tracking_mode": "extraction",
                                    "topics": []
                                })

                            new_backlog = preserved_backlog + dynamic_modules
                            if philosophy_module:
                                new_backlog.append(philosophy_module)
                            script["module_backlog"] = new_backlog

                        elif curr_data.get("extracted_type") == "topics" and curr_data.get("topics"):
                            # 1. Update Curriculum Blueprint in Scratchpad
                            target_mod = curr_data.get("topics_for_module", "")
                            for mod in curriculum_blueprint.get("modules", []):
                                if target_mod and target_mod.lower() in mod["title"].lower():
                                    mod["topics"] = curr_data["topics"]
                                    mod["topics_done"] = True
                                    break
                            
                            # Advance drill pointer to next module without topics
                            for i, mod in enumerate(curriculum_blueprint.get("modules", [])):
                                if not mod["topics_done"]:
                                    curriculum_blueprint["current_module_being_drilled"] = i
                                    break
                            else:
                                curriculum_blueprint["all_topics_extracted"] = True

                            # 2. Dynamic Backlog Insertion
                            for mod in module_backlog:
                                m_title = mod.get("module_title", "")
                                if m_title.startswith("CURRICULUM:"):
                                    core_title = m_title.replace("CURRICULUM:", "").strip()
                                    if target_mod and target_mod.lower() in core_title.lower():
                                        new_topics = []
                                        for t_idx, t_name in enumerate(curr_data["topics"]):
                                            new_topics.append({
                                                "topic_id": f"{mod['module_id']}_t{t_idx}",
                                                "topic_title": t_name,
                                                "opener_question": f"Let's drill into the topic '{t_name}' under '{core_title}'. What is the core concept of this topic?",
                                                "exploration_vectors": [
                                                    f"Explore the core definition of {t_name}",
                                                    f"Ask for a concrete breakdown of how it works in production",
                                                    f"Get the expert's rule of thumb or heuristic for {t_name}"
                                                ],
                                                "target_objectives": ["concept", "breakdown", "edge_cases", "constraints", "action_items", "evaluation_path", "common_mistakes", "expert_story", "expert_heuristic"],
                                                "estimated_minutes": 10
                                            })
                                        mod["topics"] = new_topics
                                        break

                    current_scratchpad["curriculum_blueprint"] = curriculum_blueprint
                except Exception as e:
                    logger.warning(f"Phase 5A curriculum extractor failed: {e}")

                # Coverage for curriculum topics: check blueprint completeness
                if is_curriculum_discovery:
                    # Module 3 (Curriculum Discovery) contains exactly 1 topic: Core Pillars & Module Brainstorming.
                    # We stay on this topic to list modules and topics, and only advance once the full tree is mapped out.
                    mods = curriculum_blueprint.get("modules", [])
                    if curriculum_blueprint.get("all_topics_extracted") or (mods and all(m["topics_done"] for m in mods)):
                        block_completion_count = block_rules["minimum_completion"]
                        topic_completion_count = block_rules["minimum_completion"]
                        coverage_map = {k: True for k in target_objectives}
                    elif curriculum_blueprint.get("modules_listed"):
                        # Modules listed but topics not done yet
                        block_completion_count = 1  # partial
                        coverage_map = {k: False for k in target_objectives}

            if not is_curriculum_discovery:
                # Standard extraction: run COVERAGE_AND_GAP_PROMPT for non-curriculum topics
                try:
                    res_coverage = await self.llm_fast.ainvoke(COVERAGE_AND_GAP_PROMPT.format(
                        current_block=current_block,
                        current_topic=current_topic,
                        required_targets=json.dumps(block_rules["required"]),
                        knowledge_nodes=json.dumps(knowledge_nodes),
                        conversation_history=self._build_conversation_history(new_transcript, max_turns=6)
                    ))
                    coverage_map = _parse_json(res_coverage.content)

                    for key in block_rules["exit_requirements"]:
                        if coverage_map.get(key) is True:
                            block_completion_count += 1
                            topic_completion_count += 1
                except Exception as e:
                    logger.warning(f"Phase 5 (extraction) failed: {e}")
        # In journalistic mode: coverage_map stays empty, counts stay 0.
        # Advancement is driven by tangent_budget instead.

        # ── DETERMINISTIC ORCHESTRATOR ──
        # EXTRACTION mode: stay on topic until ALL 7 components satisfied.
        # JOURNALISTIC mode: advance on tangent budget (natural conversation flow).
        
        next_action = "CONTINUE_TOPIC"
        
        if tracking_mode == "extraction":
            all_components_done = (block_completion_count >= block_rules["minimum_completion"])
        else:
            # Journalistic: advance after natural tangent budget exhaustion
            # (approximately 4-6 exchanges per topic, then move on)
            all_components_done = (tangent_depth >= tangent_budget)
        
        if all_components_done:
            # ── Advance topic pointer ──
            topics_in_module = current_module_obj.get("topics", [])
            if t_idx + 1 < len(topics_in_module):
                next_action = "MOVE_TOPIC"
                new_t_idx = t_idx + 1
                new_m_idx = m_idx
            elif m_idx + 1 < len(module_backlog):
                next_action = "MOVE_MODULE"
                new_m_idx = m_idx + 1
                new_t_idx = 0
            else:
                next_action = "END_INTERVIEW"
                new_m_idx = m_idx
                new_t_idx = t_idx
                
        elif drift_score < DRIFT_RULES["drift_threshold"]:
            next_action = "RETURN_TO_TOPIC"
            
        elif tracking_mode == "extraction" and tangent_depth >= tangent_budget:
            # Extraction mode + budget exhausted but components not done: keep asking
            next_action = "ASK_GAP_QUESTION"
            
        elif top_insight.get("score", 0) >= TANGENT_BUDGET_RULES["high_value_threshold"] and extra_budget_used < TANGENT_BUDGET_RULES["max_high_value_followups"]:
            tangent_budget += TANGENT_BUDGET_RULES["extra_for_high_value"]
            extra_budget_used += 1
            next_action = "EXPLORE_INSIGHT"
            
        else:
            next_action = "ASK_GAP_QUESTION"

        # ── Persist topic/component progress to topic_progress table ──
        try:
            components_bool = {k: (coverage_map.get(k) is True) for k in target_objectives}
            self.supabase.table("topic_progress").upsert({
                "session_id": session_id,
                "expert_id": session["expert_id"],
                "module_id": current_module_obj.get("module_id", f"m{m_idx}"),
                "module_title": current_module,
                "topic_id": topic_id,
                "topic_title": current_topic,
                "components": components_bool,
                "is_complete": all_components_done
            }, on_conflict="session_id,topic_id").execute()
        except Exception as e:
            logger.warning(f"topic_progress upsert failed: {e}")

        # ── Execute advancement if topic/module complete ──
        if next_action in ["MOVE_TOPIC", "MOVE_MODULE", "END_INTERVIEW"]:
            # Update scratchpad with new pointer position
            current_scratchpad["current_module_idx"] = new_m_idx
            current_scratchpad["current_topic_idx"] = new_t_idx
            current_scratchpad["tangent_depth"] = 0
            current_scratchpad["tangent_budget"] = TANGENT_BUDGET_RULES["base_budget"]
            current_scratchpad["extra_budget_used"] = 0
            current_scratchpad["knowledge_nodes"] = knowledge_nodes
            
            self.supabase.table("interview_sessions").update({
                "raw_transcript": new_transcript,
                "live_scratchpad": current_scratchpad,
                "script": script
            }).eq("id", session_id).execute()
            
            # Return null question → frontend uses next topic's opener_question from script
            return {
                "question": None,
                "decision": {
                    "action": "next_script_question",
                    "intent": "advance",
                    "next_module_idx": new_m_idx,
                    "next_topic_idx": new_t_idx,
                    "reasoning": f"{next_action}: all {block_completion_count}/{block_rules['minimum_completion']} components satisfied for '{current_topic}'"
                },
                "updated_script": script
            }

        # If not advancing: increment tangent depth and generate follow-up question
        current_scratchpad["current_module_idx"] = m_idx
        current_scratchpad["current_topic_idx"] = t_idx
        current_scratchpad["tangent_depth"] = tangent_depth + 1
        current_scratchpad["tangent_budget"] = tangent_budget
        current_scratchpad["extra_budget_used"] = extra_budget_used
        current_scratchpad["knowledge_nodes"] = knowledge_nodes

        # PHASE 6: ADAPTIVE CURIOSITY ENGINE
        # When inside Curriculum Discovery, override coverage_gaps with curriculum state.
        # The curiosity engine knows which module to ask about topics for next.
        curriculum_blueprint = current_scratchpad.get("curriculum_blueprint", {})
        is_curriculum_discovery = "curriculum discovery" in current_module.lower()

        if is_curriculum_discovery and curriculum_blueprint.get("modules_listed"):
            # Build a structured hint for the curiosity engine about what to ask next
            mods = curriculum_blueprint.get("modules", [])
            drill_idx = curriculum_blueprint.get("current_module_being_drilled", 0)
            pending = [m["title"] for m in mods if not m["topics_done"]]
            done = [m["title"] for m in mods if m["topics_done"]]
            curriculum_context = json.dumps({
                "modules_confirmed": [m["title"] for m in mods],
                "topics_done_for": done,
                "next_module_to_drill": mods[drill_idx]["title"] if drill_idx < len(mods) else None,
                "still_need_topics_for": pending
            })
            coverage_gaps_payload = json.dumps(pending)  # pending modules = the gaps
        else:
            curriculum_context = "{}"
            coverage_gaps_payload = json.dumps([k for k, v in coverage_map.items() if not v])

        try:
            res_curiosity = await self.llm.ainvoke(ADAPTIVE_CURIOSITY_PROMPT.format(
                current_module=current_module,
                current_topic=current_topic,
                conversation_history=self._build_conversation_history(new_transcript, max_turns=6),
                reflection_output=top_insight.get("evidence", ""),
                detected_insights=json.dumps(detected_insights),
                knowledge_graph=json.dumps(knowledge_nodes),
                coverage_gaps=coverage_gaps_payload,
                engagement_signals=f"Drift Score: {drift_score} | Curriculum Blueprint: {curriculum_context}"
            ))
            curiosity_data = _parse_json(res_curiosity.content)
            reflection = curiosity_data.get("reflection", "").strip()
            question = curiosity_data.get("question", "").strip()
            if reflection and question:
                next_question = f"{reflection} {question}"
            else:
                next_question = question or reflection or "Can you expand on that?"
        except Exception as e:
            logger.warning(f"Phase 6 failed: {e}")
            next_question = "Can you expand on that?"

        if next_question:
            new_transcript += f"\n\n[AI JOURNALIST]: {next_question}"
            
        self.supabase.table("interview_sessions").update({
            "raw_transcript": new_transcript,
            "live_scratchpad": current_scratchpad,
            "script": script
        }).eq("id", session_id).execute()

        # Map internal action to frontend expected action string
        frontend_action = "follow_tangent"
        if next_action == "RETURN_TO_TOPIC":
            frontend_action = "redirect_to_script"

        return {
            "question": next_question,
            "decision": {
                "action": frontend_action,
                "intent": "substantive",
                "current_module_idx": m_idx,
                "current_topic_idx": t_idx,
                "components_done": block_completion_count,
                "components_total": block_rules["minimum_completion"],
                "coverage": coverage_map,
                "reasoning": f"Action: {next_action}. Drift: {drift_score}. Budget: {tangent_depth+1}/{tangent_budget}"
            },
            "updated_script": script
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

    def _compute_server_tangent_count(self, transcript: str, client_count: int = 0) -> int:
        """
        FIX 1.3 — Count consecutive AI follow-ups since the last [SCRIPT] boundary.

        BUG FIXED: the previous version broke on [EXPERT]: lines, which appear
        between every AI question. This reset the counter to 1 on every turn.
        Now ONLY [SCRIPT]: boundaries reset the count.

        Falls back to client_count if no [SCRIPT]: boundary has ever been stamped
        (i.e., early in the session before the first script advance).
        """
        if not transcript:
            return client_count  # Trust frontend before first boundary exists

        lines = [l.strip() for l in transcript.split("\n") if l.strip()]
        found_boundary = False
        count = 0

        for line in reversed(lines):
            if line.startswith("[AI JOURNALIST]:"):
                count += 1
            elif line.startswith("[SCRIPT]:"):
                # Only SCRIPT markers are real reset boundaries
                found_boundary = True
                break
            # [EXPERT]: is NOT a boundary — skip it and keep counting

        if not found_boundary:
            # No [SCRIPT]: stamps yet — use max of server/client as safety net
            return max(count, client_count)

        return count

    def _validate_and_persist_block(self, session: dict, session_id: str, requested_block: str) -> str:
        """
        FIX 2.3 — Validates block transitions and persists current_block server-side.
        Prevents the frontend from skipping blocks or sending invalid block strings.
        Allows same block or one step forward only.
        """
        current_block = session.get("current_block") or "Block 1"

        def extract_num(s: str) -> int:
            m = re.search(r'Block\s*(\d+)', s)
            return int(m.group(1)) if m else 1

        requested_num = extract_num(requested_block)
        current_num = extract_num(current_block)

        # Allow skips during testing, but reject going backward or invalid
        if requested_num < current_num:
            logger.warning(
                f"Backward block movement rejected: '{current_block}' → '{requested_block}'. "
                f"Holding at '{current_block}'."
            )
            return current_block

        # Reject completely invalid block strings
        if requested_num < 1 or requested_num > 5:
            logger.warning(f"Invalid block number '{requested_block}', holding at '{current_block}'.")
            return current_block

        # Persist if changed
        if requested_num != current_num:
            try:
                self.supabase.table("interview_sessions").update(
                    {"current_block": requested_block}
                ).eq("id", session_id).execute()
            except Exception as e:
                logger.warning(f"Could not persist current_block (column may not exist yet): {e}")

        return requested_block

    def _compute_session_saturation(self, transcript: str, scratchpad: dict = None) -> Tuple[int, int, str]:
        """
        Computes real-time session saturation (0-100%) based on token weight, turn count, and satisfied objectives.
        """
        if not transcript:
            return 0, 0, "Empty transcript"
            
        expert_turns = [l for l in transcript.split("\n") if l.strip().startswith("[EXPERT]:")]
        turn_count = len(expert_turns)
        
        # 1. Token pressure: optimal chapter session ceiling = 8,000 chars (~2,000 tokens / ~10 rich Q&As)
        token_pressure = min(1.0, len(transcript) / 8000.0)
        
        # 2. Objectives complete rate (target 4 objectives per chapter block)
        sat_objs = (scratchpad or {}).get("satisfied_objectives", [])
        obj_rate = min(1.0, len(sat_objs) / 4.0)
        
        # Dynamic Saturation: Whichever vector is highest drives the session boundary
        composite = (0.65 * token_pressure) + (0.50 * obj_rate)
        score = min(1.0, max(token_pressure, obj_rate, composite))
        sat_pct = int(score * 100)
        return sat_pct, turn_count, f"Tokens={int(len(transcript)/4)}, Objs={len(sat_objs)}, Sat={sat_pct}%"

    def _compute_phase_objectives(self, active_block: str, transcript: str, current_scratchpad: dict = None) -> Tuple[str, List[str]]:
        """
        FIX 2.2 — Computes a structured objective map for the current block.

        Returns:
            Tuple of (formatted_string_for_prompt, list_of_missing_objective_labels)

        Uses multi-word signal phrases only (not single words like 'if', 'first')
        and scans ONLY expert speech to prevent false positives from AI questions.
        """

        # ── Per-block objectives — hybrid signals (2-3 word, natural speech) ──
        # IMPORTANT: These must match how experts ACTUALLY speak, not formal phrases.
        # Each objective gets 8+ variants to prevent false-negative (objective never completing).
        BLOCK_OBJECTIVES: Dict[str, List[Dict]] = {
            "Block 1": [
                {"id": "B1-O1", "label": "Origin Story",
                 "signals": [
                     "got into", "how i got", "why i", "career began", "started out",
                     "my first job", "began my", "i started", "i got into", "fell into",
                     "came from", "background is", "worked in", "used to be"
                 ]},
                {"id": "B1-O2", "label": "First Defining Experience",
                 "signals": [
                     "first time", "early on", "very early", "when i was", "starting out",
                     "fresh out", "in the beginning", "back then", "years ago",
                     "one of my first", "that early", "when i started"
                 ]},
                {"id": "B1-O3", "label": "Self-Description / Persona",
                 "signals": [
                     "i tend to", "my approach", "i think of", "i see myself",
                     "i'm very", "i am someone", "i would say i", "i care about",
                     "i value", "i focus on", "my style", "i like to", "i prefer",
                     "i believe in", "for me it", "i'm someone"
                 ]},
                {"id": "B1-O4", "label": "Initial Learning Challenges",
                 "signals": [
                     "hardest part", "struggled with", "learning curve", "took me a while",
                     "confusing", "didn't understand", "frustrating", "challenge when learning",
                     "when i was learning", "trying to figure out", "stuck on",
                     "setback", "mistake", "went wrong", "blew up", "tough",
                     "didn't know", "had no idea", "figured out", "lesson learned",
                     "the hard way", "that taught me", "it broke", "failure",
                     "i failed", "cost us", "i messed", "embarrassing",
                     "shaped my", "looking back", "back then", "early mistake",
                     "took a while", "painful", "burned by", "bit me"
                 ]},
            ],
            "Block 2": [
                {"id": "B2-O1", "label": "Major Challenges",
                 "signals": [
                     "hardest", "toughest", "biggest challenge", "struggled", "difficult",
                     "really hard", "wasn't easy", "challenging", "it was tough",
                     "took me a while", "the problem was", "not easy"
                 ]},
                {"id": "B2-O2", "label": "Failures",
                 "signals": [
                     "failed", "mistake", "went wrong", "blew up", "disaster",
                     "regret", "should have", "i messed", "that was bad",
                     "we lost", "it broke", "embarrassing", "cost us", "burned"
                 ]},
                {"id": "B2-O3", "label": "Belief Changes",
                 "signals": [
                     "changed my mind", "realized", "turning point", "pivoted",
                     "shifted", "rethought", "now i think", "used to think",
                     "changed how", "moment i", "that's when", "i no longer",
                     "i stopped", "i started thinking", "assumption", "unlearn"
                 ]},
                {"id": "B2-O4", "label": "Decision Frameworks",
                 "signals": [
                     "how i decide", "framework", "mental model", "approach to",
                     "strategy", "process for", "way i think about", "evaluate",
                     "criteria", "weigh the", "trade-offs", "structured approach"
                 ]},
                {"id": "B2-O5", "label": "Pattern Recognition",
                 "signals": [
                     "warning signs", "red flags", "notice today", "looking back",
                     "missed early", "recognize", "pattern", "signs that",
                     "usually means", "tends to be", "predict"
                 ]},
                {"id": "B2-O6", "label": "Learning Process",
                 "signals": [
                     "how i learned", "resource", "documentation", "studied",
                     "tutorial", "course", "reading about", "practicing",
                     "building projects", "hands-on"
                 ]},
            ],
            "Block 3": [
                {"id": "B3-O1", "label": "Module Overview",
                 "signals": [
                     "module", "section", "part", "chapter", "pillar",
                     "unit", "area", "cover", "break it", "split it",
                     "organized into", "structure it", "would include", "focus of this"
                 ]},
                {"id": "B3-O2", "label": "Specific Topics Identified",
                 "signals": [
                     "first topic", "next topic", "then we cover", "concept of",
                     "we dive into", "specifics of", "topics include", "we will talk about"
                 ]},
            ],
            "Block 5": [
                {"id": "B5-O1", "label": "Overarching Mental Model",
                 "signals": [
                     "mental model", "framework", "philosophy", "way i think",
                     "how i approach", "lens", "perspective", "mindset",
                     "fundamentally", "at the core", "underlying"
                 ]},
                {"id": "B5-O2", "label": "Advice to Beginners",
                 "signals": [
                     "advice", "tell beginners", "if i could go back", "starting out",
                     "to someone new", "for newcomers", "to someone just",
                     "what i wish", "don't make", "i'd tell"
                 ]},
                {"id": "B5-O3", "label": "Contrarian Belief",
                 "signals": [
                     "most people think", "contrary", "unpopular", "actually",
                     "disagree", "not what people", "people are wrong", "overrated",
                     "underrated", "opposite of", "i push back"
                 ]},
            ]
        }

        # Determine which block map to use
        block_key = "Block 1"
        for k in ["Block 1", "Block 2", "Block 3", "Block 4", "Block 5"]:
            if k in active_block:
                block_key = k
                break

        # ── BLOCK 4 DYNAMIC NODE CHECKLIST ─────────────────────────────
        # If Block 4, ignore the text signals and build the objective map
        # dynamically from the scratchpad's node_checklist for the current topic.
        if block_key == "Block 4":
            current_scratchpad = current_scratchpad or {}
            checklist = current_scratchpad.get("node_checklist", {})
            current_topic = current_scratchpad.get("current_topic", "General Topic")

            # Default slots if nothing is in scratchpad yet
            slots = {
                "concept": False, "breakdown": False, "action_items": False,
                "reference_guides": False, "edge_cases": False,
                "constraints": False, "evaluation_path": False
            }

            if checklist:
                # Grab the topic checklist if it exists, or the first one available
                topic_data = checklist.get(current_topic)
                if not topic_data and len(checklist) > 0:
                    topic_data = list(checklist.values())[0]
                if topic_data:
                    slots.update(topic_data)

            formatted_lines = [f"PHASE OBJECTIVE MAP — Block 4 (Node Extraction)"]
            formatted_lines.append(f"CURRENT TOPIC: {current_topic}")
            formatted_lines.append(
                "You are extracting deep knowledge nodes for this specific topic.\n"
                "Your next question MUST target the FIRST MISSING [✗] slot.\n"
                "Do NOT ask about anything else."
            )
            
            missing_labels = []
            slot_labels = {
                "concept": "Concept",
                "breakdown": "Breakdown",
                "action_items": "Action Items",
                "reference_guides": "Reference Guides",
                "edge_cases": "Edge Cases",
                "constraints": "Constraints",
                "evaluation_path": "Evaluation Path"
            }

            for slot_key, label in slot_labels.items():
                is_complete = slots.get(slot_key, False)
                if is_complete:
                    formatted_lines.append(f"✓ COMPLETE: {label}")
                else:
                    formatted_lines.append(f"✗ MISSING: {label}")
                    missing_labels.append(label)

            if not missing_labels:
                formatted_lines.append("\nSTATUS: ALL SLOTS COMPLETE. RETURN INTENT='skip'.")
            else:
                formatted_lines.append("\nSTATUS: ACTION REQUIRED. Target the FIRST [✗] slot.")

            return "\n".join(formatted_lines), missing_labels
        # ───────────────────────────────────────────────────────────────

        objectives = BLOCK_OBJECTIVES.get(block_key, [])
        if not objectives:
            return "(No phase objectives defined for this block.)", []

        # FIX 2.2 — Extract ONLY expert speech to prevent AI question text
        # from triggering false-positive objective completion signals
        expert_lines = []
        for line in (transcript or "").split("\n"):
            line = line.strip()
            if line.startswith("[EXPERT]:"):
                expert_lines.append(line[len("[EXPERT]:"):].strip().lower())
        expert_text = " ".join(expert_lines)

        result_lines = [f"PHASE OBJECTIVE MAP — {active_block}"]
        result_lines.append(
            "This map shows which interview objectives for the current block are COMPLETE vs MISSING.\n"
            "You MUST use this map as your compass. Your next question MUST target the highest-priority MISSING objective.\n"
            "Do NOT follow technical details from the last answer unless they directly help complete a MISSING objective.\n"
        )

        complete_count = 0
        missing_objectives: List[str] = []

        for obj in objectives:
            satisfied = any(signal in expert_text for signal in obj["signals"])
            
            # Persistent memory check: if the LLM evaluator marked this complete previously, it STAYS complete.
            sat_list = (current_scratchpad or {}).get("satisfied_objectives", [])
            if obj["label"] in sat_list:
                satisfied = True
            
            # FIX: Automatic fulfillment based on Brain B's scratchpad state
            # If we are looking for Specific Topics, and Brain B has already populated
            # the node_checklist with at least one topic, force this to TRUE so we don't get stuck.
            if obj["label"] == "Specific Topics Identified":
                checklist = (current_scratchpad or {}).get("node_checklist", {})
                if checklist and len(checklist) > 0:
                    satisfied = True

            status = "✓ COMPLETE" if satisfied else "✗ MISSING"
            if satisfied:
                complete_count += 1
            else:
                missing_objectives.append(obj["label"])
            result_lines.append(f"  [{obj['id']}] {obj['label']} — {status}")

        result_lines.append("")
        if missing_objectives:
            result_lines.append(
                f"ACTION REQUIRED: {len(missing_objectives)} objective(s) are still MISSING.\n"
                f"Your next question MUST target one of: {', '.join(missing_objectives[:3])}.\n"
                f"IGNORE the last answer's technical details. Generate a question for a MISSING objective."
            )
        else:
            result_lines.append(
                "ALL OBJECTIVES COMPLETE for this block. "
                "Return intent='skip' to allow the system to advance to the next block."
            )

        return "\n".join(result_lines), missing_objectives

    async def background_embed_turn(self, session_id: str, expert_answer: str, embeddings_model: Any):
        """Phase 2: Extract semantic essence from the latest turn and store in vector memory."""
        try:
            # Check if answer has substance
            res = self.llm.invoke(BACKGROUND_EMBED_FILTER_PROMPT.format(expert_answer=expert_answer))
            essence = res.content.strip()
            
            if essence.upper() == "SKIP" or not essence:
                logger.info("Background embedding skipped - conversational filler detected.")
                return
                
            # It has substance, get the session to find the live_transcript_source_id
            session_res = self.supabase.table("interview_sessions").select("live_transcript_source_id").eq("id", session_id).execute()
            if not session_res.data:
                return
            source_id = session_res.data[0].get("live_transcript_source_id")
            if not source_id:
                logger.warning(f"No knowledge source attached to session {session_id} for embedding.")
                return
                
            # Embed the essence
            emb = embeddings_model.embed_query(essence)
            
            # Save to knowledge_chunks
            self.supabase.table("knowledge_chunks").insert({
                "source_id": source_id,
                "content": essence,
                "embedding": emb,
                "location_marker": f"Session {session_id} extract"
            }).execute()
            logger.info(f"Background embedding complete for session {session_id}")
        except Exception as e:
            logger.error(f"Error in background_embed_turn: {e}")

    async def background_update_scratchpad(self, session_id: str):
        """
        DEPRECATED — scratchpad is now updated synchronously inside live_turn()
        using llm_fast before the prompt is built. This method is kept as a
        no-op so any lingering background_tasks.add_task() calls don't crash.
        """
        logger.debug(f"background_update_scratchpad called for {session_id} — no-op (now sync)")

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

            # Extract persona specifics for expert_profile
            persona = tutor_data.get("tutor_persona", {})
            update_ep["teaching_style"] = persona.get("teaching_style", ep.get("teaching_style", ""))
            update_ep["linguistic_fingerprint"] = persona.get("linguistic_fingerprint", ep.get("linguistic_fingerprint", {}))
            update_ep["system_prompt"] = persona.get("system_prompt", ep.get("system_prompt", ""))

            # Upsert Curriculum Blueprints (store raw modules blob for backward compat)
            course_structure = tutor_data.get("course_structure", {})
            modules = course_structure.get("modules", [])
            cb_res = self.supabase.table("curriculum_blueprints").select("*").eq("expert_id", expert["id"]).execute()
            if not cb_res.data:
                self.supabase.table("curriculum_blueprints").insert({
                    "expert_id": expert["id"],
                    "session_id": session_id,
                    "course_modules": modules
                }).execute()
            else:
                cb = cb_res.data[0]
                curriculum_locked = session.get("live_scratchpad", {}).get("curriculum_locked", False)
                if not curriculum_locked:
                    existing_modules = cb.get("course_modules", [])
                    merged_modules = existing_modules + modules
                    self.supabase.table("curriculum_blueprints").update({
                        "course_modules": merged_modules,
                        "session_id": session_id,
                        "iteration_last_updated": session["iteration_number"]
                    }).eq("id", cb["id"]).execute()
                else:
                    self.supabase.table("curriculum_blueprints").update({
                        "session_id": session_id,
                        "iteration_last_updated": session["iteration_number"]
                    }).eq("id", cb["id"]).execute()

        # Save updated expert profile
        self.supabase.table("expert_profile").update(update_ep).eq("id", ep["id"]).execute()

        # ── Build the clean unified knowledge output ──────────────────────────
        persona_out = tutor_data.get("tutor_persona", {}) if tutor_data else {}
        course_out = tutor_data.get("course_structure", {}) if tutor_data else {}

        knowledge_output = {
            "persona": {
                "system_prompt": persona_out.get("system_prompt", ""),
                "teaching_style": persona_out.get("teaching_style", ""),
                "linguistic_fingerprint": persona_out.get("linguistic_fingerprint", {})
            },
            "course": course_out,
            "tacit_insights": general_data.get("tacit_insights", []),
            "war_stories": general_data.get("war_stories", []),
            "mental_models": general_data.get("mental_models", []),
            "pattern_breaks": general_data.get("pattern_breaks", []),
            "structured_tacit_notes": tutor_data.get("structured_tacit_notes", []) if tutor_data else []
        }
        # ─────────────────────────────────────────────────────────────────────

        # ── 3. Granular Insights Extraction (For Verification Dashboard) ──
        try:
            res_insights = await self.llm.ainvoke(INSIGHTS_SYNTHESIS_PROMPT.format(
                expert_name=expert.get('name', 'Expert'),
                expert_domain=expert.get('domain', 'Domain'),
                transcript=transcript
            ))
            cl_ins = res_insights.content.strip()
            if "```json" in cl_ins:
                cl_ins = cl_ins.split("```json")[1].split("```")[0].strip()
            insights_list = json.loads(cl_ins)
            
            # Insert insights into expert_tacit_insights
            if isinstance(insights_list, list):
                # Delete any existing pending insights for this session to prevent duplicates
                self.supabase.table("expert_tacit_insights").delete().eq("session_id", session_id).execute()
                
                insert_rows = []
                for item in insights_list:
                    classification = item.get("classification", "").strip().lower()
                    allowed_classes = [
                        'mental_model', 'heuristic', 'decision_rule', 'failure_pattern', 
                        'misconception', 'tradeoff', 'evaluation_signal', 'constraint', 
                        'belief', 'turning_point', 'workflow', 'tool_or_technology'
                    ]
                    if classification not in allowed_classes:
                        if classification == "tool":
                            classification = "tool_or_technology"
                        else:
                            classification = "heuristic"
                            
                    insert_rows.append({
                        "expert_id": expert["id"],
                        "session_id": session_id,
                        "classification": classification,
                        "title": item.get("title", "Tacit Insight"),
                        "content": item.get("content", ""),
                        "expert_quote": item.get("expert_quote", ""),
                        "status": "pending"
                    })
                if insert_rows:
                    self.supabase.table("expert_tacit_insights").insert(insert_rows).execute()
                    logger.info(f"Successfully populated {len(insert_rows)} insights in expert_tacit_insights")
        except Exception as e:
            logger.error(f"Failed to populate granular tacit insights: {e}")

        session_synthesis = {
            "general": general_data, 
            "tutor": tutor_data, 
            "knowledge_output": knowledge_output,
            "raw_transcript": transcript
        }
        self.supabase.table("interview_sessions").update({
            "status": "synthesized",
            "session_synthesis": session_synthesis
        }).eq("id", session_id).execute()

        # Insert into the new tacit_knowledge_reports table
        try:
            report_title = f"Knowledge Report - Iteration {iteration_number}"
            self.supabase.table("tacit_knowledge_reports").insert({
                "expert_id": expert["id"],
                "session_id_fk": session_id,
                "report_title": report_title,
                "structured_tacit_notes": {
                    "tacit_insights": general_data.get("tacit_insights", []),
                    "war_stories": general_data.get("war_stories", []),
                    "mental_models": general_data.get("mental_models", []),
                    "pattern_breaks": general_data.get("pattern_breaks", []),
                    "tutor_notes": tutor_data.get("structured_tacit_notes", []) if tutor_data else []
                },
                "persona_snapshot": knowledge_output["persona"],
                "course_structure": knowledge_output["course"]
            }).execute()
        except Exception as e:
            logger.error(f"Failed to insert into tacit_knowledge_reports: {e}")

        return {"status": "success", "knowledge_output": knowledge_output}

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
        
        # Run AI Automated Validation on extracted resources
        ai_open_loops = hw_data.get("ai_open_loops", [])
        for loop in ai_open_loops:
            resource_mentioned = loop.get("resource_mentioned")
            what_expert_claimed = loop.get("what_expert_claimed")
            
            if resource_mentioned and what_expert_claimed:
                try:
                    val_res = self.llm.invoke(RESOURCE_VALIDATION_PROMPT.format(
                        resource_mentioned=resource_mentioned,
                        what_expert_claimed=what_expert_claimed
                    ))
                    val_cl = val_res.content.strip()
                    if "```json" in val_cl: val_cl = val_cl.split("```json")[1].split("```")[0].strip()
                    val_data = json.loads(val_cl)
                    loop["validation_status"] = val_data.get("validation_status", "Needs Human Review")
                    loop["validation_reasoning"] = val_data.get("validation_reasoning", "")
                except Exception as e:
                    logger.error(f"Failed to validate resource {resource_mentioned}: {e}")
                    loop["validation_status"] = "Needs Human Review"
                    loop["validation_reasoning"] = "Validation failed due to server error."
        
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
         hw= hw_res.data[0] if hw_res.data else{}
            
      
        previous_day = hw.get("iteration_number", 1)
        current_day = previous_day + 1

        block_2_first_q = "Let's dive into our second block: how do your core architectural decisions hold up under extreme production load?"
try:
sess_res = self.supabase.table("interview_sessions").select("script").eq("expert_id", expert_id).order("iteration_number", desc=True).limit(2).execute()
if sess_res.data:
for s in sess_res.data:
if s.get("script"):
arc = s["script"].get("interview_arc") or s["script"]
if isinstance(arc, dict):
sorted_blocks = sorted(arc.items(), key=lambda x: int(re.search(r'\d+', x[0]).group(0)) if re.search(r'\d+', x[0]) else 99)
if len(sorted_blocks) > 1:
b2_data = sorted_blocks[1][1]
if isinstance(b2_data, dict) and b2_data.get("questions") and len(b2_data["questions"]) > 0:
block_2_first_q = b2_data["questions"][0].get("question_text", block_2_first_q)
break
except Exception as e:
logger.warning(f"Could not extract block 2 first question: {e}")
        
        res = self.llm.invoke(FLYWHEEL_BRIDGE_PROMPT.format(
            expert_name=expert.get('name', ''),
            expert_domain=expert.get('domain', ''),
            previous_day=previous_day,
            current_day=current_day,
            archetype_rules=get_archetype_rules(archetype),
            ai_open_loops=json.dumps(hw.get("ai_open_loops", []), indent=2),
            human_manual_notes=hw.get("human_manual_notes", ""),
            block_2_first_question=block_2_first_q
        ))
        cl = res.content.strip()
        if "```json" in cl: cl = cl.split("```json")[1].split("```")[0].strip()
        bridge_data = json.loads(cl)
        
        return bridge_data

# =====================================================================
# PHASE 6+ — BACKGROUND VERIFICATION ENGINE & EVIDENCE CROSS-REFERENCING
# =====================================================================

EVIDENCE_VERIFICATION_PROMPT = """You are the AI Journalist Background Verification Engine.
An expert previously claimed the following during an interview session:
CLAIM / TOPIC: {loop_topic}
RESOURCE MENTIONED: {resource_mentioned}
WHAT EXPERT CLAIMED: {what_expert_claimed}

The expert has now submitted supporting evidence ({material_type}):
SUBMITTED CONTENT / EXTRACT:
{content_or_url}

Your task is to analyze the submitted evidence against the expert's prior claim.
Return valid JSON matching this exact structure:
{{
  "verification_status": "verified",
  "authenticity_score": 0.95,
  "key_findings": ["Finding 1", "Finding 2"],
  "inconsistencies_or_gaps": ["Any gaps or contradictions spotted"],
  "suggested_followup_probe": "A sharp, evidence-backed question to ask the expert in the next session"
}}
Note: "verification_status" must be one of: "verified", "inconsistent", or "needs_review".
Return ONLY valid JSON.
"""

VERIFICATION_QUESTION_PROMPT = """You are the AI Journalist.
The expert submitted supporting evidence for several open loops between interview sessions.
Our Background Verification Engine analyzed the evidence and generated these verification insights:
{verification_insights_json}

Your task is to generate 1 to 2 sharp, highly contextual follow-up verification questions to present to the expert before or during the next interview phase.
These questions should validate their learning journey, explore any gaps/inconsistencies, or solidify their tacit knowledge blueprint.

Return valid JSON:
{{
  "verification_questions": [
    {{
      "question_text": "...",
      "target_topic": "...",
      "rationale": "..."
    }}
  ]
}}
Return ONLY valid JSON.
"""

# Monkey-patching additional methods onto InterviewDomain
async def _submit_evidence_method(self, expert_id: str, session_id: str, iteration_number: int, loop_topic: str, material_type: str, content_or_url: str, resource_mentioned: str = "", what_expert_claimed: str = "") -> Dict[str, Any]:
    # Insert record into submitted_materials table (handle fallback if table not created)
    try:
        mat_res = self.supabase.table("submitted_materials").insert({
            "expert_id": expert_id,
            "session_id": session_id,
            "iteration_number": iteration_number,
            "loop_topic": loop_topic,
            "material_type": material_type,
            "content_or_url": content_or_url,
            "verification_status": "verifying"
        }).execute()
        mat_id = mat_res.data[0]["id"] if mat_res.data else "MAT-" + str(int(datetime.now().timestamp()))
    except Exception as e:
        logger.warning(f"submitted_materials table missing or error: {e}")
        mat_id = "MAT-DEMO-" + str(int(datetime.now().timestamp()))

    return {
        "status": "received",
        "material_id": mat_id,
        "loop_topic": loop_topic,
        "resource_mentioned": resource_mentioned,
        "what_expert_claimed": what_expert_claimed
    }

async def _background_verify_evidence_method(self, material_id: str, loop_topic: str, material_type: str, content_or_url: str, resource_mentioned: str, what_expert_claimed: str):
    logger.info(f"Background Verification Engine running for evidence: {material_id}")
    try:
        res = self.llm.invoke(EVIDENCE_VERIFICATION_PROMPT.format(
            loop_topic=loop_topic,
            resource_mentioned=resource_mentioned,
            what_expert_claimed=what_expert_claimed,
            material_type=material_type,
            content_or_url=content_or_url[:3000]
        ))
        cl = res.content.strip()
        if "```json" in cl: cl = cl.split("```json")[1].split("```")[0].strip()
        insights = json.loads(cl)

        status = insights.get("verification_status", "verified")
        try:
            self.supabase.table("submitted_materials").update({
                "verification_status": status,
                "verification_insights": insights
            }).eq("id", material_id).execute()
        except Exception:
            pass
        logger.info(f"Evidence {material_id} verified with status: {status}")
    except Exception as e:
        logger.error(f"Background verification failed for {material_id}: {e}")

async def _generate_verification_questions_method(self, expert_id: str) -> List[Dict[str, Any]]:
    try:
        mats_res = self.supabase.table("submitted_materials").select("*").eq("expert_id", expert_id).neq("verification_status", "pending").execute()
        if not mats_res.data:
            return []
        
        insights_list = [m.get("verification_insights", {}) for m in mats_res.data if m.get("verification_insights")]
        if not insights_list:
            return []

        res = self.llm.invoke(VERIFICATION_QUESTION_PROMPT.format(
            verification_insights_json=json.dumps(insights_list, indent=2)
        ))
        cl = res.content.strip()
        if "```json" in cl: cl = cl.split("```json")[1].split("```")[0].strip()
        data = json.loads(cl)
        return data.get("verification_questions", [])
    except Exception as e:
        logger.error(f"Verification question generation error: {e}")
        return []

InterviewDomain.submit_evidence = _submit_evidence_method
InterviewDomain.background_verify_evidence = _background_verify_evidence_method
InterviewDomain.generate_verification_questions = _generate_verification_questions_method

