System Architecture Document for Antigravity (AI Coding Agent)
Core System Directive for Antigravity:
This application is NOT a standard conversational chatbot. Do not implement continuous text-streaming chat UI. This system is a state-driven interview teleprompter that utilizes offline, asynchronous LLM synthesis to prevent context bloat. You must adhere strictly to the phase logic below.

Phase 1: The Database Foundation (Supabase)
What this phase is: The creation of the relational database schema and JSONB storage structures.

What it actually does: It replaces traditional "raw chat history" with structured memory. Instead of storing 10,000 words of dialogue, we store the extracted concepts to feed into future prompts.

Antigravity Implementation Rules:

Create tables using PostgreSQL.

experts table: Stores name, domain, and stream_type (general or tutor).

expert_profile table: Must use JSONB arrays for persona_traits, war_stories, mental_models, and edge_cases.

curriculum_blueprints table: Must use a nested JSONB object for course_modules.

interview_sessions table: Stores the raw_transcript for audit only, and a session_synthesis JSONB object.

homework_ledger table: Stores ai_open_loops (JSONB) and human_manual_notes (Text).

Crucial Logic: Code all database update functions to append to JSONB arrays (using PostgreSQL jsonb_insert or equivalent), never overwrite existing arrays.

Phase 2: The Intake Flow
What this phase is: The initial onboarding of a new expert before any interviews take place.

What it actually does: It collects the expert's metadata and generates the very first "Icebreaker" question so the human interviewer doesn't start with a blank screen.

Antigravity Implementation Rules:

Build a React form to capture Name, Domain, and Stream Type.

On submit, hit a Node.js endpoint (/api/intake).

The backend creates the expert record in Supabase and fires a prompt to the LLM asking for a "Day 1 Interview Strategy."

Store the resulting Icebreaker question in the React state to display on the interview screen.

Phase 3: The Live Interview Loop (The State Machine)
What this phase is: The actual interview screen where the human talks to the expert.

What it actually does: It controls the flow of audio capture and question generation. It completely decouples the AI processing from the live conversation to prevent lag and hallucinations.

Antigravity Implementation Rules:

Do not build a chat window. Build a prominent text display (the Teleprompter) and a primary Action Button.

State 1 (READY): The screen displays the current question. The Action Button says "Start Recording".

State 2 (PAUSED_RECORDING): The human clicks the button. The UI locks. Trigger the browser's MediaRecorder API to capture the audio of the human speaking and the expert answering. The LLM is completely idle here.

State 3 (PROCESSING): The human clicks "Stop & Process". Stop the MediaRecorder. Send the audio blob to the Node.js backend.

Backend Logic: Transcribe the audio (e.g., Whisper API). Take only this new transcript chunk, send it to the LLM to generate the next logical follow-up question, and return that question to the React frontend. Loop back to State 1.

Phase 4: Post-Session Asynchronous Synthesis
What this phase is: The data extraction pipeline that runs after the human clicks "End Session" for the day.

What it actually does: It reads the messy, raw transcript from that day and extracts pure, structured knowledge into the Supabase JSONB tables. This is the core engine that prevents LLM memory loss.

Antigravity Implementation Rules:

Create a background worker endpoint in Node.js (/api/synthesize-session).

Universal Extraction: Feed the full day's transcript to the LLM. Instruct it to extract persona_traits, war_stories, and edge_cases. Append these to the expert_profile table.

Conditional Routing: Read the expert's stream_type. If it is tutor, run a second LLM call instructing it to extract modules, topics, and content. Upsert this into the curriculum_blueprints table.

Phase 5: The Hybrid Homework Ledger
What this phase is: The bridge between interview days where missing knowledge is identified.

What it actually does: It forces the AI to figure out what the expert forgot to explain, and gives the human a dashboard to manually correct or research those gaps.

Antigravity Implementation Rules:

Immediately after Phase 4 completes, run a final LLM prompt on the extracted data to identify "Open Loops" (topics mentioned but not fully explained).

Save these to homework_ledger.ai_open_loops.

Build a React Dashboard View for the human to review these loops. Provide a text area for human_manual_notes where the human can type their own research. Save this to the ledger.

Phase 6: Day 2+ Flywheel Bridge (Session Reactivation)
What this phase is: The generation of the very first question when starting Session 2, Session 3, etc.

What it actually does: It proves to the expert that the system "remembered" yesterday's chat by generating a highly specific opening question based on the Homework Ledger.

Antigravity Implementation Rules:

When the human clicks "Start Session" on an existing expert, hit a Node.js endpoint (/api/day2-bridge).

Strict Constraint: Do NOT load previous raw transcripts. Fetch only the completed homework_ledger from Supabase.

Pass the ledger to the LLM and instruct it to generate a "Trust-Signal Opener" that acknowledges yesterday's topic and asks a follow-up based on the research gaps.

Return this question to the React frontend and initiate Phase 3 (State 1).














WHERE I NEED PROMPTS HERE: 

Here is the complete inventory of every system prompt you need for the AI Journalist framework. These are designed for your Node.js backend to enforce strict JSON outputs, preventing hallucinations and ensuring the frontend receives clean data.

1. The Intake Phase (Before the Interview Starts)
Where it is used: In the Node.js backend when you submit the initial expert details.
Purpose: To generate the Day 1 strategy and the very first question to start the podcast smoothly without diving into heavy technical details.

JavaScript
const intakeSystemPrompt = `
You are an elite podcast producer preparing a host for a deep-dive interview with an industry expert. The interview style should feel like long-form, curious storytelling (e.g., Lex Fridman).

Expert Name: ${expertName}
Domain: ${expertDomain}
Stream Type: ${streamType} // General or Tutor

Generate a Day 1 strategy to make this expert comfortable. Do not ask for technical architecture, syllabus, or deep edge-cases yet. Focus entirely on their origins, early struggles, and career journey.

Output STRICTLY in the following JSON format. Do not include markdown formatting or extra text outside the JSON object.
{
  "context_brief": "A 2-sentence summary of what this domain typically entails to prep the host.",
  "opening_icebreaker": "A specific, conversational opening question asking how they broke into this field.",
  "listening_cues": ["Cue 1", "Cue 2"] // Specific topics or themes the host should listen for to branch deeper.
}
`;
2. The Live Interview Loop (The Pause/Unpause Engine)
Where it is used: In the backend when you click "Stop & Process (Unpause)" during the live recording.
Purpose: To take the newly transcribed audio chunk and instantly generate the next conversational follow-up question for you to read.

JavaScript
const liveFollowUpPrompt = `
You are a deeply curious interviewer in the middle of a live conversation. Your goal is to extract tacit knowledge, unwritten rules, or war stories without sounding like a robotic script.

Expert's last spoken answer: "${transcribedAudioChunk}"

Generate the NEXT logical question. 
Rules:
1. Make it highly conversational and brief. It must sound natural when spoken out loud by a human.
2. If they mentioned a specific tool, client, or problem, ask exactly how they handled it.
3. Do not change the subject abruptly. Pull on the thread they just handed you.

Output STRICTLY in the following JSON format.
{
  "internal_reasoning": "A 1-sentence explanation of why you chose this follow-up.",
  "display_question": "The exact conversational question the host should say out loud next."
}
`;
3. The Post-Session Universal Extraction
Where it is used: When you click "End Session". Runs asynchronously in the background.
Purpose: To read the entire day's transcript and extract the raw facts into the database so you do not have to store the full transcript in the AI's memory.

JavaScript
const universalExtractionPrompt = `
You are an elite Knowledge Extraction Agent. Analyze the following raw interview transcript from today's session.

Transcript: "${fullSessionTranscript}"

Ignore conversational filler. Extract the deep, tacit knowledge and categorize it. 

Output STRICTLY in the following JSON format.
{
  "persona_traits": ["Trait 1", "Trait 2"], // How they think or approach problems (e.g., First Principles thinking).
  "war_stories": [
    {
      "context": "The situation or client problem.",
      "action": "The specific action the expert took.",
      "result": "The outcome."
    }
  ],
  "mental_models": [
    {
      "concept": "Name of the concept.",
      "definition": "How they define it in their own words."
    }
  ],
  "edge_cases": [
    {
      "scenario": "The weird or unusual problem they encountered.",
      "solution": "Their specific, undocumented fix."
    }
  ],
  "synthesis_summary": "A highly compressed, 3-sentence summary of today's core value."
}
`;
4. The Post-Session Curriculum Extraction (Tutor Stream Only)
Where it is used: Immediately after the Universal Extraction, but only if the stream_type is set to tutor.
Purpose: To map out the teaching syllabus based on whatever the expert naturally discussed that day.

JavaScript
const tutorCurriculumPrompt = `
You are a Curriculum Architect. Analyze the following interview transcript and map out the teaching structure the expert discussed today.

Transcript: "${fullSessionTranscript}"

Look for high-level chapters (Modules) and the specific lessons within them (Topics). Do not invent content; only extract what was spoken.

Output STRICTLY in the following JSON format.
{
  "course_modules": [
    {
      "module_name": "Name of the module",
      "topics": [
        {
          "topic_name": "Name of the topic",
          "content_summary": "What they explicitly taught about this today. LEAVE THIS BLANK if they mentioned the topic name but did not explain how to do it yet."
        }
      ]
    }
  ]
}
`;
5. The Homework Generator (Open Loops)
Where it is used: Runs right after the extraction passes are complete.
Purpose: To figure out what the expert forgot to explain so you can populate the Hybrid Homework Dashboard.

JavaScript
const homeworkGeneratorPrompt = `
Analyze the extracted knowledge from today's session. Your job is to identify "Open Loops."

Extracted Knowledge: ${JSON.stringify(extractedSessionData)}

Look for:
1. Concepts or tools they mentioned but did not fully explain.
2. Problems they brought up without giving the solution.
3. (If Curriculum Data exists): Topics that have a name, but the "content_summary" is blank.

Output STRICTLY in the following JSON format.
{
  "ai_open_loops": [
    {
      "topic": "The missing concept or gap.",
      "reasoning": "Why we must ask about this in the next session to complete the profile."
    }
  ]
}
`;
6. The Flywheel Spin (Session 2+ Bridge Opener)
Where it is used: When you click "Start Session" on a subsequent day (Day 2, Day 3, etc.).
Purpose: To generate the Trust-Signal Opener that proves you did your homework and gets the expert to open up immediately.

JavaScript
const dayTwoBridgePrompt = `
You are the podcast host opening a new interview session. 

Here is the validated homework ledger from yesterday's session:
AI Identified Gaps: ${JSON.stringify(homeworkLedger.ai_open_loops)}
Human Research Notes: "${homeworkLedger.human_manual_notes}"

Generate the opening question for today. 
Rules:
1. Acknowledge a specific point they made yesterday.
2. Reference the human research notes to prove you did your homework.
3. Ask a specific follow-up question bridging yesterday's topic into one of the open gaps.
4. Sound natural, curious, and highly competent.

Output STRICTLY in the following JSON format.
{
  "internal_reasoning": "Why this specific bridge was chosen.",
  "bridge_opener": "The exact conversational script the human host will say out loud to open the interview."
}
`;