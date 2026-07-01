# ==========================================================================
# Phase 8 — Knowledge Coverage Engine
# ==========================================================================
# A lightweight fast-model check that evaluates the conversation history for
# the current topic and determines if the current lens has been sufficiently
# covered.
# ==========================================================================

KNOWLEDGE_COVERAGE_PROMPT = """\
PHASE 8 — KNOWLEDGE COVERAGE ENGINE

You are a fast evaluation engine checking the coverage of the current topic's active lens.

CURRENT TOPIC: "{current_topic}"
ACTIVE LENS: "{current_lens}"

CONVERSATION HISTORY FOR THIS TOPIC:
{conversation_history}

EXPERT'S LATEST ANSWER:
{expert_answer}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LENS COMPLETENESS DEFINITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. "understanding" (Understanding Lens)
   - Completed when: The expert has explained what the concept is AND how it works.
   
2. "teaching" (Teaching Lens)
   - Completed when: The expert has detailed the steps a student takes to apply/implement this
     and mentioned reference materials/guides (or stated none are needed).

3. "failure" (Failure Lens)
   - Completed when: The expert has named at least one common mistake students make AND
     at least one production edge case/exception.

4. "experience" (Experience Lens)
   - Completed when: The expert has shared a personal rule of thumb (heuristic) OR a concrete
     war story/case study.

5. "mastery" (Mastery Lens)
   - Completed when: The expert has described a project, question, or method they use to evaluate
     if a learner has truly mastered the topic.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Return a STRICT JSON object:
{{
  "lens_complete": true | false,
  "confidence_score": 0.0 to 1.0,
  "covered_fields": {{
    "concept": true | false,
    "breakdown": true | false,
    "action_items": true | false,
    "reference_guides": true | false,
    "common_mistakes": true | false,
    "edge_cases": true | false,
    "expert_heuristic": true | false,
    "expert_story": true | false,
    "evaluation_path": true | false
  }},
  "reasoning": "brief explanation of why the lens is or isn't complete"
}}
"""
