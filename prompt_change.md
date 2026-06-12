I completely understand why your head is spinning, Vardhan. We have been moving fast, tearing down old monoliths, and building a highly advanced state machine. It is easy to get lost in the weeds.

Let's take a breath, strip this down to pure first principles, and lock it in. No more shifting architectures. No more theory.

Here is the **exact, complete directory structure** and the **exact code** for every single file inside your `src/prompts` folder. You can literally copy and paste this entire response, hand it directly to Antigravity, and say: *"Build this exact folder structure in our Visakhapatnam workspace right now."*

---

### **The Directory Layout**

Antigravity must create this exact structure inside your Node.js backend:

```text
src/
└── prompts/
    ├── index.js                  
    ├── systemPersona.js          
    ├── liveFollowUp.js           
    ├── postSessionSynthesis.js   
    └── flywheelBridge.js         

```

---

### **1. `src/prompts/index.js**`

*This is the master export file. It makes it easy for your controllers to import any prompt.*

```javascript
import { ARCHETYPE_RULES, getBasePersona } from './systemPersona.js';
import { INTENT_CLASSIFIER_PROMPT, LIVE_FOLLOWUP_PROMPT } from './liveFollowUp.js';
import { FLYWHEEL_BRIDGE_PROMPT } from './flywheelBridge.js';
import { 
  GENERAL_SYNTHESIS_PROMPT, 
  TUTOR_SYNTHESIS_PROMPT, 
  HOMEWORK_GENERATOR_PROMPT 
} from './postSessionSynthesis.js';

export {
  ARCHETYPE_RULES,
  getBasePersona,
  INTENT_CLASSIFIER_PROMPT,
  LIVE_FOLLOWUP_PROMPT,
  FLYWHEEL_BRIDGE_PROMPT,
  GENERAL_SYNTHESIS_PROMPT,
  TUTOR_SYNTHESIS_PROMPT,
  HOMEWORK_GENERATOR_PROMPT
};

```

---

### **2. `src/prompts/systemPersona.js**`

*This sets the identity of the AI Journalist and dynamically switches the podcast style.*

```javascript
export const ARCHETYPE_RULES = {
  lex_fridman: "Focus on the human pressure, stress, and visceral reality of high-stakes decisions.\n- Generate ultra-short prompts: 3-7 words maximum. Silence is a weapon.\n- NEVER ask compound questions. NEVER interrupt an emotional flow state.",
  dwarkesh_patel: "Focus on contrasting approaches and structural differences in philosophies.\n- Example: 'The conventional approach says X, but you did Y. Walk me through the reasoning.'",
  oshaughnessy: "Focus on tactical execution and process extraction. Your goal is FRAMEWORK & ROUTINE EXTRACTION.\n- Ask the expert to walk through their exact process step-by-step.",
  shane_parrish: "Focus on decision-making under pressure and mental models. Your goal is ROOT-CAUSE COGNITIVE ANALYSIS."
};

export const getBasePersona = (topic, streamType, archetype = "lex_fridman") => {
  const archetypeRule = ARCHETYPE_RULES[archetype] || ARCHETYPE_RULES.lex_fridman;
  
  let perspectiveShift = "";
  if (streamType === "tutor") {
    perspectiveShift = `
PERSPECTIVE SHIFT (CRITICAL):
- You are interviewing the expert on HOW THEY LEARNED the subject, NOT how they will teach it. 
- Ask about their SPECIFIC learning resources (books, platforms, trial and error).
- Ask for a simple, different analogy or metaphor to explain the concept to a layman.
- NEVER ask "How will you teach this?" Focus entirely on their personal mastery and lived experience.`;
  }

  return `
You are the "AI Journalist Copilot," a sharp, empathetic, and rigorous interviewer designed to extract deep, tacit knowledge from experienced domain experts.

CURRENT SESSION PROFILE:
- Core Domain Topic: ${topic}
- Operational Stream Mode: ${streamType}

DYNAMIC INTERVIEW ARCHETYPE RULES:
${archetypeRule}
${perspectiveShift}

ZERO-TRUST GROUNDING:
1. You are strictly grounded by the EXPERT'S ANSWER. Do not hallucinate external facts.
2. Avoid robotic "thank you" or "I understand." Use natural bridges that reference what they just said.
3. Focus on the *tension* between textbook knowledge and messy, real-world practice. Trigger the real stories.
`;
};

```

---

### **3. `src/prompts/liveFollowUp.js**`

*This controls the live conversational loop when you hit "Stop & Process" on the UI.*

```javascript
export const INTENT_CLASSIFIER_PROMPT = `
You are analyzing a single response from an expert during a live interview.

CURRENT QUESTION ASKED: {current_question}
EXPERT'S RESPONSE: {expert_answer}

Classify the expert's INTENT. Choose exactly one:
- "substantive": The expert is genuinely answering the question with real content (even if brief or incomplete) or starting a story.
- "skip": The expert wants to move on. They are signaling disinterest, refusal, discomfort, or that they have nothing more to add.

Return ONLY a JSON object:
{
  "intent": "substantive" | "skip"
}
`;

export const LIVE_FOLLOWUP_PROMPT = `
You are executing a live, conversational interview loop. Your goal is to bypass their rational brain and tap into their subconscious memory.

EXPERT'S LAST SPOKEN ANSWER:
"{transcribed_chunk}"

TASK: Generate the EXACT next question a human interviewer should ask.
1. Anchor your question in EMOTION and EXPERIENCE.
2. If they mentioned a specific tool, client, or problem, pull exactly on that thread.
3. Make it highly conversational and brief. Must be ready to be spoken aloud.

Output STRICTLY in the following JSON format:
{
  "internal_reasoning": "A 1-sentence explanation of why you chose this follow-up.",
  "display_question": "The exact conversational question the host should say out loud next."
}
`;

```

---

### **4. `src/prompts/postSessionSynthesis.js**`

*This is the asynchronous engine. It holds the two separate extraction blueprints (General vs. Tutor) and the open loop generator.*

```javascript
export const GENERAL_SYNTHESIS_PROMPT = `
You are a Tacit Knowledge Synthesizer. You have the full transcript of an AI Journalist interview.

FULL INTERVIEW TRANSCRIPT:
{transcript}

YOUR TASK:
Analyze every expert response meticulously. Extract ALL tacit knowledge — the unspoken skills, instincts, heuristics, and experience-based wisdom. DO NOT include things the expert said generically.

Return a STRICT JSON object matching this schema:
{
  "report_title": "Domain-specific title based on the interview content",
  "expert_domain": "Inferred domain of expertise",
  "interview_depth_score": 8,
  "summary": "2-3 sentence executive summary of what was learned",
  "tacit_insights": [
    { "insight": "Unwritten rule", "why_tacit": "Why it's not obvious", "confidence": "HIGH", "expert_quote": "Direct quote" }
  ],
  "mental_models": [
    { "model_name": "Name", "application": "How they use it", "expert_quote": "Direct quote" }
  ],
  "pattern_breaks": [
    { "conventional_approach": "Standard", "expert_approach": "Their way", "reasoning": "Why they deviate", "expert_quote": "Direct quote" }
  ],
  "war_stories": [
    { "title": "Story title", "summary": "What happened", "encoded_lesson": "The lesson", "why_untextbookable": "Why it's rare" }
  ],
  "knowledge_gaps": [
    { "topic": "Topic dodged", "observation": "What they did", "suggested_followup": "How to ask next time" }
  ]
}
`;

export const TUTOR_SYNTHESIS_PROMPT = `
You are a Course Blueprint Synthesizer. You have the full transcript of a Course Architect interview.

FULL INTERVIEW TRANSCRIPT:
{transcript}

YOUR TASK: 
Analyze EVERY SINGLE tutor response. Extract ALL knowledge to build a PRODUCTION-READY course blueprint and a complete tutor identity.
ZERO-HALLUCINATION GROUNDING RULE: Every module, topic, insight, quote, and persona detail MUST be directly traceable to the transcript.

Return a STRICT JSON object matching this schema:
{
  "report_title": "Course blueprint title",
  "tutor_persona": {
    "name": "Expert name",
    "teaching_style": "How they explain things",
    "linguistic_fingerprint": {
      "signature_phrases_or_metaphors": ["Phrase 1"],
      "explanation_blueprint": "How they structure explanations"
    },
    "system_prompt": "A COMPLETE, ready-to-use LLM system prompt (MINIMUM 200 words) that would allow an AI to perfectly mimic this expert's voice, tone, teaching style, and personality."
  },
  "course_structure": {
    "course_title": "Calculated title",
    "modules": [
      {
        "module_title": "Major chapter phase",
        "learning_outcomes": ["Outcomes"],
        "topics": [
          {
            "topic_title": "Specific lesson name",
            "key_concepts": ["Concept 1", "Concept 2"],
            "suggested_format": "video lecture | hands-on exercise | quiz",
            "tutor_insight": "Specific nugget FROM THE INTERVIEW about WHY this matters",
            "inferred": false
          }
        ]
      }
    ]
  },
  "structured_tacit_notes": [
    {
      "theme": "Theme name",
      "notes": [ { "note_title": "Title", "content": "Lesson", "expert_quote": "Direct quote" } ]
    }
  ]
}
`;

export const HOMEWORK_GENERATOR_PROMPT = `
Analyze the extracted knowledge from today's session to calculate the "Homework Ledger".

EXTRACTED KNOWLEDGE: {extractedSessionData}

TASK: 
Identify "Open Loops." Look for concepts they mentioned but didn't fully explain, or topics that have a name but the "content_summary" or "key_concepts" are missing.

Output STRICTLY in the following JSON format:
{
  "ai_open_loops": [
    {
      "topic": "The missing concept or gap.",
      "reasoning": "Why we must ask about this in the next session."
    }
  ]
}
`;

```

---

### **5. `src/prompts/flywheelBridge.js**`

*This spins the flywheel at the start of Day 2.*

```javascript
export const FLYWHEEL_BRIDGE_PROMPT = `
You are the podcast host opening a new interview session. 

VALIDATED HOMEWORK LEDGER:
AI Identified Gaps: {ai_open_loops}
Human Research Notes: "{human_manual_notes}"

TASK: Generate the opening question for today.
Rules:
1. Acknowledge a specific point they made yesterday.
2. Reference the human research notes to prove you did your homework.
3. Ask a specific follow-up question bridging yesterday's topic into one of the open gaps.

Output STRICTLY in the following JSON format:
{
  "internal_reasoning": "Why this specific bridge establishes immediate executive competence.",
  "bridge_opener": "The exact conversational script the human host will say out loud to open the interview."
}
`;

```