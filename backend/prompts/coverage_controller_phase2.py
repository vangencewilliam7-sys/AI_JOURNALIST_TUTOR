# ==========================================================================
# Phase 2 Coverage Controller Prompt
# ==========================================================================
# Deliberately evaluates the full transcript of Phase 2 (and previous phases)
# to extract the definitive list of modules that have been discussed.
# ==========================================================================

MODULE_COVERAGE_CONTROLLER_PROMPT = """\
PHASE 2 — MODULE COVERAGE CONTROLLER

ROLE
You are the Module Coverage Controller.
Your job is to objectively analyze the transcript of the interview so far and extract all major modules/chapters of the course that the expert has described.

CONVERSATION TRANSCRIPT:
{transcript}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXTRACTION RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Extract only major modules, chapters, or milestones (e.g., "Building Backend Applications", "Operating Production Systems").
2. Exclude sub-topics or micro-details (e.g., "FastAPI", "how to write a query").
3. Format each module title cleanly (Title Case, 2-6 words, no filler words).
4. If the expert has already listed these chapters earlier in the conversation (even during Phase 1), extract them now.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Return a STRICT JSON object:
{{
  "modules": ["string", ...],
  "expert_signaled_complete": true | false,
  "internal_reasoning": "brief explanation of extracted modules"
}}
"""
