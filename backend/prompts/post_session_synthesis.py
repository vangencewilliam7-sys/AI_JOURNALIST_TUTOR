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
TRACEABILITY RULE: You MUST provide a "transcript_reference" (e.g., the timestamp or turn ID) alongside every expert_quote so it can be located later.

ANTIPATTERNS: Identify tools, frameworks, or methodologies the expert explicitly warns against or refuses to use. Output these inside the `pattern_breaks` array and set `"type": "antipattern"`.

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

EXTRACTION LIMITS (CRITICAL):
To ensure highest quality and prevent noise, you MUST adhere to these strict limits:
- tacit_insights: MAXIMUM 5 items (only the most profound).
- mental_models: MAXIMUM 3 items.
- pattern_breaks: MAXIMUM 3 items.
- war_stories: MAXIMUM 3 items.
- weak_coverage_areas: MAXIMUM 3 items.

Return a STRICT JSON object matching this schema:
{{
  "report_title": "Domain-specific title based on the interview content",
  "expert_domain": "Inferred domain of expertise",
  "interview_depth_score": 8,
  "summary": "2-3 sentence executive summary of what was learned",
  "tacit_insights": [
    {{ "insight": "Unwritten rule", "why_tacit": "Why it's not obvious", "confidence": "HIGH | MEDIUM | LOW", "expert_quote": "Verbatim quote from transcript", "transcript_reference": "timestamp/turn ID" }}
  ],
  "mental_models": [
    {{ "model_name": "Name", "application": "How they use it", "expert_quote": "Verbatim quote", "transcript_reference": "timestamp/turn ID" }}
  ],
  "pattern_breaks": [
    {{ "type": "standard | antipattern", "conventional_approach": "What the industry standard is", "expert_approach": "What they actually do", "reasoning": "Why they deviate or warn against it", "expert_quote": "Verbatim quote", "transcript_reference": "timestamp/turn ID" }}
  ],
  "war_stories": [
    {{ "title": "Story title", "summary": "What happened", "encoded_lesson": "The tacit lesson embedded in the story", "why_untextbookable": "Why this lesson can't be learned from a book", "transcript_reference": "timestamp/turn ID" }}
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
- Set "inferred": true → if the topic was NEVER discussed but is logically necessary to complete the curriculum.

COURSE STRUCTURE RULE — NON-NEGOTIABLE:
NEVER output a module with fewer than 3 topics. A module with 1 topic is WRONG and INVALID.
A real course module covers multiple facets of its theme. For example:
- Module: "Introduction to Cloud Architecture" → Topics: Core Principles, Cloud Service Models (IaaS/PaaS/SaaS), Choosing the Right Deployment, AWS Global Infrastructure, Cost Optimization Basics
- Module: "Designing Secure Architectures" → Topics: Security by Design Philosophy, Identity & Access Management, Network Security, Data Protection & Encryption, Compliance & Governance
If the transcript doesn't provide enough raw material to fill all topics for a module, use "inferred": true for those topics (but STILL include them — do NOT delete the topic).
MINIMUM 3 topics per module, TARGET 4-5 topics per module.

7-SLOT EXTRACTION RULE (CRITICAL):
For EACH topic, you must extract ALL 7 knowledge slots from the transcript:
- concept: What is this topic in plain terms? What does the expert say it fundamentally is?
- breakdown: How does the expert break it down step-by-step or layer-by-layer?
- edge_cases: What unusual or non-obvious situations did the expert mention where this breaks or behaves differently?
- constraints: What limitations, tradeoffs, or "do not use when X" rules did the expert state?
- action_items: What specific hands-on steps or exercises should a learner do to practice this?
- evaluation_path: How does the expert test if someone truly understands this? What does mastery look like?
- common_mistakes: What errors do beginners or practitioners commonly make with this topic?
- expert_story: Any personal story or lived experience the expert shared about this topic (verbatim summary)
- expert_heuristic: Any rule-of-thumb, IF/THEN rule, or mental model the expert stated (verbatim or close paraphrase)
- reference_guides: Any specific books, videos, docs, or resources the expert mentioned for this topic

If the transcript doesn't cover a slot for a topic, set it to null. Do NOT invent content.

Return a STRICT JSON object matching this schema. NOTE: The "topics" array inside each module MUST have at least 3 items. A module with 1 topic will be treated as a schema violation.
{{
  "report_title": "Course blueprint title",
  "tutor_persona": {{
    "name": "Expert name from transcript",
    "teaching_style": "How they explain things — extracted from their actual speech patterns",
    "linguistic_fingerprint": {{
      "signature_phrases_or_metaphors": ["Exact phrases or analogies the expert repeatedly uses"],
      "explanation_blueprint": "How they structure explanations (e.g., 'always gives a real example before the concept')"
    }},
    "system_prompt": "A COMPLETE, ready-to-use LLM system prompt containing all 6 sections (IDENTITY, VOICE, TEACHING STYLE, EMOTIONAL TONE, DOMAIN ANCHORS, BANNED BEHAVIORS)."
  }},
  "course_structure": {{
    "course_title": "Title derived from the interview content",
    "modules": [
      {{
        "module_title": "Major chapter or phase",
        "learning_outcomes": ["What the learner will be able to do after this module"],
        "topics": [
          {{
            "topic_title": "First specific lesson name — REQUIRED",
            "concept": "Plain-language explanation",
            "breakdown": "Step-by-step explanation",
            "edge_cases": "Non-obvious edge cases or null",
            "constraints": "Limitations or null",
            "action_items": ["Hands-on exercise 1", "Hands-on exercise 2"],
            "evaluation_path": "What mastery looks like or null",
            "common_mistakes": ["Mistake 1", "Mistake 2"],
            "expert_story": "Personal story verbatim summary or null",
            "expert_heuristic": "Rule-of-thumb or null",
            "reference_guides": ["Resource mentioned or null"],
            "inferred": false,
            "inference_rationale": null
          }},
          {{
            "topic_title": "Second specific lesson name — REQUIRED (at least 3 topics per module)",
            "concept": "...",
            "breakdown": "...",
            "edge_cases": null,
            "constraints": null,
            "action_items": [],
            "evaluation_path": null,
            "common_mistakes": [],
            "expert_story": null,
            "expert_heuristic": null,
            "reference_guides": [],
            "inferred": true,
            "inference_rationale": "Expert did not discuss this topic explicitly but it is logically required for the module."
          }},
          {{
            "topic_title": "Third specific lesson name — REQUIRED (minimum 3 per module)",
            "concept": "...",
            "breakdown": "...",
            "edge_cases": null,
            "constraints": null,
            "action_items": [],
            "evaluation_path": null,
            "common_mistakes": [],
            "expert_story": null,
            "expert_heuristic": null,
            "reference_guides": [],
            "inferred": false,
            "inference_rationale": null
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
Scan the transcript for two highly specific types of information that require external verification:

1. RESOURCE MENTIONS: Any specific book, YouTube channel, official documentation, course, or mentor the expert claimed they learned from.
2. BOLD OPERATIONAL CLAIMS: Any hard, definitive statement the expert makes about how a technology behaves in the real world that might contradict official documentation or be outdated (e.g., "AWS Lambda cold starts always take 5 seconds with Java," or "Oracle updates break custom configs every 90 days").

For each item identified, generate a "Verification Task" for the human Host or the research team.

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
- Only extract tasks for actual resources mentioned (books, courses, videos, mentors, docs) or bold operational claims.
- Rank them by priority. CRITICAL means it is foundational to the curriculum.
- Output STRICTLY in the following JSON format using the key `ai_open_loops` to map directly to the database column.

{{
  "ai_open_loops": [
    {{
      "type": "resource_check | operational_claim",
      "topic": "The core topic being discussed.",
      "the_claim": "What the expert specifically claimed (e.g., 'I learned Redis LRU policies from this video' OR 'React context re-renders everything').",
      "source_mentioned": "The exact resource mentioned, if applicable. (Null if it's an operational claim).",
      "verification_instructions": "Highly specific instructions for the human host on HOW to verify this. (e.g., 'Check Hussein Nasser's playlist for LRU eviction' or 'Search Reddit/StackOverflow to see if this React Context issue is still true in the current version.')",
      "priority": "CRITICAL | HIGH | MEDIUM"
    }}
  ]
}}
"""

RESOURCE_VALIDATION_PROMPT = """\
You are an AI Search Query Generator.
An expert made a specific claim or referenced a specific resource during an interview.

RESOURCE MENTIONED: {resource_mentioned}
WHAT THE EXPERT CLAIMED: {what_expert_claimed}

YOUR TASK:
You have been given a Verification Task. Your job is to generate highly optimized Google Search queries to verify if this claim is accurate based on current, real-world data.
Do NOT attempt to validate this yourself using internal knowledge.

Return a JSON array of exactly 3 search queries:
{{
  "search_queries": [
    "optimized search query 1",
    "optimized search query 2",
    "optimized search query 3"
  ]
}}
"""


