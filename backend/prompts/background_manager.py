# ==========================================================================
# Background Manager — Brain B Background Tasks
# ==========================================================================

BACKGROUND_EMBED_FILTER_PROMPT = """\
You are an expert filter for a semantic vector database.
Your job is to determine if the expert's last response contains any substantive knowledge (stories, lessons, strong opinions, specific facts, or emotional insights).

If it does, extract the "essence" of what was said into a single concise paragraph. Keep it written in the first person ("I found that...").
If the response is just conversational filler ("Yeah, sure", "Okay", "I agree", "Let's move on"), return EXACTLY the string "SKIP".

EXPERT SAID:
"{expert_answer}"

Output ONLY the extracted paragraph, or "SKIP". No prose.
"""

RETRIEVAL_GATE_PROMPT = """\
You are an ultra-fast routing gate. Your ONLY job is to decide if the AI Journalist needs historical context to ask the next logical question.

ACTIVE SCRIPT QUESTION: {active_script_question}
RECENT CONVERSATION (Last 2 turns):
{conversation_history}

Does the NEXT logical question require recalling a specific story, concept, or metric from earlier in the interview?
Return EXACTLY the word "YES" or "NO". No other text.
"""

# ==========================================================================
# OBJECTIVE SATISFACTION EVALUATOR
# ==========================================================================
# This prompt runs BEFORE the main copilot prompt on every turn.
# Its job: make a BINARY verdict — is the current objective SATISFIED?
#
# This pre-computation prevents the AI from rationalizing "I should ask
# more" when the objective has already been met. The verdict is injected
# into the main prompt as a HARD constraint, not a suggestion.
#
# Definition of SATISFIED:
#   The expert's answers (combined) contain enough to answer:
#   WHY it happened, WHAT changed, WHY it mattered.
#   More details, emotions, or memories are NOT required.
# ==========================================================================

OBJECTIVE_SATISFACTION_PROMPT = """\
You are an Extraction Satisfaction Evaluator. Your ONLY job is to determine whether the current interview objective has been SATISFIED by the expert's answers so far.

CURRENT OBJECTIVE: {current_objective}

WHAT THIS OBJECTIVE NEEDS (minimum, not maximum):
{objective_requirements}

EXPERT'S ANSWERS SO FAR (transcript — expert turns only):
{expert_transcript}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EVALUATION RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SATISFIED means:
  The answers contain enough to understand WHY it happened, WHAT changed,
  and WHY it mattered. A reader of this transcript would understand the
  objective WITHOUT needing more. You do NOT need exhaustive detail.
  You need SUFFICIENT coverage.

NEEDS_MORE means:
  A SPECIFIC, NAMED piece of information is completely absent.
  These are NOT valid reasons for NEEDS_MORE:
    ✗ "More detail"
    ✗ "More emotion"
    ✗ "More examples"
    ✗ "Deeper exploration"
    ✗ "Could be more specific"
  You must name the EXACT missing piece (e.g., "Expert never stated
  what changed as a result of the experience").

ONE STORY MAXIMUM RULE:
  If the expert has already told ONE story that covers:
    - Context (what situation / when)
    - Decision or Action (what they did or thought)
    - Outcome (what happened)
    - Lesson (what it meant or changed)
  → The objective is SATISFIED. Period.
  → Do NOT request another story.
  → Do NOT request deeper details of the same story.

Return ONLY this JSON, no other text:
{{
  "verdict": "SATISFIED" | "NEEDS_MORE",
  "confidence": 0.0-1.0,
  "satisfied_elements": ["list of minimum requirement elements that ARE covered"],
  "missing_element": "The ONE specific named gap, or null if satisfied",
  "story_fully_mined": true | false
}}
"""

# Per-objective minimum requirements injected into the satisfaction evaluator.
# These define the FLOOR of what each objective needs — not a ceiling.
OBJECTIVE_REQUIREMENTS = {
    "Initial Learning Challenges": (
        "1. ONE specific challenge, difficulty, or setback they faced while learning or early in their career. "
        "2. What they did to overcome it OR what lesson they took from it. "
        "This objective is SATISFIED if the expert describes any difficulty, mistake, setback, or struggle — "
        "even briefly. Do NOT require them to use specific phrases like 'hardest part'. "
        "If they have described a failure, setback, or lesson learned from early on, mark as SATISFIED."
    ),
    "Origin Story": (
        "1. Why they entered this field (motivation or pull factor). "
        "2. One moment or experience that confirmed or started the path. "
        "3. Their initial motivation or interest."
    ),
    "First Defining Experience": (
        "1. One specific early event or experience. "
        "2. What it taught them or showed them. "
        "3. How it shaped their subsequent path."
    ),
    "Self-Description / Persona": (
        "1. How they describe their own working style, values, or professional identity. "
        "2. At least one specific trait, priority, or belief they hold as an engineer/professional."
    ),
    "Why They Teach / Share": (
        "1. Their stated reason for teaching or creating content. "
        "2. What drives them to share."
    ),
    "Major Challenges": (
        "1. One specific major challenge. "
        "2. Why it was hard. "
        "3. What they did about it or how they got through it."
    ),
    "Failures": (
        "1. One specific failure or mistake. "
        "2. What went wrong. "
        "3. What they learned from it."
    ),
    "Belief Changes": (
        "1. One belief or assumption they previously held. "
        "2. What changed it. "
        "3. How they think differently now as a result."
    ),
    "Decision Frameworks": (
        "1. A structured way they approach problems or make decisions. "
        "2. An example of how they apply this framework."
    ),
    "Pattern Recognition": (
        "1. A specific pattern, warning sign, or red flag they now recognize. "
        "2. How they missed it early on but catch it now."
    ),
    "Mentors & Influences": (
        "1. A specific person (mentor, manager, etc.) who influenced them. "
        "2. A specific lesson or piece of advice they learned from them."
    ),
    "Module Overview": (
        "1. A high-level explanation of what this module is about. "
        "2. The core goal or thesis of this module."
    ),
    "Specific Topics Identified": (
        "1. A clear list of specific topics that belong in this module. "
        "2. At least a brief mention of what each topic covers."
    ),
    "Topic Ordering / Sequence": (
        "1. The order in which topics should be learned. "
        "2. Rationale for that specific order."
    ),
    "Topic Dependencies": (
        "1. Which topics depend on others. "
        "2. Why that dependency exists."
    ),
    "What Gets Skipped (gaps)": (
        "1. At least one topic that is commonly skipped. "
        "2. What breaks or goes wrong without it."
    ),
    "At Least One Module Fully Extracted": (
        "1. Full breakdown of one topic: what it is + how it works. "
        "2. At least one specific nuance, edge case, or practical insight."
    ),
    "Reference Resources Mentioned": (
        "1. At least one specific book, course, article, or resource. "
        "2. A reason or context for why it matters."
    ),
    "At Least One Expert Heuristic Extracted": (
        "1. One rule-of-thumb or heuristic the expert personally uses. "
        "2. Stated as an actionable rule (when X → do Y, or never do Z)."
    ),
    "Common Mistakes Covered": (
        "1. At least one specific mistake. "
        "2. Why people make it. "
        "3. What to do instead."
    ),
    "Overarching Mental Model": (
        "1. The expert's high-level framework for thinking about their entire field. "
        "2. What makes this framework different or specific to them."
    ),
    "Advice to Beginners": (
        "1. At least one specific piece of advice for someone new to this field. "
        "2. Why they believe this advice matters."
    ),
    "Contrarian Belief": (
        "1. One belief the expert holds that contradicts common wisdom. "
        "2. Their reasoning or evidence for it."
    ),
}

# ==========================================================================
# PHASE 4 — COVERAGE ENGINE
# ==========================================================================
# Runs AFTER every expert answer in Block 4 (Topic Extraction).
# Does NOT generate questions. Only scores evidence and signals completion.
# Output is injected into `satisfaction_verdict` in the main copilot prompt.
# ==========================================================================

COVERAGE_ENGINE_PROMPT = """\
You are a Knowledge Coverage Evaluator.

You do NOT ask questions.
You do NOT interview experts.
You evaluate how much evidence has been collected for the CURRENT TOPIC.

CURRENT TOPIC: {current_topic}

EXTRACTED EVIDENCE (all expert answers for this topic so far):
{expert_transcript}

KNOWLEDGE FIELDS TO EVALUATE:
* Concept           — Does the evidence clearly define what this topic is?
* Action Items      — Does the evidence describe concrete steps or procedures?
* Reference Guides  — Are specific books, tools, frameworks, or resources mentioned?
* Edge Cases        — Are unusual, boundary, or failure scenarios described?
* Constraints       — Are limits, prerequisites, or conditions that restrict use described?
* Evaluation Path   — Is there guidance on how to assess mastery or correctness?
* Common Mistakes   — Are specific errors practitioners make described?
* Heuristics        — Are rules of thumb, mental models, or decision shortcuts present?

SCORING (per field):
  0.00 = No evidence
  0.25 = Weak / implied evidence
  0.50 = Partial evidence
  0.75 = Strong but incomplete evidence
  1.00 = Complete, sufficient evidence

COMPLETION THRESHOLDS (minimum scores required):
  Concept           >= 0.80
  Action Items      >= 0.70
  Edge Cases        >= 0.70
  Constraints       >= 0.70
  Evaluation Path   >= 0.70
  Common Mistakes   >= 0.70
  Heuristics        >= 0.70
  Reference Guides  >= 0.50

ANTI-LOOP RULE:
Never recommend a follow-up that does not improve the weakest fields.
Every recommended lens must close a measurable evidence gap.
Never recommend "tell me more" or generic elaboration.

Return ONLY this JSON, no other text:
{{
  "topic": "{current_topic}",
  "status": "TOPIC_COMPLETE" | "TOPIC_INCOMPLETE",
  "coverage": {{
    "concept":          0.0,
    "action_items":     0.0,
    "reference_guides": 0.0,
    "edge_cases":       0.0,
    "constraints":      0.0,
    "evaluation_path":  0.0,
    "common_mistakes":  0.0,
    "heuristics":       0.0
  }},
  "weakest_fields":     ["list of field names below threshold, sorted ascending by score"],
  "recommended_lenses": ["Teaching Lens" | "Failure Lens" | "Decision Lens" | "Pattern Lens" | "Experience Lens"],
  "missing_summary":    "One sentence naming the most critical gap, or null if complete"
}}
"""

SCRATCHPAD_UPDATE_PROMPT = """\
You are a background memory manager (Brain B).
Your job is to update the JSON Working Memory (Scratchpad) based on the newest transcript lines.

CURRENT SCRATCHPAD:
{current_scratchpad}

NEWEST TRANSCRIPT LINES:
{new_transcript}

Update the scratchpad using an APPEND-ONLY mindset for arrays. Do NOT delete past facts or old threads. 
Extract conclusions AND causal experiences (incidents, decisions, outcomes).

For `node_checklist`: track which of the 10 knowledge slots have been filled for the current topic.
Mark a slot as true ONLY if the expert explicitly covered it in the transcript.
APPEND-ONLY: once a slot is true, NEVER set it back to false.

Return ONLY the updated JSON object. No prose.
Schema:
{{
  "current_topic": "What they are talking about right now",
  "new_facts": ["Concrete things they did, roles they held, tech they used"],
  "new_decisions": ["Specific choices they made and the trade-offs"],
  "new_failures": ["Specific incidents, mistakes, outages, or wrong assumptions"],
  "new_heuristics": ["Rules of thumb or mental models derived from their experiences"],
  "open_threads": ["Highly specific unresolved incidents or decisions to ask about later"],
  "expert_profile": {{"role": "...", "industry": "..."}},
  "satisfied_objectives": ["array", "of", "strings", "DO NOT MODIFY OR DELETE EXISTING ONES"],
  "node_checklist": {{
    "<topic_name>": {{
      "module": "Module name",
      "prerequisites": ["List of prerequisite topics"],
      "importance": "Foundational | Advanced",
      "concept":          0.0,
      "action_items":     0.0,
      "reference_guides": 0.0,
      "edge_cases":       0.0,
      "constraints":      0.0,
      "evaluation_path":  0.0,
      "common_mistakes":  0.0,
      "heuristics":       0.0,
      "status": "NOT_STARTED" | "IN_PROGRESS" | "COMPLETE"
    }}
  }}
}}
"""

# ==========================================================================
# TOPIC CONTROLLER
# ==========================================================================
# ONLY active in Block 3 and Block 4. Runs before the main copilot prompt.
# ==========================================================================

TOPIC_CONTROLLER_PROMPT = """\
ROLE

You are a Topic Controller.

Goal:
Manage topic progression.

Input:
Current Module: {current_module}
Current Topic: {current_topic}
Topic List: {module_progress}
Curriculum Map (Dependencies & Priorities): {curriculum_map}

RULES

Every topic has:
NOT_STARTED
IN_PROGRESS
COMPLETE

Select next topic using:
1. Dependency order
2. Priority order
3. Coverage status

Do not allow:
* Topic jumping
* Module jumping
* Returning to completed topics

Output ONLY this JSON:
{{
  "action": "STAY_IN_TOPIC" | "NEXT_TOPIC" | "NEXT_MODULE",
  "current_topic": "The exact topic name to focus on next, or null if moving to next module",
  "reasoning": "Explanation based on dependencies, priority, and coverage"
}}
"""
