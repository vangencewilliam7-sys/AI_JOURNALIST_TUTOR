# ==========================================================================
# Post-Session Synthesis Prompts — Asynchronous extraction after "End Session"
# Converted from: src/prompts/postSessionSynthesis.js (Node.js brainstorm)
# ==========================================================================
# These prompts run asynchronously AFTER the human clicks "End Session".
# They extract structured knowledge from the raw transcript into JSONB tables.
#
# GENERAL_SYNTHESIS_PROMPT   — Universal extraction (persona_traits, war_stories, etc.)
# TUTOR_SYNTHESIS_PROMPT     — Curriculum extraction (modules, topics) — tutor stream only
# HOMEWORK_GENERATOR_PROMPT  — Identifies open loops / knowledge gaps
# ==========================================================================

GENERAL_SYNTHESIS_PROMPT = """\
You are a Tacit Knowledge Synthesizer. You have the full transcript of an AI Journalist interview.

FULL INTERVIEW TRANSCRIPT:
{transcript}

YOUR TASK:
Analyze every expert response meticulously. Extract ALL tacit knowledge — the unspoken skills, instincts, heuristics, and experience-based wisdom. DO NOT include things the expert said generically.

Return a STRICT JSON object matching this schema:
{{
  "report_title": "Domain-specific title based on the interview content",
  "expert_domain": "Inferred domain of expertise",
  "interview_depth_score": 8,
  "summary": "2-3 sentence executive summary of what was learned",
  "tacit_insights": [
    {{ "insight": "Unwritten rule", "why_tacit": "Why it's not obvious", "confidence": "HIGH", "expert_quote": "Direct quote" }}
  ],
  "mental_models": [
    {{ "model_name": "Name", "application": "How they use it", "expert_quote": "Direct quote" }}
  ],
  "pattern_breaks": [
    {{ "conventional_approach": "Standard", "expert_approach": "Their way", "reasoning": "Why they deviate", "expert_quote": "Direct quote" }}
  ],
  "war_stories": [
    {{ "title": "Story title", "summary": "What happened", "encoded_lesson": "The lesson", "why_untextbookable": "Why it's rare" }}
  ],
  "knowledge_gaps": [
    {{ "topic": "Topic dodged", "observation": "What they did", "suggested_followup": "How to ask next time" }}
  ]
}}
"""

TUTOR_SYNTHESIS_PROMPT = """\
You are a Course Blueprint Synthesizer. You have the full transcript of a Course Architect interview.

FULL INTERVIEW TRANSCRIPT:
{transcript}

YOUR TASK: 
Analyze EVERY SINGLE tutor response. Extract ALL knowledge to build a PRODUCTION-READY course blueprint and a complete tutor identity.
ZERO-HALLUCINATION GROUNDING RULE: Every module, topic, insight, quote, and persona detail MUST be directly traceable to the transcript.

Return a STRICT JSON object matching this schema:
{{
  "report_title": "Course blueprint title",
  "tutor_persona": {{
    "name": "Expert name",
    "teaching_style": "How they explain things",
    "linguistic_fingerprint": {{
      "signature_phrases_or_metaphors": ["Phrase 1"],
      "explanation_blueprint": "How they structure explanations"
    }},
    "system_prompt": "A COMPLETE, ready-to-use LLM system prompt (MINIMUM 200 words) that would allow an AI to perfectly mimic this expert's voice, tone, teaching style, and personality."
  }},
  "course_structure": {{
    "course_title": "Calculated title",
    "modules": [
      {{
        "module_title": "Major chapter phase",
        "learning_outcomes": ["Outcomes"],
        "topics": [
          {{
            "topic_title": "Specific lesson name",
            "key_concepts": ["Concept 1", "Concept 2"],
            "suggested_format": "video lecture | hands-on exercise | quiz",
            "tutor_insight": "Specific nugget FROM THE INTERVIEW about WHY this matters",
            "inferred": false
          }}
        ]
      }}
    ]
  }},
  "structured_tacit_notes": [
    {{
      "theme": "Theme name",
      "notes": [ {{ "note_title": "Title", "content": "Lesson", "expert_quote": "Direct quote" }} ]
    }}
  ]
}}
"""

HOMEWORK_GENERATOR_PROMPT = """\
Analyze the transcript and extracted knowledge from today's session to calculate the "Homework Ledger".

RAW TRANSCRIPT: {transcript}
EXTRACTED KNOWLEDGE: {extracted_session_data}

TASK: 
Identify "Open Loops", "continuation threads", and "cliffhangers" from the raw transcript. 
Look for highly compelling stories, critical concepts, or major events the expert briefly introduced, but which the host failed to explore because they followed a different conversational tangent.

Output STRICTLY in the following JSON format:
{{
  "ai_open_loops": [
    {{
      "topic": "The exact cliffhanger or continuation thread left behind.",
      "reasoning": "Why this is a juicy story we must ask about in the next session."
    }}
  ]
}}
"""
