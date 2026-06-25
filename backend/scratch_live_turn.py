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
