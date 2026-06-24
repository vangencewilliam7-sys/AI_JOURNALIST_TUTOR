import json
import re
import logging
from typing import Dict, Any, List, Tuple
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
    RESOURCE_VALIDATION_PROMPT,
    FLYWHEEL_BRIDGE_PROMPT,
    ARCHETYPE_CLASSIFIER_PROMPT,
    BACKGROUND_EMBED_FILTER_PROMPT,
    RETRIEVAL_GATE_PROMPT,
    SCRATCHPAD_UPDATE_PROMPT,
    OBJECTIVE_SATISFACTION_PROMPT,
    OBJECTIVE_REQUIREMENTS,
    COVERAGE_ENGINE_PROMPT,
    TOPIC_CONTROLLER_PROMPT
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

        # ── FIX 1.3 — Block validation (server-side, trusted) ────────────────
        requested_block = (request_data or {}).get("active_block", "Block 1: Personal Origin & Persona")
        active_block = self._validate_and_persist_block(session, session_id, requested_block)
        # ─────────────────────────────────────────────────────────────────────

        # 2. Get active script question
        current_script_question = (request_data or {}).get("current_script_question", "")
        if not current_script_question:
            current_script_question = "General domain exploration."

        # ── FIX 1.1 — Build transcript with boundary stamping ────────────────
        # The frontend sends tangent_count=0 when it just advanced the script.
        # We use this ONLY to stamp a [SCRIPT] boundary in the transcript so
        # the server-side tangent counter can detect topic resets reliably.
        client_tangent_count = int((request_data or {}).get("tangent_count", 0))
        current_transcript = session.get("raw_transcript", "")
        if client_tangent_count == 0 and current_transcript:
            # Frontend advanced to a new script question — stamp a boundary
            new_transcript = (
                current_transcript
                + f"\n\n[SCRIPT]: {current_script_question}"
                + f"\n\n[EXPERT]: {expert_answer}"
            )
        else:
            new_transcript = current_transcript + f"\n\n[EXPERT]: {expert_answer}"
        # ─────────────────────────────────────────────────────────────────────

        # ── FIX 1.3 — Server-side tangent count (browser-crash-proof) ────────
        tangent_count = self._compute_server_tangent_count(current_transcript, client_count=client_tangent_count)
        # Per-block tangent limits: how many AI follow-ups are allowed per script question
        _TANGENT_LIMITS = {
            "Block 1": 3,  # Origin stories — personal, need a bit of depth
            "Block 2": 4,  # Challenges & failures — rich stories, dig deeper
            "Block 3": 2,  # Course structure — list-based, keep tight
            "Block 4": 6,  # Deep topic extraction — intentionally deep
            "Block 5": 2,  # Mental models & wrap-up — concise
        }
        tangent_limit = 2  # default fallback
        for block_key, limit in _TANGENT_LIMITS.items():
            if block_key in active_block:
                tangent_limit = limit
                break
        pacing_warning = ""
        if tangent_count >= tangent_limit:
            pacing_warning = (
                f"WARNING: You have asked {tangent_count} follow-ups on this topic "
                f"(limit = {tangent_limit}). You MUST return intent='skip' now to advance."
            )
        # ─────────────────────────────────────────────────────────────────────

        # 3. Build conversation history sliding window
        conversation_history = self._build_conversation_history(current_transcript, max_turns=6)

        # ── FIX 1.1 — Sync scratchpad update (always fresh before the prompt) ─
        # Previously this ran in the background AFTER the response was sent,
        # so the AI always had stale memory. Now we update it synchronously
        # using the fast model before building the prompt.
        current_scratchpad = session.get("live_scratchpad", {})
        live_scratchpad_str = json.dumps(current_scratchpad, indent=2)  # fallback
        try:
            scratchpad_turns = self._build_conversation_history(
                current_transcript + f"\n\n[EXPERT]: {expert_answer}", max_turns=4
            )
            sp_res = self.llm_fast.invoke(SCRATCHPAD_UPDATE_PROMPT.format(
                current_scratchpad=json.dumps(current_scratchpad, indent=2),
                new_transcript=scratchpad_turns
            ))
            sp_cl = sp_res.content.strip()
            if "```json" in sp_cl:
                sp_cl = sp_cl.split("```json")[1].split("```")[0].strip()
            sp_cl = re.sub(r',\s*([}\]])', r'\1', sp_cl)
            updated_scratchpad = json.loads(sp_cl)
            # Persist immediately — next turn reads a fresh scratchpad
            self.supabase.table("interview_sessions").update(
                {"live_scratchpad": updated_scratchpad}
            ).eq("id", session_id).execute()
            live_scratchpad_str = json.dumps(updated_scratchpad, indent=2)
        except Exception as e:
            logger.warning(f"Sync scratchpad update failed, using prior state: {e}")
        # ─────────────────────────────────────────────────────────────────────

        # ── Phase Objective Map ───────────────────────────────────────────────
        script = session.get("script") or {}
        # FIX: Pass the newly synced scratchpad, not the stale one from the start of the turn
        final_scratchpad = locals().get("updated_scratchpad", current_scratchpad)
        phase_objectives_str, missing_objectives = self._compute_phase_objectives(
            active_block=active_block,
            transcript=current_transcript,
            current_scratchpad=final_scratchpad
        )
        # ─────────────────────────────────────────────────────────────────────

        # ── FIX 2.4 — Retrieval Gate with objective-anchored embedding ────────
        gate_res = self.llm_fast.invoke(RETRIEVAL_GATE_PROMPT.format(
            active_script_question=current_script_question,
            conversation_history=self._build_conversation_history(current_transcript, max_turns=2)
        ))

        retrieved_context = "None"
        if gate_res.content.strip().upper() == "YES" and self.embeddings_model:
            source_id = session.get("live_transcript_source_id")
            if source_id:
                # Anchor the retrieval to what we NEED next (missing objectives)
                # rather than what was just said — avoids retrieving more of the same topic
                retrieval_anchor = current_script_question
                if missing_objectives:
                    retrieval_anchor += " " + " ".join(missing_objectives[:2])
                try:
                    query_emb = self.embeddings_model.embed_query(retrieval_anchor)
                    rpc_res = self.supabase.rpc('match_knowledge_chunks', {
                        'query_embedding': query_emb,
                        'match_threshold': 0.7,
                        'match_count': 10
                    }).execute()
                    matches = [
                        r['content'] for r in rpc_res.data
                        if r.get('knowledge_sources', {}).get('id') == source_id
                    ]
                    if matches:
                        retrieved_context = "\n".join(matches)
                except Exception as e:
                    logger.error(f"Retrieval error: {e}")
        # ─────────────────────────────────────────────────────────────────────
        # ── MASTER INTERVIEW CONTROLLER (Block 3 & 4 only) ───────────────────
        # Block 1 & Block 2 are UNTOUCHED. This only runs for curriculum
        # discovery (Block 3) and topic extraction (Block 4).
        if active_block and ("Block 3" in active_block or "Block 4" in active_block):
            try:
                sp = locals().get("updated_scratchpad", current_scratchpad)
                node_checklist = sp.get("node_checklist", {})
                current_topic_name = sp.get("current_topic") or "Unknown"

                # Build curriculum map summary from scratchpad
                curriculum_map_str = json.dumps(node_checklist, indent=2) if node_checklist else "Not yet mapped."

                # Determine current module from scratchpad or script question
                current_module_name = sp.get("current_module") or current_script_question or "Unknown"

                # Coverage scores for current topic (Block 4 only)
                topic_node = node_checklist.get(current_topic_name, {})
                coverage_scores_str = json.dumps(
                    {k: v for k, v in topic_node.items() if k != "status"}, indent=2
                ) if topic_node else "N/A (Block 3 or no data yet)"

                topic_status = topic_node.get("status", "NOT_STARTED") if isinstance(topic_node, dict) else "NOT_STARTED"

                # Build module progress
                module_topics = [
                    f"{t}: {info.get('status', 'NOT_STARTED')}"
                    for t, info in node_checklist.items()
                    if isinstance(info, dict)
                ]
                module_progress_str = ", ".join(module_topics) if module_topics else "No topics tracked yet."

                ctrl_res = self.llm_fast.invoke(MASTER_INTERVIEW_CONTROLLER_PROMPT.format(
                    current_block=active_block,
                    current_module=current_module_name,
                    current_topic=current_topic_name,
                    topic_status=topic_status,
                    module_progress=module_progress_str,
                    curriculum_map=curriculum_map_str,
                    coverage_scores=coverage_scores_str
                ))
                ctrl_cl = ctrl_res.content.strip()
                if "```json" in ctrl_cl:
                    ctrl_cl = ctrl_cl.split("```json")[1].split("```")[0].strip()
                ctrl_cl = re.sub(r',\s*([}\]])', r'\1', ctrl_cl)
                ctrl_data = json.loads(ctrl_cl)

                ctrl_action = ctrl_data.get("action", "STAY_IN_TOPIC")
                ctrl_reason = ctrl_data.get("reasoning", "")
                logger.info(f"Master Controller [{active_block}]: {ctrl_action} — {ctrl_reason}")

                # If controller says to advance, return skip immediately
                if ctrl_action in ("NEXT_TOPIC", "NEXT_MODULE", "NEXT_BLOCK"):
                    self.supabase.table("interview_sessions").update(
                        {"raw_transcript": new_transcript}
                    ).eq("id", session_id).execute()
                    return {
                        "question": None,
                        "decision": {
                            "action": "next_script_question",
                            "intent": "skip",
                            "reasoning": f"Master Controller: {ctrl_action} — {ctrl_reason}",
                            "controller_action": ctrl_action,
                            "next_topic": ctrl_data.get("next_topic"),
                            "next_module": ctrl_data.get("next_module")
                        }
                    }
                # STAY_IN_TOPIC: fall through to normal generation pipeline

            except Exception as e:
                logger.warning(f"Master Interview Controller failed, continuing normally: {e}")
        # ─────────────────────────────────────────────────────────────────────

        # ── EXTRACTION SATISFACTION EVALUATOR ─────────────────────────────
        # Runs via llm_fast BEFORE the main copilot prompt.
        # Produces a BINARY verdict: SATISFIED or NEEDS_MORE.
        # The verdict is injected as a hard constraint into the prompt
        # so the AI cannot rationalize drilling deeper when done.
        # Targets the first MISSING objective from the phase map.
        satisfaction_verdict = "NOT_EVALUATED"
        satisfaction_missing = "N/A"
        current_objective_label = missing_objectives[0] if missing_objectives else None

        if current_objective_label:
            obj_requirements = OBJECTIVE_REQUIREMENTS.get(
                current_objective_label,
                "The expert must have given a clear, substantive answer to this objective."
            )
            # Build expert-only transcript for evaluation
            expert_lines = [
                line.strip()[len("[EXPERT]:"):].strip()
                for line in current_transcript.split("\n")
                if line.strip().startswith("[EXPERT]:")
            ]
            expert_transcript_str = "\n\n".join(expert_lines[-8:])  # last 8 expert turns

            try:
                sat_res = self.llm_fast.invoke(OBJECTIVE_SATISFACTION_PROMPT.format(
                    current_objective=current_objective_label,
                    objective_requirements=obj_requirements,
                    expert_transcript=expert_transcript_str
                ))
                sat_cl = sat_res.content.strip()
                if "```json" in sat_cl:
                    sat_cl = sat_cl.split("```json")[1].split("```")[0].strip()
                sat_cl = re.sub(r',\s*([}\]])', r'\1', sat_cl)
                sat_data = json.loads(sat_cl)
                satisfaction_verdict = sat_data.get("verdict", "NOT_EVALUATED")
                satisfaction_missing = sat_data.get("missing_element") or "None"
                sat_confidence = sat_data.get("confidence", 0.0)
                sat_story_mined = sat_data.get("story_fully_mined", False)

                # Hard enforcement: if SATISFIED, ALWAYS persist to memory to avoid the Confidence Trap
                if satisfaction_verdict == "SATISFIED":
                    logger.info(
                        f"Satisfaction evaluator: '{current_objective_label}' SATISFIED "
                        f"(confidence={sat_confidence}). Persisting to memory."
                    )
                    
                    # Persist the satisfaction state to the scratchpad so we NEVER ask about it again
                    sat_list = updated_scratchpad.get("satisfied_objectives", [])
                    if current_objective_label not in sat_list:
                        sat_list.append(current_objective_label)
                    updated_scratchpad["satisfied_objectives"] = sat_list
                    self.supabase.table("interview_sessions").update(
                        {"live_scratchpad": updated_scratchpad}
                    ).eq("id", session_id).execute()

                    # ONLY force skip if confidence is high AND it was the absolute last objective left in this block
                    if sat_confidence >= 0.80 and len(missing_objectives) <= 1:
                        logger.info("All objectives satisfied with high confidence! Forcing skip to next block.")
                        self.supabase.table("interview_sessions").update(
                            {"raw_transcript": new_transcript}
                        ).eq("id", session_id).execute()
                        return {
                            "question": None,
                            "decision": {
                                "action": "next_script_question",
                                "intent": "skip",
                                "reasoning": f"Satisfaction evaluator: '{current_objective_label}' complete.",
                                "objective_satisfied": current_objective_label
                            }
                        }
                    # Otherwise, we DO NOT RETURN here! We let it fall through to generate a question for the NEXT objective.
            except Exception as e:
                logger.warning(f"Satisfaction evaluator failed, proceeding to main prompt: {e}")

        # Build satisfaction context string for injection into prompt
        if satisfaction_verdict == "SATISFIED":
            satisfaction_context = (
                f"SATISFACTION VERDICT: OBJECTIVE '{current_objective_label}' IS COMPLETE.\n"
                f"FORBIDDEN: Do NOT ask any more questions about this objective or this story.\n"
                f"ACTION: Generate a question for the NEXT missing objective."
            )
        elif satisfaction_verdict == "NEEDS_MORE" and satisfaction_missing and satisfaction_missing != "None":
            satisfaction_context = (
                f"SATISFACTION VERDICT: OBJECTIVE '{current_objective_label}' HAS ONE GAP.\n"
                f"ONLY MISSING: {satisfaction_missing}\n"
                f"Generate ONE question that fills exactly this gap. Do not ask for anything else."
            )
        else:
            satisfaction_context = "(Satisfaction evaluator not run — proceed with objective compass.)"
        # ─────────────────────────────────────────────────────────────────────

        # ── PHASE 4: COVERAGE ENGINE (Block 4 only) ───────────────────────────
        # Runs AFTER the satisfaction evaluator. Scores 8 knowledge fields
        # (0.0–1.0) for the current topic and injects TOPIC_COMPLETE /
        # TOPIC_INCOMPLETE status into the copilot prompt.
        if active_block and "Block 4" in active_block:
            try:
                current_topic_name = (
                    updated_scratchpad.get("current_topic")
                    or current_scratchpad.get("current_topic")
                    or "Current Topic"
                )
                # Build topic-specific expert transcript (all turns so far)
                topic_expert_lines = [
                    line.strip()[len("[EXPERT]:"):].strip()
                    for line in current_transcript.split("\n")
                    if line.strip().startswith("[EXPERT]:")
                ]
                topic_transcript_str = "\n\n".join(topic_expert_lines)

                cov_res = self.llm_fast.invoke(COVERAGE_ENGINE_PROMPT.format(
                    current_topic=current_topic_name,
                    expert_transcript=topic_transcript_str
                ))
                cov_cl = cov_res.content.strip()
                if "```json" in cov_cl:
                    cov_cl = cov_cl.split("```json")[1].split("```")[0].strip()
                cov_cl = re.sub(r',\s*([}\]])', r'\1', cov_cl)
                cov_data = json.loads(cov_cl)

                cov_status = cov_data.get("status", "TOPIC_INCOMPLETE")
                cov_weakest = cov_data.get("weakest_fields", [])
                cov_lenses = cov_data.get("recommended_lenses", [])
                cov_missing = cov_data.get("missing_summary") or "No summary."
                cov_scores = cov_data.get("coverage", {})

                # Persist scored coverage into scratchpad node_checklist
                node_cl = updated_scratchpad.setdefault("node_checklist", {})
                node_cl[current_topic_name] = {**cov_scores, "status": cov_status}
                updated_scratchpad["node_checklist"] = node_cl
                self.supabase.table("interview_sessions").update(
                    {"live_scratchpad": updated_scratchpad}
                ).eq("id", session_id).execute()

                if cov_status == "TOPIC_COMPLETE":
                    satisfaction_context = (
                        f"COVERAGE ENGINE: Topic '{current_topic_name}' is TOPIC_COMPLETE.\n"
                        f"All 8 knowledge fields have met their evidence thresholds.\n"
                        f"ACTION: Return intent='skip'. The controller will advance to the next topic."
                    )
                    logger.info(f"Coverage Engine: '{current_topic_name}' COMPLETE.")
                else:
                    weakest_str = ", ".join(cov_weakest) if cov_weakest else "unknown"
                    lenses_str = ", ".join(cov_lenses) if cov_lenses else "any"
                    satisfaction_context = (
                        f"COVERAGE ENGINE: Topic '{current_topic_name}' is TOPIC_INCOMPLETE.\n"
                        f"Weakest Fields (priority targets): {weakest_str}\n"
                        f"Recommended Lenses: {lenses_str}\n"
                        f"Critical Gap: {cov_missing}\n"
                        f"ACTION: Use one of the recommended lenses to fill the weakest field. "
                        f"Do NOT ask generically — target the named gap directly."
                    )
                    logger.info(f"Coverage Engine: '{current_topic_name}' INCOMPLETE. Weakest: {weakest_str}")

            except Exception as e:
                logger.warning(f"Coverage Engine failed, using satisfaction context: {e}")

        # ── TOPIC CONTROLLER (Block 3 & Block 4 only) ────────────────────────
        if active_block and ("Block 3" in active_block or "Block 4" in active_block):
            try:
                # Extract state from scratchpad
                sp = locals().get("updated_scratchpad", current_scratchpad)
                current_module = sp.get("current_module", "Unknown")
                current_topic = sp.get("current_topic", "Unknown")
                node_checklist = sp.get("node_checklist", {})
                
                module_progress = [
                    f"{t}: {info.get('status', 'NOT_STARTED')}" 
                    for t, info in node_checklist.items() 
                    if isinstance(info, dict)
                ]
                
                ctrl_res = self.llm_fast.invoke(TOPIC_CONTROLLER_PROMPT.format(
                    current_module=current_module,
                    current_topic=current_topic,
                    module_progress=json.dumps(module_progress),
                    curriculum_map=json.dumps(node_checklist)
                ))
                
                ctrl_cl = ctrl_res.content.strip()
                if "```json" in ctrl_cl:
                    ctrl_cl = ctrl_cl.split("```json")[1].split("```")[0].strip()
                ctrl_cl = re.sub(r',\s*([}\]])', r'\1', ctrl_cl)
                ctrl_data = json.loads(ctrl_cl)
                
                ctrl_action = ctrl_data.get("action", "STAY_IN_TOPIC")
                next_topic = ctrl_data.get("current_topic")
                
                if ctrl_action in ["NEXT_TOPIC", "NEXT_MODULE"] and next_topic:
                    logger.info(f"Topic Controller advancing to {next_topic} ({ctrl_action})")
                    # Update scratchpad with the new active topic
                    sp["current_topic"] = next_topic
                    self.supabase.table("interview_sessions").update(
                        {"live_scratchpad": sp}
                    ).eq("id", session_id).execute()
                    
                    satisfaction_context = (
                        f"TOPIC CONTROLLER VERDICT: {ctrl_action}\n"
                        f"REASONING: {ctrl_data.get('reasoning')}\n"
                        f"ACTION: You MUST explicitly transition the conversation to the new topic: '{next_topic}'. "
                        f"Generate a question that introduces this topic."
                    )
            except Exception as e:
                logger.warning(f"Topic Controller failed: {e}")
        # ─────────────────────────────────────────────────────────────────────

        # ── THREAD SCORING ALGORITHM (WITH INFINITE LOOP PROTECTION) ─────────
        highest_value_thread = "None (No open threads)"
        current_sp = locals().get("updated_scratchpad", current_scratchpad)
        open_threads = current_sp.get("open_threads", [])
        asked_threads = current_sp.get("asked_threads", [])
        
        # Filter out threads we have already asked about
        filtered_threads = [t for t in open_threads if t not in asked_threads]
        
        if isinstance(filtered_threads, list) and len(filtered_threads) > 0:
            scoring_prompt = f"""\
You are an interview strategist. 
Score the following open threads from 1 to 10 based on their potential to reveal new heuristics, decisions, or failures.
Prefer threads about specific incidents, failures, and decisions.
Penalize threads about identity, philosophy, or general topics.
Return ONLY the exact text of the highest scoring thread. Nothing else.

THREADS:
{json.dumps(filtered_threads, indent=2)}
"""
            try:
                score_res = self.llm_fast.invoke(scoring_prompt)
                highest_value_thread = score_res.content.strip()
                
                # Save the highest scoring thread to asked_threads so we NEVER ask about it again
                if highest_value_thread not in asked_threads:
                    asked_threads.append(highest_value_thread)
                    current_sp["asked_threads"] = asked_threads
                    self.supabase.table("interview_sessions").update(
                        {"live_scratchpad": current_sp}
                    ).eq("id", session_id).execute()
            except Exception as e:
                logger.warning(f"Thread scoring failed: {e}")
                highest_value_thread = filtered_threads[-1] if filtered_threads else "None"
        # ─────────────────────────────────────────────────────────────────────

        # 4. Build prompt kwargs (used by both first attempt and retry)
        # Safely extract topic and coverage from scratchpad for Block 4 prompt
        current_topic_name = current_sp.get("current_topic", "Unknown")
        topic_node = current_sp.get("node_checklist", {}).get(current_topic_name, {})
        coverage_str = json.dumps(topic_node) if isinstance(topic_node, dict) else "None"
        missing_areas_str = locals().get("weakest_str", "Unknown")
        
        prompt_kwargs = dict(
            active_block=active_block,
            active_script_question=current_script_question,
            live_scratchpad=live_scratchpad_str,
            phase_objectives=phase_objectives_str,
            satisfaction_verdict=satisfaction_context,
            retrieved_context=retrieved_context,
            conversation_history=conversation_history,
            expert_answer=expert_answer,
            archetype_rules=get_archetype_rules(archetype),
            pacing_warning=pacing_warning,
            target_thread=highest_value_thread,
            current_topic=current_topic_name,
            coverage_scores=coverage_str,
            missing_areas=missing_areas_str
        )

        # ── FIX 1.2 — Safe JSON parse with retry ─────────────────────────────
        # Default is "skip" (safe) — not "substantive" which would silently advance
        copilot_data = {"intent": "skip", "follow_up": None}
        copilot_res = self.llm.invoke(LIVE_COPILOT_PROMPT.format(**prompt_kwargs))
        for attempt in range(2):
            try:
                raw = copilot_res.content.strip() if attempt == 0 else \
                    self.llm.invoke(LIVE_COPILOT_PROMPT.format(**prompt_kwargs)).content.strip()
                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0].strip()
                # Strip trailing commas that GPT occasionally emits
                raw = re.sub(r',\s*([}\]])', r'\1', raw)
                copilot_data = json.loads(raw)
                break
            except Exception as e:
                if attempt == 1:
                    logger.error(f"Copilot JSON failed after retry, defaulting to skip: {e}")
        # ─────────────────────────────────────────────────────────────────────
            
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
                existing_modules = cb.get("course_modules", [])
                merged_modules = existing_modules + modules
                self.supabase.table("curriculum_blueprints").update({
                    "course_modules": merged_modules,
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

        session_synthesis = {"general": general_data, "tutor": tutor_data, "knowledge_output": knowledge_output}
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
