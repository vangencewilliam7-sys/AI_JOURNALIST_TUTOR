1. Executive Summary & Design PhilosophyProject AJ is a stateful, multi-agent AI framework engineered to solve the Tacit Knowledge Extraction Problem. Conventional knowledge management systems rely on experts self-reporting their knowledge, resulting in shallow, explicit data collection. AJ models the investigative rigor of world-class journalists to systematically surface subconscious frameworks, operational instincts, and unrecorded edge cases through an automated, human-in-the-loop interviewing loop called The Flywheel.The Core Architectural Paradigm: The Stateful State-MachineThis system is strictly architected as a deterministic state-machine where Large Language Models (LLMs) function purely as ephemeral, stateless context transformers. The application state is permanently anchored inside an external relational database layer.To achieve industrial reliability, high throughput, and zero structural hallucinations, the system relies on Staged Context Injection and Single-Pass Structured JSON Schemas.2. Comprehensive A-to-Z System TopologyThe diagram below maps the runtime architecture, execution boundaries, data routing layers, and database transition states across the entire 6-phase engineering framework.┌────────────────────────────────────────────────────────────────────────────────────────┐
│ UI LAYER (React TypeScript SPA Framework)                                              │
└───────────┬───────────────────┬────────────────────▲────────────────────▲──────────────┘
            │                   │                    │                    │
   (Phase 1: Profile)  (Phase 3: Live Input)  (Phase 2 Script)     (Phase 5/6 Dashboard)
            │                   │                    │                    │
┌───────────▼───────────────────▼────────────────────┴────────────────────┴──────────────┐
│ RUNTIME ORCHESTRATION LAYER (FastAPI Enterprise Engine)                                 │
└───────────┬───────────────────┬────────────────────▲────────────────────▲──────────────┘
            │                   │                    │                    │
            │ [POST /initialize]│ [POST /stream-turn]│ [JSON Stream]      │ [Hydrated Context]
            ▼                   ▼                    │                    │
┌────────────────────────────────────────────────────┴────────────────────┴──────────────┐
│ AI MULTI-AGENT EXECUTION ENGINE (LangChain / Native Gemini 1.5 Pro Matrix)             │
│                                                                                        │
│  [PROMPT 1: Day One Opener] ──> Synthesizes Emotional Core Hook                        │
│                                                                                        │
│  [PROMPT 2: Script Architect] ──> Generates 5-Phase Blueprint Matrix                   │
│                                                                                        │
│  [PROMPT 3: Live Copilot Engine] ──> Single-Pass Intent + Follow-up Router             │
│                                                                                        │
│  [PROMPT 4/5: Multi-Agent Extraction Worker] ──(Async Concurrent Execution)            │
│       ├── Agent A: Tacit Knowledge Synthesizer ──> Structure Matrix Block              │
│       └── Agent B: Open-Loop Gap Hunter ──────────> Structural Fragment Isolation      │
│                                                                                        │
│  [PROMPT 6: Flywheel Bridge Builder] ──> Contextual Trust-Signal Ingestion             │
└───────────────────────┬─────────────────────────────────────────────────┬──────────────┘
                        │                                                 ▲
                [Write / Append]                                      [Read State]
                        ▼                                                 │
┌─────────────────────────────────────────────────────────────────────────┴──────────────┐
│ DATABASE & STATE STORAGE LAYER (Supabase Infrastructure / PostgreSQL 16)               │
│                                                                                        │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────────────┐  │
│  │ experts              │  │ interview_sessions   │  │ expert_profile               │  │
│  │ ──────────────────── │  │ ──────────────────── │  │ ──────────────────────────── │  │
│  │ pk: expert_id (UUID) │  │ pk: session_id (UUID)│  │ pk: profile_id (UUID)        │  │
│  │ name: VARCHAR        │  │ fk: expert_id (UUID) │  │ fk: expert_id (UUID)         │  │
│  │ domain: VARCHAR      │  │ raw_transcript: TEXT │  │ tacit_matrix: JSONB (Append) │  │
│  │ experience: INT      │  │ script: JSONB Matrix │  │ curriculum: JSONB            │  │
│  └──────────────────────┘  └──────────────────────┘  └──────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
3. The 5-Phase Investigative Framework (Deep Justification)To extract tacit knowledge, standard informational questions fail. The system's Script Architect (Prompt 2) is structurally bound to a 5-Phase Psychological Extraction Model designed to break down a professional's cognitive defenses systematically.Phase NumberPhase NameArchitectural & Psychological ObjectiveData FocusPhase 1Warmup (Contextual Anchoring)Establishes absolute psychological safety and mutual trust. Prompts the expert to recount historical personal narratives, removing their rehearsed corporate presentation filter.Origin stories, early industry pivots, formative failures.Phase 2Deep Dive (System Mechanics)Maps the explicit operational realities. Captures how the expert interfaces with systems, tools, and processes on a day-to-day basis.Tool stacks, precise workflows, baseline delivery rules.Phase 3Friction Post-MortemThe Structural Core of Tacit Knowledge. Forces the expert to detail high-stakes operational crises. Human instincts reveal themselves only when standard manuals fail.Production crashes, architectural rebuilds, 3 AM improvisations.Phase 4Paradigm ChallengeAn analytical audit. Introduces structural friction by forcing the expert to defend their custom frameworks against highly validated industry standards or conventional wisdom.Non-consensus beliefs, contrarian methods, pattern breaks.Phase 5Synthesis (Compression Trap)Forces immediate cognitive compression. Demands the expert convert decades of complex operational execution into highly primitive, immutable execution laws.Mental models, operational heuristics, rules of thumb.4. End-to-End Functional Specification (Phases 1 to 6)Phase 1: Intake & Ephemeral Profile InitializationWhat Happens: The host fills out the primary configuration variables inside the React UI initialization matrix. Upon save, the backend instantly issues an isolated LLM execution call.The AI Mechanics: The LLM evaluates the target domain and experience index to construct an emotionally targeted, narrative-driven entry question.System Prompt Configuration:PlaintextRole: Lead Production Interviewer
Task: Generate an isolated Day One Opener question based on:
- Expert: {{EXPERT_NAME}}
- Domain: {{CORE_DOMAIN}}
- Yrs Exp: {{YEARS_OF_EXPERIENCE}}

Constraints:
1. Output exactly ONE single question. Zero pre-text or post-text.
2. The question must bypass standard resume details and force a personal story about how they originally survived the chaos of this field.

Format Enforcer:
<day_one_opener>[Question Text]</day_one_opener>
State Impact: Writes a new record to the experts table. Returns the clean XML string directly to the frontend header display block.Phase 2: Dynamic Script Architecture BlueprintingWhat Happens: Runs immediately prior to the user entering the live interview room.The AI Mechanics: The AI ingests the initialized data schema. It designs a tailored 5-phase sequential interview roadmap containing exactly two deep questions per phase.System Prompt Configuration (Structured JSON Strategy):PlaintextRole: Executive Script Architect
Task: Generate a 10-question structural interview matrix mapped across the 5 Investigative Phases.

Constraints:
- You must strictly output the response inside a valid JSON array matching the provided schema.
- Every question must include a data-driven rationale explaining the psychological or technical intent behind it.

JSON Schema Enforcer:
[
  {
    "phase_number": 1,
    "phase_name": "Warmup",
    "question_index": 1,
    "question_text": "string",
    "rationale": "string"
  }
]
State Impact: Hydrates interview_sessions.script as a structured JSONB payload. The frontend loops through this matrix to populate the teleprompter component.Phase 3: The Live Teleprompter & Real-Time Copilot LoopWhat Happens: The interview executes live. The host uses the teleprompter as the operational spine, while the AI listens continuously to every transaction.The AI Mechanics (The Latency Shield): Executing sequential calls for intent parsing and text generation is prohibited due to critical network lag. The system triggers a Single-Pass Structural Engine. It passes the active teleprompter question along with the last three context turns to evaluate intent and output follow-up variants simultaneously.System Prompt Configuration:PlaintextRole: Real-Time Interview Copilot
Inputs:
- Active Script Question: {{ACTIVE_QUESTION}}
- Context History: {{LAST_THREE_TURNS}}

Task: Analyze the final user response turn. Classify if the response is "substantive" (rich in tacit data, hooks, or emotional friction) or "skip" (shallow, defensive, or indicating topic exhaustion). If substantive, generate a sharp, conversational follow-up matching a world-class investigative reporter.

Output Schema Enforcer (Zero Prose Allowed):
{
  "intent": "substantive" | "skip",
  "internal_reasoning": "string",
  "follow_up_question": "string"
}
State Impact: Appends each transaction block to interview_sessions.raw_transcript. If intent == skip, the React app moves the teleprompter selector down; if substantive, it streams the follow-up text to the copilot alert panel.Phase 4: Multi-Agent Knowledge SynthesisWhat Happens: Triggered asynchronously when the session is closed by the host.The AI Mechanics: An asynchronous backend script spawns concurrent worker threads using asyncio.gather(). Worker 1 executes dense qualitative feature extraction to map paragraphs of real-world insights, ensuring no low-level operational mechanical descriptions are lost.System Prompt Configuration:PlaintextRole: Advanced Knowledge Synthesizer
Task: Parse the raw interview transcript and extract high-density knowledge blocks.
Categories: Personal Narratives, Tactical Domain Mechanics, Pattern Breaks, War Stories, Mental Models.

Constraints:
1. Do not output bulleted lists. 
2. You must output deep, exhaustive, fully-formed paragraphs containing the complete operational context of every claim made by the expert.
State Impact: Executes an UPDATE on expert_profile.tacit_matrix using a PostgreSQL JSONB append sequence (jsonb_concat), preserving historical state without destructive overwrites.Phase 5: The Homework Ledger & Negative Space MiningWhat Happens: Runs concurrently with Phase 4 during post-session cleanup.The AI Mechanics (The Open-Loop Hunter): The model parses the raw text explicitly seeking "negative space"—unresolved conversational cliffhangers where the expert dropped an incredibly high-value hook but the host or copilot failed to pursue it.System Prompt Configuration:PlaintextRole: Investigative Editor
Task: Identify highly valuable "open loops" or dropped conversational threads within the transcript.
Example: Expert says "we fixed the database crash by re-writing the cache at 3 AM, but anyway, then we changed teams..." -> Dropped thread: The 3 AM cache rewrite mechanics.

Output Schema Enforcer:
[
  {
    "loop_id": "string",
    "context_hook": "string",
    "unresolved_gap_description": "string"
  }
]
State Impact: Inserts entries into homework_ledger.ai_open_loops.The Human-in-the-Loop Gatekeeper: The application halts progress here. It loads Screen 5 (The Homework Dashboard). The system presents the AI-identified loops alongside a blank text area wrapper (homework_ledger.human_manual_notes). The host inputs manual overnight research, context notes, or explicit directions here. Progress is locked until this manual validation state is committed.Phase 6: The Flywheel Bridge EngineWhat Happens: Triggered manually by clicking "Trigger Flywheel Bridge" to spin up the next major tracking iteration.The AI Mechanics: The prompt ingests the precise context loops from Phase 5 combined with the host's manual verification notes. It synthesizes an elite opening sequence script for Day 2.System Prompt Configuration:PlaintextRole: Master Speechwriter
Task: Synthesize a highly strategic, hyper-contextualized opening monologue for Day 2 of the interview.
Inputs:
- Historical Open Loops: {{AI_OPEN_LOOPS}}
- Host Manual Research: {{HUMAN_MANUAL_NOTES}}

Constraints:
1. Write the script exactly from the perspective of the human host addressing the expert.
2. The script must explicitly reference the expert's previous statements and weave in the new manual research notes.
3. This must function as a deep "trust signal" proving comprehensive listening occurred.

Format Enforcer:
<flywheel_bridge_script>[Streaming Text Data]</flywheel_bridge_script>
State Impact: The system initializes a new row entry inside interview_sessions with iteration_number += 1. The generated bridge script streams via a typewriter UI component onto Screen 5. Clicking "Launch Session" pushes the application context back to Phase 2, where the script generator consumes the updated expert_profile data to build a highly targeted Day 2 script.5. Architectural Mandates: Guardrails, Do's & Don'tsStrict Engineering Mandates (DO)Enforce JSON Schema Validations at API Level: All structural outputs from Prompts 2, 3, and 5 must be validated against Pydantic models in FastAPI before database routing occurs. If a validation error trips, catch the exception and run an immediate low-token repair prompt.Use Context Sliding Windows for Live Tracking: Never feed an expanding raw text transcript into the live copilot engine. Cap the history parameter array to exactly the last 3 turns of active dialogue to keep execution times under 1.5 seconds.Execute Phase 4 and Phase 5 Concurrently: Utilize explicit asynchronous scheduling mechanisms in Python to trigger knowledge extraction and gap analysis simultaneously, reducing overall database block latency.Prohibited Operations (DON'T)NEVER Automate the Phase 5 to Phase 6 Transition: The system must never auto-generate the Day 2 opening sequence without waiting for the host's manual research input. Automation removes human editorial oversight, leading to repetitive or shallow conversational trajectories.NEVER Allow Destructive Overwrites on Profiles: The expert_profile table must remain strictly append-only. Overwriting records strips out foundational historical context, breaking the downstream semantic capability of the RAG engine over multiple sessions.NEVER Allow Conversational Meta-Prose in System API Outputs: Every prompt must use strict formatting rules or XML isolation wrappers. If an LLM returns fluff like "Sure, let me generate that question for you", it will break your backend parsing mechanisms and crash the user interface.