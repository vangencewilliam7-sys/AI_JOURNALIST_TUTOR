# AI Journalist - API Reference

## Overview
This document provides a comprehensive reference for the FastAPI backend endpoints powering the AI Journalist platform. All APIs currently bypass explicit token authentication, relying on frontend integration with Supabase for data access, while the backend utilizes an anonymous service key.

---

## Module 1: Intake & Script Generation (Phase 2)

### 1. `POST /intake`
- **Purpose:** Registers a new expert, calibrates their archetype via LLM, and generates the Day 1 icebreaker prompt.
- **Authentication:** None
- **Path Parameters:** None
- **Query Parameters:** None
- **Request Body (`application/json`):**
  ```json
  {
    "name": "string",
    "domain": "string",
    "stream_type": "string (general | tutor)",
    "course_title": "string (optional)",
    "course_description": "string (optional)",
    "target_audience": "string (optional)",
    "expertise_streams": ["string"],
    "years_of_experience": 0,
    "short_bio": "string (optional)",
    "linkedin_url": "string (optional)"
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "expert_id": "uuid",
    "session_id": "uuid",
    "icebreaker": { ... }
  }
  ```
- **Error Responses:** 
  - `422 Unprocessable Entity` (Invalid JSON body)
  - `500 Internal Server Error` (Database/LLM failure)
- **Database Interactions:** Inserts a new row into the `experts` table. Inserts a new row (Iteration 1) into the `interview_sessions` table.
- **Related Frontend Pages:** `/intake` (Expert Form)

### 2. `POST /generate-script/{expert_id}`
- **Purpose:** Generates the dynamic interview script/backlog for the active session, utilizing accumulated profile data and open homework loops.
- **Authentication:** None
- **Path Parameters:** `expert_id` (UUID of the expert)
- **Query Parameters:** None
- **Request Body:** None
- **Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "script": { "interview_arc": [...] },
    "expert": { "id": "...", "name": "..." }
  }
  ```
- **Error Responses:** `500 Internal Server Error`
- **Database Interactions:** Reads `experts`, `expert_profile`, `curriculum_blueprints`, and `homework_ledger`. Updates the `script` JSONB column in the active `interview_sessions` row.
- **Related Frontend Pages:** `/interview/[session_id]` (Initialization phase)

---

## Module 2: Live Interview Loop (Phase 3)

### 3. `GET /session/{session_id}`
- **Purpose:** Fetches the active session state, including the generated script and current raw transcript, to hydrate the frontend teleprompter.
- **Authentication:** None
- **Path Parameters:** `session_id` (UUID)
- **Query Parameters:** None
- **Request Body:** None
- **Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "session": {
      "id": "uuid",
      "script": {...},
      "raw_transcript": "string"
    }
  }
  ```
- **Error Responses:** `404 Not Found` (If session doesn't exist)
- **Database Interactions:** SELECT from `interview_sessions`.
- **Related Frontend Pages:** `/interview/[session_id]`

### 4. `POST /live-turn`
- **Purpose:** Analyzes the expert's last answer, decides whether to drill down on a tangent or move to the next script question, and generates the AI's follow-up question.
- **Authentication:** None
- **Path Parameters:** None
- **Query Parameters:** None
- **Request Body (`application/json`):**
  ```json
  {
    "session_id": "string",
    "expert_answer": "string",
    "current_script_question": "string (optional)",
    "active_block": "string (optional)",
    "tangent_count": 0
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "question": "string (Next AI spoken line)",
    "decision": {
      "action": "follow_tangent | next_script_question",
      "intent": "substantive | skip",
      "reasoning": "string"
    }
  }
  ```
- **Error Responses:** `404 Not Found`, `500 Internal Server Error`
- **Database Interactions:** Appends both the expert's answer and the AI's follow-up to `raw_transcript` in `interview_sessions`.
- **Related Frontend Pages:** `/interview/[session_id]` (Live recording loop)

### 5. `POST /transcribe`
- **Purpose:** Proxies audio blobs to Deepgram Nova-2 for real-time speech-to-text transcription.
- **Authentication:** None
- **Path Parameters:** None
- **Query Parameters:** None
- **Request Body:** `multipart/form-data` (File payload attached to `audio` field)
- **Response (`200 OK`):**
  ```json
  {
    "transcript": "string"
  }
  ```
- **Error Responses:** 
  - `502 Bad Gateway` (Deepgram API error)
  - `504 Gateway Timeout` (Deepgram took too long)
- **Database Interactions:** None.
- **Related Frontend Pages:** `/interview/[session_id]` (Microphone recording)

---

## Module 3: Synthesis & Homework (Phase 4 & 5)

### 6. `POST /end-session/{session_id}`
- **Purpose:** Triggers the massive post-interview synthesis pipeline. Extracts persona traits, tacit knowledge, course modules, and generates "homework" open loops for the next day.
- **Authentication:** None
- **Path Parameters:** `session_id` (UUID)
- **Query Parameters:** None
- **Request Body:** None
- **Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "message": "Session synthesized and homework generated.",
    "synthesis": { "general": {...}, "tutor": {...} },
    "homework": { "ai_open_loops": [...] }
  }
  ```
- **Error Responses:** `404 Not Found`, `500 Internal Server Error`
- **Database Interactions:** 
  - Updates `ended_at` and `session_synthesis` in `interview_sessions`.
  - Upserts JSONB arrays in `expert_profile` and `curriculum_blueprints`.
  - Inserts a new row in `homework_ledger`.
- **Related Frontend Pages:** `/interview/[session_id]` (On ending the interview)

### 7. `GET /homework/{expert_id}`
- **Purpose:** Fetches the most recent pending homework/open loops for the expert.
- **Authentication:** None
- **Path Parameters:** `expert_id` (UUID)
- **Query Parameters:** None
- **Request Body:** None
- **Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "homework": { "id": "...", "ai_open_loops": [...], "human_manual_notes": "..." }
  }
  ```
- **Error Responses:** `500 Internal Server Error`
- **Database Interactions:** SELECT from `homework_ledger` ORDER BY created_at LIMIT 1.
- **Related Frontend Pages:** `/dashboard/[expert_id]`

### 8. `PUT /homework/{homework_id}`
- **Purpose:** Allows the human journalist to manually input research notes to resolve AI-identified open loops.
- **Authentication:** None
- **Path Parameters:** `homework_id` (UUID)
- **Query Parameters:** None
- **Request Body (`application/json`):**
  ```json
  {
    "human_manual_notes": "string"
  }
  ```
- **Response (`200 OK`):**
  ```json
  { "status": "success" }
  ```
- **Error Responses:** `422 Unprocessable Entity`, `500 Internal Server Error`
- **Database Interactions:** Updates `human_manual_notes` and sets `status` to 'completed' in `homework_ledger`.
- **Related Frontend Pages:** `/dashboard/[expert_id]` (Homework Tab)

---

## Module 4: Flywheel Bridge (Phase 6)

### 9. `POST /start-session/{expert_id}`
- **Purpose:** Initializes a new iterative interview session (e.g., Day 2). Generates a trust-building "Flywheel Bridge" opening statement utilizing the resolved homework notes.
- **Authentication:** None
- **Path Parameters:** `expert_id` (UUID)
- **Query Parameters:** None
- **Request Body:** None
- **Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "session_id": "uuid",
    "iteration_number": 2,
    "opener": { "bridge_opener": "...", "internal_reasoning": "..." }
  }
  ```
- **Error Responses:** `500 Internal Server Error`
- **Database Interactions:** Reads `homework_ledger`. Inserts new row into `interview_sessions` with incremented `iteration_number`.
- **Related Frontend Pages:** `/dashboard/[expert_id]` (Clicking "Start Day X Session")

---

## Module 5: Knowledge Reports (Dashboard)

### 10. `GET /knowledge-report/{expert_id}`
- **Purpose:** Retrieves the fully accumulated state of the expert's synthesized knowledge, combining the Persona/Insights profile with the Curriculum Blueprint.
- **Authentication:** None
- **Path Parameters:** `expert_id` (UUID)
- **Query Parameters:** None
- **Request Body:** None
- **Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "expert_profile": { ... },
    "curriculum_blueprints": { ... }
  }
  ```
- **Error Responses:** `500 Internal Server Error`
- **Database Interactions:** SELECT from `expert_profile` and `curriculum_blueprints`.
- **Related Frontend Pages:** `/dashboard/[expert_id]` (Report & Course tabs)

---

## Module 6: RAG Ingestion

### 11. `POST /ingest`
- **Purpose:** Accepts PDF, TXT, or DOCX file uploads, chunks the text, generates vector embeddings, and stores them in the Supabase Vector Database. Processed asynchronously.
- **Authentication:** None
- **Path Parameters:** None
- **Query Parameters:** None
- **Request Body (`multipart/form-data`):**
  - `files`: List of files
  - `domain`: `string`
  - `user_session_id`: `string`
- **Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "message": "Processing 2 files in the background."
  }
  ```
- **Error Responses:** `500 Internal Server Error`
- **Database Interactions:** Background task inserts into `knowledge_sources` and `knowledge_chunks` (including 1536-dimensional embeddings).
- **Related Frontend Pages:** Potentially triggered from an ingestion UI or Dashboard (not heavily featured in standard intake flow).
