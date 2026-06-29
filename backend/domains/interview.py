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
    TOPIC_CONTROLLER_PROMPT,
    INSIGHT_DETECTION_PROMPT,
    INSIGHT_PRIORITIZATION_PROMPT,
    KNOWLEDGE_GRAPH_UPDATE_PROMPT,
    COVERAGE_AND_GAP_PROMPT,
    MASTER_INTERVIEW_ORCHESTRATOR_PROMPT,
    ADAPTIVE_CURIOSITY_PROMPT
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
        
        # Save script to the most recent active session
        session_res = self.supabase.table("interview_sessions").select("id").eq("expert_id", expert_id).eq("status", "active").order("created_at", desc=True).limit(1).execute()
        if session_res.data:
            session_id = session_res.data[0]["id"]
            self.supabase.table("interview_sessions").update({"script": script_data}).eq("id", session_id).execute()
            
        return script_data

    async def live_turn(self, session_id: str, expert_answer: str, request_data: Dict[str, Any] = None) -> Dict[str, Any]:
        session_res = self.supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Active session not found.")
        session = session_res.data[0]
        expert = await self._get_expert(session["expert_id"])
        
        # 1. Update Transcript
        current_transcript = session.get("raw_transcript", "")
        new_transcript = current_transcript + f"\n\n[EXPERT]: {expert_answer}"
        
        # Pull State
        current_scratchpad = session.get("live_scratchpad", {})
        current_block = current_scratchpad.get("current_block", "Block 1: Personal Origin & Persona")
        current_topic = current_scratchpad.get("current_topic", "General Exploration")
        current_module = current_scratchpad.get("current_module", "Unknown")
        knowledge_nodes = current_scratchpad.get("knowledge_nodes", [])
        
        tangent_depth = current_scratchpad.get("tangent_depth", 0)
        tangent_budget = current_scratchpad.get("tangent_budget", 2)
        extra_budget_used = current_scratchpad.get("extra_budget_used", 0)
        
        # Import rules
        from domains.rules import get_block_rules, DRIFT_RULES, TANGENT_BUDGET_RULES
        block_rules = get_block_rules(current_block)
        
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

        # ── PHASE 1.5: DRIFT DETECTOR ──
        drift_score = 1.0
        try:
            # We don't have the last exact question easily accessible here without parsing transcript
            # We can use the last AI JOURNALIST line from current_transcript
            last_question = "Unknown"
            if current_transcript:
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

        # ── PHASE 5: DETERMINISTIC COVERAGE ──
        topic_completion_count = 0
        block_completion_count = 0
        coverage_map = {}
        try:
            res_coverage = await self.llm_fast.ainvoke(COVERAGE_AND_GAP_PROMPT.format(
                current_block=current_block,
                current_topic=current_topic,
                required_targets=json.dumps(block_rules["required"]),
                knowledge_nodes=json.dumps(knowledge_nodes),
                conversation_history=self._build_conversation_history(new_transcript, max_turns=6)
            ))
            coverage_map = _parse_json(res_coverage.content)
            
            # Calculate counts
            for key in block_rules["exit_requirements"]:
                if coverage_map.get(key) is True:
                    block_completion_count += 1
                    topic_completion_count += 1
        except Exception as e:
            logger.warning(f"Phase 5 failed: {e}")

        # ── DETERMINISTIC ORCHESTRATOR (Replacing Phase 7 LLM) ──
        next_action = "CONTINUE_TOPIC"
        
        # 1. Is Block Complete?
        if block_completion_count >= block_rules["minimum_completion"]:
            next_action = "MOVE_BLOCK"

        # 2. Is Topic Complete?
        elif topic_completion_count >= block_rules["minimum_completion"]:
            next_action = "MOVE_TOPIC"

        # 3. Drift Detected?
        elif drift_score < DRIFT_RULES["drift_threshold"]:
            next_action = "RETURN_TO_BLOCK"

        # 4. Tangent Budget Exhausted?
        elif tangent_depth >= tangent_budget:
            next_action = "MOVE_TOPIC"

        # 5. High Value Insight?
        elif top_insight.get("score", 0) >= TANGENT_BUDGET_RULES["high_value_threshold"] and extra_budget_used < TANGENT_BUDGET_RULES["max_high_value_followups"]:
            tangent_budget += TANGENT_BUDGET_RULES["extra_for_high_value"]
            extra_budget_used += 1
            next_action = "EXPLORE_INSIGHT"

        # 6. Default Gap Question
        else:
            next_action = "ASK_GAP_QUESTION"
            
        # ── Execute Action ──
        if next_action in ["MOVE_BLOCK", "MOVE_TOPIC"]:
            # Reset tangent depth for the next block/topic
            current_scratchpad["tangent_depth"] = 0
            current_scratchpad["tangent_budget"] = TANGENT_BUDGET_RULES["base_budget"]
            current_scratchpad["extra_budget_used"] = 0
            current_scratchpad["knowledge_nodes"] = knowledge_nodes
            
            self.supabase.table("interview_sessions").update({
                "raw_transcript": new_transcript,
                "live_scratchpad": current_scratchpad
            }).eq("id", session_id).execute()
            
            return {
                "question": None,
                "decision": {
                    "action": "next_script_question",
                    "intent": "skip",
                    "reasoning": f"Deterministic Rule matched: {next_action}. Coverage: {block_completion_count}/{block_rules['minimum_completion']}"
                }
            }

        # If not moving, increment tangent depth
        current_scratchpad["tangent_depth"] = tangent_depth + 1
        current_scratchpad["tangent_budget"] = tangent_budget
        current_scratchpad["extra_budget_used"] = extra_budget_used
        current_scratchpad["knowledge_nodes"] = knowledge_nodes

        # PHASE 6: ADAPTIVE CURIOSITY ENGINE
        try:
            res_curiosity = await self.llm.ainvoke(ADAPTIVE_CURIOSITY_PROMPT.format(
                current_block=current_block,
                current_module=current_module,
                current_topic=current_topic,
                conversation_history=self._build_conversation_history(new_transcript, max_turns=6),
                reflection_output=top_insight.get("evidence", ""),
                detected_insights=json.dumps(detected_insights),
                knowledge_graph=json.dumps(knowledge_nodes),
                coverage_gaps=json.dumps([k for k, v in coverage_map.items() if not v]),
                engagement_signals=f"Drift Score: {drift_score}"
            ))
            curiosity_data = _parse_json(res_curiosity.content)
            next_question = curiosity_data.get("question", "")
        except Exception as e:
            logger.warning(f"Phase 6 failed: {e}")
            next_question = "Can you expand on that?"

        if next_question:
            new_transcript += f"\n\n[AI JOURNALIST]: {next_question}"
            
        self.supabase.table("interview_sessions").update({
            "raw_transcript": new_transcript,
            "live_scratchpad": current_scratchpad
        }).eq("id", session_id).execute()

        return {
            "question": next_question,
            "decision": {
                "action": "follow_tangent",
                "intent": "substantive",
                "reasoning": f"Action: {next_action}. Drift: {drift_score}. Budget: {tangent_depth+1}/{tangent_budget}"
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

