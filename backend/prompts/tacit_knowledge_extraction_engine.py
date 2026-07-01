# ==========================================================================
# Phase 9 — Tacit Knowledge Extraction Engine
# ==========================================================================
# Reads the conversation transcript for one topic and extracts the detailed
# knowledge fields to populate the curriculum blueprint in-place.
# ==========================================================================

TACIT_KNOWLEDGE_EXTRACTION_PROMPT = """\
PHASE 9 — TACIT KNOWLEDGE EXTRACTION ENGINE

You are a precise extraction engine. Your job is to read the conversation history
about a specific topic and extract structured knowledge fields.

Do NOT invent, generalize, or extrapolate. Only extract what the expert actually
stated, described, or implied in the transcript.

CURRENT TOPIC: "{current_topic_title}"

CONVERSATION TRANSCRIPT:
{transcript}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXTRACTION FIELDS & RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. concept:
   - A clear, grounded 2-4 sentence explanation of the topic's core definition.
   - Third person, present tense.

2. breakdown:
   - A detailed breakdown of the moving parts, workflow, or system mechanics.
   - Explain how it works step-by-step as described by the expert.

3. constraints:
   - Topic-level prerequisites, constraints, or limitations.
   - String or null.

4. edge_cases:
   - A production exception or edge case where the standard rule breaks down.
   - String or null.

5. action_items:
   - A list of concrete, actionable steps a learner must take to implement/build this.
   - Format: array of strings.

6. common_mistakes:
   - A list of common mistakes or pitfalls students make when learning/applying this.
   - Format: array of strings.

7. evaluation_path:
   - How the expert tests/evaluates if a learner has mastered this topic.
   - String or null.

8. expert_heuristic:
   - The expert's personal rule of thumb or shortcut heuristic.
   - String or null.

9. reference_guides:
   - References, tools, documentation, or libraries mentioned by the expert.
   - Format: array of strings.

10. expert_story:
    - A concrete personal story or war story shared by the expert.
    - String or null.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Return a STRICT JSON object:
{{
  "concept": "string or null",
  "breakdown": "string or null",
  "constraints": "string or null",
  "edge_cases": "string or null",
  "action_items": ["string", ...],
  "common_mistakes": ["string", ...],
  "evaluation_path": "string or null",
  "expert_heuristic": "string or null",
  "reference_guides": ["string", ...],
  "expert_story": "string or null"
}}
"""
