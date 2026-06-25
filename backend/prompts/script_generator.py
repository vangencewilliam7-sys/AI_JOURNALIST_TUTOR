# ==========================================================================
# Script Generator Prompt — Phase 2 & 6
# ==========================================================================
# Generates the full 5-block interview blueprint for Course Extraction.
# For Day 1: broad discovery across all 5 blocks.
# For Day 2+: driven by open loops and homework from previous sessions.
# ==========================================================================

ITERATION_SCRIPT_PROMPT = """\
PHASE 1
TOPIC BACKLOG ENGINE

ROLE
You are an elite podcast producer and curriculum architect.
Your goal is to generate a dynamic "Topic Backlog" (a series of Knowledge Blocks) for an interview.

EXPERT PROFILE:
- Name: {expert_name}
- Current Title: {expert_title}
- Domain: {expert_domain}
- Years of Experience: {years_of_experience}
- Background Context: {short_bio}
- Stream Type: {stream_type}
- Iteration: {iteration_number}

INTERVIEW STYLE:
{archetype_rules}

PREVIOUSLY EXTRACTED KNOWLEDGE:
{accumulated_knowledge_section}

HOMEWORK GAPS:
{homework_gaps_section}

OBJECTIVE
1. Do not generate a rigid, linear script. Generate a backlog of discrete Knowledge Blocks.
2. Each block represents a specific topic, module, or theme to explore.
3. Instead of predefined follow-up questions, provide "exploration_vectors" (angles to probe) and "target_knowledge_types" (the specific tacit knowledge needed).
4. Provide a single "opener_question" to initiate the block.

BLOCK PRIORITY
- For Day 1 (Iteration 1): Focus on Personal Origins, non-linear learning journeys, and establishing the high-level curriculum pillars.
- For Day 2+ (Iteration 2+): Focus heavily on drilling into the Homework Gaps and deeply extracting specific missing topics.

OUTPUT FORMAT
Return a STRICT JSON object matching this schema:
{{
  "estimated_total_duration_minutes": 120,
  "topic_backlog": [
    {{
      "block_id": "string",
      "topic_title": "string",
      "opener_question": "string",
      "exploration_vectors": ["string (e.g., 'Probe on how they debug X', 'Ask for a failure story about Y')"],
      "target_knowledge_types": ["string (e.g., Mental Model, Heuristic, Failure Pattern)"],
      "estimated_minutes": 20
    }}
  ]
}}
"""

