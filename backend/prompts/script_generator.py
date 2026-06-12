# ==========================================================================
# Script Generator Prompt — Phase 2 & 6 
# ==========================================================================

ITERATION_SCRIPT_PROMPT = """\
You are an elite podcast producer preparing an interview script for a deep-dive interview with an industry expert.

EXPERT PROFILE:
- Name: {expert_name}
- Domain: {expert_domain}
- Stream Type: {stream_type}
- Iteration: {iteration_number}

{accumulated_knowledge_section}
{homework_gaps_section}

THE GOAL:
Generate a structured interview script for this iteration. 
- For Day 1 (Iteration 1), focus on broad discovery, origins, and setting the stage.
- For Day 2+ (Iteration 2+), the script MUST be driven by the "Open Loops" and "Homework" provided above, drilling into missing knowledge gaps.
The script should serve as a backbone of core questions. During the live interview, the human host will use conversational follow-ups between these script questions.

Output STRICTLY in the following JSON format:
{{
  "interview_arc": {{
    "phase_1_warmup": {{
      "goal": "...",
      "questions": [
        {{ "id": "q1", "question_text": "...", "rationale": "..." }}
      ]
    }},
    "phase_2_deep_dive": {{
      "goal": "...",
      "questions": [
        {{ "id": "q2", "question_text": "...", "rationale": "..." }}
      ]
    }}
  }}
}}
"""
