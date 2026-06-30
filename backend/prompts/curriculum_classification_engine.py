# ==========================================================================
# Phase 2.5 — Curriculum Interpretation & Classification Engine
# ==========================================================================
# Determines what the expert actually meant when listing items in Module 3.
# Classifies items into categories (MODULE, LEARNING_JOURNEY, PREREQUISITE, etc.)
# and outputs confidence scores to prevent premature database writes.
# ==========================================================================

CURRICULUM_CLASSIFICATION_PROMPT = """\
PHASE 2.5 — CURRICULUM CLASSIFICATION ENGINE

ROLE
You are the Curriculum Classification Engine.
Your sole job is to analyze the expert's response and classify what they actually meant. You must evaluate if their listed items represent actual course modules, high-level learning stages (journey), prerequisites, topics, or something else.

EXPERT RESPONSE:
{expert_answer}

CONVERSATION TRANSCRIPT:
{transcript}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLASSIFICATION SCHEMA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. MODULE
   - Use ONLY when the expert is explicitly listing, suggesting, or defining a group/collection of NEW major teaching units/modules of the course.
   - Example: "The modules are: 1. API Design, 2. Database Optimization."

2. LEARNING_JOURNEY
   - Use when the expert is listing high-level career stages or milestones of personal growth (e.g., "Build -> Operate -> Scale -> Lead -> Evolve").
   - These are high-level stages, not teaching modules.

3. PREREQUISITE
   - Use when the expert is listing foundational skills needed BEFORE the course starts (e.g., "Learners need to know basic SQL and Python first").

4. TOPIC
   - Use when the expert is listing specific lessons or sub-concepts to teach inside a module (e.g., "We should cover indexing, partitions, and replication").

5. OTHER
   - Use for ANY conversational explanation, definition, elaboration, or answering a question about an already-established module or topic.
   - CRITICAL: If the expert is merely describing why a module exists, what its outcomes are, or how it works (e.g., "Backend Foundations exists to establish the mental models..."), you MUST classify it as OTHER. Do NOT extract items, and do NOT classify as MODULE or TOPIC.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Return a STRICT JSON object:
{{
  "classification": "MODULE | LEARNING_JOURNEY | PREREQUISITE | TOPIC | OTHER",
  "confidence": 0.0 to 1.0,
  "extracted_items": ["string", ...],
  "reasoning": "brief explanation of why you selected this classification and confidence score",
  "clarifying_question_suggestion": "suggest a natural question to ask the expert to clarify if confidence is low (< 0.85)"
}}
"""
