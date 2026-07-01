# ==========================================================================
# Script Generator Prompt — Phase 2 & 6
# ==========================================================================
# Generates the full interview blueprint for Course Extraction as a Module->Topic hierarchy.
# For Day 1: broad discovery across all modules.
# For Day 2+: driven by open loops and homework from previous sessions.
# ==========================================================================

ITERATION_SCRIPT_PROMPT = """\
PHASE 1
MODULE AND TOPIC BACKLOG ENGINE

ROLE
You are an elite podcast producer and curriculum architect.
Your goal is to generate a dynamic "Module Backlog" for an interview, breaking down the expert's knowledge into a structured curriculum.

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
Generate a backlog of Curriculum Modules, each containing MULTIPLE Topics (minimum 3, ideally 4-5 per module).

=== DAY 1 (Iteration 1) FIXED ARC — FOLLOW THIS EXACTLY ===
Do NOT hallucinate the expert's actual course curriculum yet.
Day 1 is a structured journalistic interview split into TWO phases:

PHASE A — JOURNALISTIC (Modules 1, 2, 4): Get to know the expert as a human being.
  These are FREE-FLOWING podcast conversations. No rigid structure. No component gates.
  The expert shares stories, opinions, and experiences. The AI follows up naturally.
  Set "tracking_mode": "journalistic" on these modules.

PHASE B — CURRICULUM DISCOVERY (Module 3 — tutor stream only): Find out what they know and would teach.
  This is where structured extraction begins. The expert reveals what modules and topics their course covers.
  Set "tracking_mode": "extraction" on this module.
  The 7-slot component tracking applies ONLY here and in Day 2+.

Generate EXACTLY 4 Modules in this fixed order (3 for general stream — omit Module 3):

MODULE 1: "Personal Stories & Origins"  [tracking_mode: journalistic]
  Generate 4 topics inside this module:
  - Topic 1: "Early Career & How They Got Here" — opener about their non-linear path into this domain
  - Topic 2: "First Defining Experience" — the moment that shaped their professional identity
  - Topic 3: "Self-Description & Working Style" — how they see themselves as a practitioner
  - Topic 4: "The Learning Journey" — how they actually learned (self-taught? mentors? failures?)

MODULE 2: "Challenges & War Stories"  [tracking_mode: journalistic]
  Generate 4 topics inside this module:
  - Topic 1: "The Hardest Problem They've Ever Faced" — a specific story, not a generic answer
  - Topic 2: "A Public or Team Failure" — something that went catastrophically wrong and what happened
  - Topic 3: "Unwritten Rules & Industry Myths" — things the industry gets wrong that they learned the hard way
  - Topic 4: "The Turning Point" — the belief or approach that fundamentally changed after a failure

MODULE 3: "Curriculum Discovery"  [tracking_mode: extraction] — TUTOR STREAM ONLY
  Discover the high-level course identity and outline the curriculum structure.
  Generate EXACTLY 1 topic:
  - Topic 1: "Curriculum Design & Mapping" — ask the expert to describe the overall learning journey and why this course must exist.

MODULE 4: "Philosophy & Mental Models"  [tracking_mode: journalistic]
  Generate 3 topics inside this module:
  - Topic 1: "The Overarching Mental Model" — the one lens they see their entire domain through
  - Topic 2: "Contrarian Beliefs" — what does the expert believe that most people in their field disagree with?
  - Topic 3: "Advice & Future Outlook" — what they'd tell someone starting out today, and where the field is going

=== DAY 2+ (Iteration 2+) ===
You are now drilling into the curriculum the expert revealed in Module 3.
Each module = a major topic area the expert mentioned. Each topic = a sub-topic inside it.
All Day 2+ modules use tracking_mode: "extraction".
Identify topics that have missing components (edge_cases, action_items, constraints, evaluation_path).
Generate exploration vectors to extract those missing pieces.
Each module must contain 3-5 topics — do NOT collapse to 1 topic per module.

=== TWO TRACKING MODES — CRITICAL DISTINCTION ===

MODE: "journalistic"  (Modules 1, 2, 4 on Day 1)
  - Free-flowing podcast conversation. The expert is a person sharing their story.
  - The AI follows up naturally and moves on when the conversation reaches a natural beat.
  - target_objectives use simple narrative labels:
    ["origin_story", "defining_moment", "personal_heuristic"]
  - No rigid component gates. The system advances when the conversation naturally moves on.

MODE: "extraction"  (Module 3 on Day 1, ALL Day 2+ modules)
  - Structured knowledge extraction. The expert reveals curriculum content.
  - target_objectives MUST use the exact 7 knowledge slot names.
  - The coverage engine checks these after EVERY expert answer.
  - The system ONLY advances to the next topic when ALL required slots are satisfied.
  - The AI asks warm follow-up questions that organically elicit each slot — NOT direct "what are the edge cases?" questions.

The 7 extraction slot names (use ONLY in extraction mode):
  - "concept"          → Expert's own plain-language definition
  - "breakdown"        → Their step-by-step internal structure or process
  - "edge_cases"       → Situations where the normal rule breaks or behaves differently
  - "constraints"      → Limits, tradeoffs, "do NOT use when X" rules they've learned
  - "action_items"     → Hands-on steps/exercises for the learner to practice this
  - "evaluation_path"  → How the expert tests true understanding; what mastery looks like
  - "common_mistakes"  → Errors beginners consistently make with this topic
  - "expert_story"     → A lived personal experience they shared about this topic
  - "expert_heuristic" → Their rule-of-thumb, IF/THEN shortcut, gut-feeling signal

PODCAST TONE RULE (applies to ALL modules):
Every opener_question MUST sound like a real podcast host — warm, curious, journalistic. NOT a survey question.
BAD: "What are the main topics you would cover?"
GOOD: "If I were a fly on the wall in your best teaching session ever — the one where students just got it — what would I see you doing?"

OUTPUT FORMAT
Return a STRICT JSON object. Every module MUST have minimum 3 topics. Day 1 = exactly 4 modules (3 for general).
{{
  "estimated_total_duration_minutes": 120,
  "module_backlog": [
    {{
      "module_id": "m1",
      "module_title": "Personal Stories & Origins",
      "tracking_mode": "journalistic",
      "estimated_minutes": 40,
      "topics": [
        {{
          "topic_id": "m1_t1",
          "topic_title": "Early Career & How They Got Here",
          "opener_question": "Before we get into everything you teach — I want to start somewhere personal. What's the actual story of how you ended up in this field? Because I have a feeling it wasn't a straight line.",
          "exploration_vectors": [
            "Probe on whether it was accidental or intentional",
            "Find the first moment they realized this was their domain",
            "Ask if they considered a completely different career"
          ],
          "target_objectives": ["origin_story", "defining_moment", "personal_heuristic"],
          "estimated_minutes": 12
        }},
        {{
          "topic_id": "m1_t2",
          "topic_title": "First Defining Experience",
          "opener_question": "Take me back to the very first project or moment where you thought — okay, I actually know what I'm doing here. What happened?",
          "exploration_vectors": [
            "Get the specific story, not a summary",
            "What did they feel when it worked?",
            "What was at stake?"
          ],
          "target_objectives": ["origin_story", "defining_moment", "personal_heuristic"],
          "estimated_minutes": 10
        }},
        {{
          "topic_id": "m1_t3",
          "topic_title": "Self-Description & Working Style",
          "opener_question": "How would a colleague who's worked closely with you describe how you actually operate — not the polished version, the real one?",
          "exploration_vectors": [
            "Press for specifics, not generalities",
            "Ask about quirks or unusual habits",
            "What do they do that others find strange but that works for them?"
          ],
          "target_objectives": ["origin_story", "personal_heuristic", "defining_moment"],
          "estimated_minutes": 8
        }},
        {{
          "topic_id": "m1_t4",
          "topic_title": "The Learning Journey",
          "opener_question": "A lot of people in your field claim they learned from books or courses. But I suspect your real education came from somewhere messier. How did you actually learn this?",
          "exploration_vectors": [
            "Find the non-obvious learning sources",
            "Ask about mentors who changed their trajectory",
            "Find the thing they had to unlearn from formal education"
          ],
          "target_objectives": ["origin_story", "defining_moment", "personal_heuristic"],
          "estimated_minutes": 10
        }}
      ]
    }},
    {{
      "module_id": "m2",
      "module_title": "Challenges & War Stories",
      "tracking_mode": "journalistic",
      "estimated_minutes": 35,
      "topics": [
        {{
          "topic_id": "m2_t1",
          "topic_title": "The Hardest Problem They've Ever Faced",
          "opener_question": "Tell me about the hardest problem you've ever had to solve in {{expert_domain}}. Not the most complex technically — the one that actually kept you up at night.",
          "exploration_vectors": [
            "Get the specific story with stakes",
            "What was their decision-making process under pressure?",
            "What would have happened if they got it wrong?"
          ],
          "target_objectives": ["origin_story", "defining_moment", "personal_heuristic"],
          "estimated_minutes": 12
        }},
        {{
          "topic_id": "m2_t2",
          "topic_title": "A Public or Team Failure",
          "opener_question": "Everyone in your field has a story they don't put in their LinkedIn bio. Something that went badly wrong. What's yours?",
          "exploration_vectors": [
            "Get the real story, not the sanitized version",
            "What was the lesson they had to learn the hard way?",
            "How did it change how they operate today?"
          ],
          "target_objectives": ["origin_story", "defining_moment", "personal_heuristic"],
          "estimated_minutes": 10
        }},
        {{
          "topic_id": "m2_t3",
          "topic_title": "Unwritten Rules & Industry Myths",
          "opener_question": "What does everyone in {{expert_domain}} believe that you think is actually wrong — or at least way more nuanced than people admit?",
          "exploration_vectors": [
            "Find the contrarian belief backed by real experience",
            "What is the industry dogma they've personally disproven?",
            "Why do most people get this wrong?"
          ],
          "target_objectives": ["origin_story", "defining_moment", "personal_heuristic"],
          "estimated_minutes": 10
        }},
        {{
          "topic_id": "m2_t4",
          "topic_title": "The Turning Point",
          "opener_question": "Was there a moment — a specific project, failure, or conversation — where the way you think about {{expert_domain}} fundamentally changed?",
          "exploration_vectors": [
            "Find the before/after in their thinking",
            "What was the catalyst — was it a person, a failure, or a realization?",
            "How did this change their actual behavior or approach?"
          ],
          "target_objectives": ["origin_story", "defining_moment", "personal_heuristic"],
          "estimated_minutes": 8
        }}
      ]
    }},
    {{
      "module_id": "m3",
      "module_title": "Curriculum Discovery",
      "tracking_mode": "extraction",
      "estimated_minutes": 25,
      "topics": [
        {{
          "topic_id": "m3_t1",
          "topic_title": "Curriculum Design & Mapping",
          "opener_question": "Before we start mapping out the specific lessons or modules, I'd love to step back and understand the bigger picture: what is the core learning journey you want to take a student on, and why does this course need to exist?",
          "exploration_vectors": [
            "What is the overall transformation of the learner?",
            "What gap does this course fill that existing resources leave?",
            "Why is this specific journey critical?"
          ],
          "target_objectives": ["concept"],
          "estimated_minutes": 15
        }}
      ]
    }},
    {{
      "module_id": "m4",
      "module_title": "Philosophy & Mental Models",
      "tracking_mode": "journalistic",
      "estimated_minutes": 20,
      "topics": [
        {{
          "topic_id": "m4_t1",
          "topic_title": "The Overarching Mental Model",
          "opener_question": "If there's one lens — one way of thinking — that you use to navigate almost every decision in {{expert_domain}}, what is it?",
          "exploration_vectors": [
            "Get the IF/THEN rule or the metaphor they live by",
            "When does this mental model fail or not apply?",
            "Can they give a concrete example of using it recently?"
          ],
          "target_objectives": ["origin_story", "personal_heuristic", "defining_moment"],
          "estimated_minutes": 8
        }},
        {{
          "topic_id": "m4_t2",
          "topic_title": "Contrarian Beliefs",
          "opener_question": "What's the most important thing you believe about {{expert_domain}} that most of your peers would push back on?",
          "exploration_vectors": [
            "Why does the conventional wisdom get it wrong?",
            "Have they ever been burned by following the conventional wisdom?",
            "Is there a situation where the conventional approach IS right?"
          ],
          "target_objectives": ["origin_story", "personal_heuristic", "defining_moment"],
          "estimated_minutes": 7
        }},
        {{
          "topic_id": "m4_t3",
          "topic_title": "Advice & Future Outlook",
          "opener_question": "If you were starting fresh in {{expert_domain}} right now — today's tools, today's landscape — what would you do differently in the first 90 days?",
          "exploration_vectors": [
            "What's the fastest path to real competence today?",
            "What skill or habit is most undervalued by people entering the field?",
            "Where is {{expert_domain}} going in 3-5 years?"
          ],
          "target_objectives": ["origin_story", "personal_heuristic", "defining_moment"],
          "estimated_minutes": 5
        }}
      ]
    }}
  ]
}}
"""
