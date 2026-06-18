# ==========================================================================
# Post-Session Synthesis Prompts — Asynchronous extraction after "End Session"
# ==========================================================================
# These prompts run asynchronously AFTER the human clicks "End Session".
# They extract structured knowledge from the raw transcript into JSONB tables.
#
# GENERAL_SYNTHESIS_PROMPT   — Universal extraction (tacit_insights, war_stories, etc.)
# TUTOR_SYNTHESIS_PROMPT     — Curriculum extraction (modules, topics) — tutor stream only
# HOMEWORK_GENERATOR_PROMPT  — Identifies open loops / dropped threads
#
# EXECUTION: Phase 4 (General + Tutor) and Phase 5 (Homework) run
# CONCURRENTLY via asyncio.gather() to reduce total processing time.
# ==========================================================================

GENERAL_SYNTHESIS_PROMPT = """\
You are a Tacit Knowledge Synthesizer. You have the full transcript of an AI Journalist interview.

EXPERT CONTEXT:
- Name: {expert_name}
- Domain: {expert_domain}
- Session: Day {iteration_number}

FULL INTERVIEW TRANSCRIPT:
{transcript}

YOUR TASK:
Analyze every expert response meticulously. Extract ALL tacit knowledge — the unspoken skills, instincts, heuristics, and experience-based wisdom. DO NOT include things the expert said generically or facts that anyone could find in a textbook or Google search.

WHAT IS TACIT KNOWLEDGE (extract these):
- Operational instincts that only come from years of experience
- Unwritten rules that contradict official documentation
- Gut feelings about when something is about to go wrong
- Workarounds that aren't in any manual
- Lessons learned from specific crises or failures

WHAT IS NOT TACIT KNOWLEDGE (DO NOT extract):
- Textbook definitions ("Oracle CPQ is a cloud-based configure-price-quote tool")
- Generic industry knowledge anyone can Google
- The expert simply describing what their product does

DEPTH SCORE RUBRIC — Use this to calculate interview_depth_score:
- 1-3: Expert gave mostly surface-level, rehearsed, corporate-safe responses. Few or no war stories. No pattern breaks.
- 4-6: Some genuine insights emerged but many topics stayed shallow. Expert deflected on several important threads.
- 7-8: Multiple deep war stories and pattern breaks extracted. Expert revealed operational realities that contradict conventional wisdom.
- 9-10: Expert revealed genuinely novel, never-before-documented knowledge. Multiple "I've never told anyone this" moments.

GROUNDING RULE: The "expert_quote" field MUST be a VERBATIM substring copied directly from the transcript. Do NOT paraphrase, summarize, or clean up the grammar. Copy exactly as spoken.

FEW-SHOT EXAMPLE — What IS tacit knowledge:
{{
  "insight": "Oracle ships quarterly updates that silently break existing custom configurations. Teams must re-validate everything every 90 days.",
  "why_tacit": "No documentation warns about this. You only discover it after your first quarterly update destroys a live client deployment.",
  "confidence": "HIGH",
  "expert_quote": "every quarter Oracle drops an update and half our validation rules just stop working"
}}

FEW-SHOT EXAMPLE — What is NOT tacit knowledge (DO NOT extract):
{{
  "insight": "Oracle CPQ is a cloud-based configure-price-quote tool",
  "why_tacit": "It's complex software"
}}
→ ❌ REJECT THIS. This is a textbook fact anyone can Google.

Return a STRICT JSON object matching this schema:
{{
  "report_title": "Domain-specific title based on the interview content",
  "expert_domain": "Inferred domain of expertise",
  "interview_depth_score": 8,
  "summary": "2-3 sentence executive summary of what was learned",
  "tacit_insights": [
    {{ "insight": "Unwritten rule", "why_tacit": "Why it's not obvious", "confidence": "HIGH | MEDIUM | LOW", "expert_quote": "Verbatim quote from transcript" }}
  ],
  "mental_models": [
    {{ "model_name": "Name", "application": "How they use it", "expert_quote": "Verbatim quote" }}
  ],
  "pattern_breaks": [
    {{ "conventional_approach": "What the industry standard is", "expert_approach": "What they actually do", "reasoning": "Why they deviate", "expert_quote": "Verbatim quote" }}
  ],
  "war_stories": [
    {{ "title": "Story title", "summary": "What happened", "encoded_lesson": "The tacit lesson embedded in the story", "why_untextbookable": "Why this lesson can't be learned from a book" }}
  ],
  "weak_coverage_areas": [
    {{ "topic": "Topic where the expert's answer was shallow or rehearsed", "observation": "What they said that signals surface-level knowledge", "depth_needed": "What a DEEPER answer would reveal" }}
  ]
}}
"""

TUTOR_SYNTHESIS_PROMPT = """\
You are a Course Blueprint Synthesizer. You have the full transcript of a Course Architect interview.

EXPERT CONTEXT:
- Name: {expert_name}
- Domain: {expert_domain}
- Session: Day {iteration_number}

FULL INTERVIEW TRANSCRIPT:
{transcript}

YOUR TASK: 
Analyze EVERY SINGLE tutor response. Extract ALL knowledge to build a PRODUCTION-READY course blueprint and a complete tutor identity.
ZERO-HALLUCINATION GROUNDING RULE: Every module, topic, insight, quote, and persona detail MUST be directly traceable to the transcript.

SYSTEM PROMPT STRUCTURE REQUIREMENT:
The "system_prompt" field must contain ALL of these sections:
1. IDENTITY — Who you are (name, title, domain expertise)
2. VOICE — Specific verbal patterns (e.g., "always starts explanations with an analogy")
3. TEACHING STYLE — How you structure explanations (top-down? example-first? story-driven?)
4. EMOTIONAL TONE — Are you warm and encouraging? Blunt and no-nonsense? Socratic?
5. DOMAIN ANCHORS — Specific real-world examples you always reference
6. BANNED BEHAVIORS — Things this expert would NEVER say or do

INFERRED FLAG RULE:
- Set "inferred": false → if the expert explicitly discussed this topic in the transcript.
- Set "inferred": true → if the topic was NEVER discussed but is logically necessary to complete the curriculum. For example, if the expert teaches advanced configuration but never mentioned basics, you may infer a "Fundamentals" module — but you MUST flag it as inferred.

Return a STRICT JSON object matching this schema:
{{
  "report_title": "Course blueprint title",
  "tutor_persona": {{
    "name": "Expert name from transcript",
    "teaching_style": "How they explain things — extracted from their actual speech patterns",
    "linguistic_fingerprint": {{
      "signature_phrases_or_metaphors": ["Exact phrases or analogies the expert repeatedly uses"],
      "explanation_blueprint": "How they structure explanations (e.g., 'always gives a real example before the concept')"
    }},
    "system_prompt": "A COMPLETE, ready-to-use LLM system prompt containing all 6 sections listed above (IDENTITY, VOICE, TEACHING STYLE, EMOTIONAL TONE, DOMAIN ANCHORS, BANNED BEHAVIORS)."
  }},
  "course_structure": {{
    "course_title": "Title derived from the interview content",
    "modules": [
      {{
        "module_title": "Major chapter or phase",
        "learning_outcomes": ["What the learner will be able to do after this module"],
        "topics": [
          {{
            "topic_title": "Specific lesson name",
            "key_concepts": ["Concept 1", "Concept 2"],
            "suggested_format": "video lecture | hands-on exercise | quiz | case study",
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
      "notes": [ {{ "note_title": "Title", "content": "The lesson extracted", "expert_quote": "Verbatim quote from transcript" }} ]
    }}
  ]
}}
"""

HOMEWORK_GENERATOR_PROMPT = """\
You are a Curriculum Fact-Checker scanning the transcript for "Resource Verification Tasks."

EXPERT CONTEXT:
- Name: {expert_name}
- Domain: {expert_domain}
- Session: Day {iteration_number}

RAW TRANSCRIPT: 
{transcript}

TASK: 
Identify every specific resource the expert mentioned (e.g., a specific book, a YouTube channel, a mentor, an official documentation page, or a course). 
For each resource, generate a "Verification Task" for the human Host. The Host needs to go look at that resource and see if the content matches what the expert claimed they learned from it.

CONCRETE EXAMPLE:
Transcript excerpt:
  HOST: "Before we get into Indexing, what about Caching? Where did you actually learn that?"
  EXPERT: "For Caching, I watched Hussein Nasser's YouTube videos. The main thing I learned was how Redis handles LRU eviction policies."

Analysis:
{{
  "topic": "Database Caching (Redis Eviction Policies)",
  "resource_mentioned": "Hussein Nasser YouTube series on Caching",
  "what_expert_claimed": "They learned Redis LRU eviction policies from this specific series.",
  "host_homework_instructions": "Watch Hussein Nasser's videos on Redis Caching. Verify if he actually covers LRU eviction policies in detail, or if there is a gap that the expert filled with their own tacit knowledge.",
  "priority": "HIGH"
}}

OUTPUT RULES:
- Only extract tasks for actual resources mentioned (books, courses, videos, mentors, docs). 
- Rank them by priority. CRITICAL means it is foundational to the curriculum.
- Output STRICTLY in the following JSON format.

{{
  "ai_open_loops": [
    {{
      "topic": "The core topic being discussed.",
      "resource_mentioned": "The exact book, video, or resource mentioned.",
      "what_expert_claimed": "What the expert specifically claimed they learned from it.",
      "host_homework_instructions": "Clear instructions for the human host on what to verify in this resource.",
      "priority": "CRITICAL | HIGH | MEDIUM"
    }}
  ]
}}
"""

RESOURCE_VALIDATION_PROMPT = """\
You are an AI Fact Checker and Curriculum Verifier.
An expert mentioned a specific resource (book, video, docs, etc.) during an interview and claimed it contains certain information or teaches specific concepts.

RESOURCE MENTIONED: {resource_mentioned}
WHAT THE EXPERT CLAIMED: {what_expert_claimed}

YOUR TASK:
Using your internal knowledge about this resource, evaluate whether the expert's claim is accurate.
- Does this resource actually cover the topics the expert claims it does?
- Is the expert misattributing a concept to the wrong resource?
- If the resource is extremely obscure, private, or you cannot confidently verify it, flag it for human review.

Return a STRICT JSON object matching this schema:
{{
  "validation_status": "Valid", 
  "validation_reasoning": "A concise (1-2 sentence) explanation of your validation."
}}
NOTE: "validation_status" MUST be exactly one of: "Valid", "Invalid", or "Needs Human Review".
"""
