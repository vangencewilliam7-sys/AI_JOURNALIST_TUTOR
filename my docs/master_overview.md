# AI Journalist - Master Project Overview

This document serves as the single comprehensive overview of the entire AI Journalist project, combining the product vision, the complete technology stack, and summaries of all architectural components into one unified guide.

---

## 1. Product Vision & Core Purpose
The AI Journalist is a specialized AI orchestration platform designed to replace human interviewers. Its primary business purpose is to interview domain experts, extract their tacit knowledge (unwritten rules, personal stories, anti-patterns), and automatically synthesize that knowledge into a structured Coursera-style curriculum. 

Instead of traditional conversational AI, it acts as a **State-Driven Teleprompter**, driving experts through a 6-phase framework (Intake ➔ Script Generation ➔ Live Interview ➔ Synthesis ➔ Homework ➔ Flywheel Bridge) over multiple days to prevent AI context-window exhaustion and human fatigue.

---

## 2. Technology Stack
The platform uses a modern, decoupled client-server architecture powered by specialized AI services.

### Frontend
* **Core:** React 18, Vite, TypeScript
* **Styling & UI:** Tailwind CSS, Radix UI Primitives, Lucide React (Icons), Framer Motion (Animations)
* **Routing:** React Router DOM
* **State Management:** Zustand (for global teleprompter state) + React Context
* **Audio Handling:** Native `MediaRecorder` API

### Backend
* **Core:** Python 3.x, FastAPI, Uvicorn
* **Data Validation:** Pydantic
* **Utilities:** `python-docx`, `PyMuPDF` (fitz), `youtube_transcript_api`, `httpx` (Async HTTP)

### AI & Machine Learning
* **LLM Provider:** OpenAI API (GPT-4o-mini for fast routing, GPT-4o for heavy synthesis)
* **Transcription:** Deepgram Nova-2 API (High-speed Automatic Speech Recognition)
* **Orchestration:** LangChain (Prompt chaining and RAG logic)
* **Embeddings:** OpenAI `text-embedding-3-small`

### Database & Infrastructure
* **Database:** Supabase (PostgreSQL)
* **Vector Store:** `pgvector` extension in Supabase
* **Deployment:** Docker & Docker Compose (Containerized microservices)

---

## 3. High-Level Architecture

The system operates on an asynchronous, decoupled loop to maintain high performance during live interviews:

1. **Frontend Capture:** The browser records microphone audio via `MediaRecorder` and sends small audio blobs to the backend.
2. **ASR Proxy:** FastAPI forwards the audio bytes to Deepgram and immediately receives the transcribed text.
3. **LLM Orchestration:** The transcribed text is sent to the LLM alongside a strict sliding-window of previous context to determine the next conversational action (drill down or move on).
4. **State Machine:** The frontend uses the LLM's response to advance the teleprompter UI, while the backend continuously appends the conversation to a monolithic transcript in the database.
5. **Post-Processing:** Once the session ends, heavy LLM tasks extract JSON-structured syllabi from the transcript and save them to Supabase.

---

## 4. Frontend Overview
* **Routing Structure:**
  - `/` (Landing / Intake Form)
  - `/interview/[session_id]` (The Live Teleprompter UI)
  - `/dashboard/[expert_id]` (The Synthesis Output & Course Syllabus viewer)
  - `/homework/[expert_id]` (The Open Loops & Research gap filler)
* **Component Design:** Built with modular, reusable UI pieces (e.g., `Button`, `Card`, `TranscriptViewer`).
* **State:** Driven by the `useInterview` hook, which syncs the local UI state with the backend's LLM responses, ensuring the teleprompter always knows what "Block" or "Phase" the interview is in.

---

## 5. Backend & API Overview
The FastAPI backend follows a simplified Domain-Driven Design (DDD). Routing is handled in `app.py`, while heavy business logic resides in `domains/interview.py`.

* **Key Endpoints:**
  * `POST /intake`: Registers the expert.
  * `POST /generate-script/{expert_id}`: Creates the custom interview script.
  * `POST /transcribe`: Proxies audio to Deepgram.
  * `POST /live-turn`: Determines the AI's next spoken line.
  * `POST /end-session/{session_id}`: Triggers the massive LLM syllabus extraction.
  * `POST /ingest`: Background task that chunks PDFs/Word docs into vectors for RAG.

---

## 6. Database Architecture
The platform runs on a **Hybrid JSON Architecture** within PostgreSQL (via Supabase).

* **Core Tables:**
  * `experts`: The root entity tracking the tutor's identity.
  * `interview_sessions`: Tracks the raw transcript for specific Day 1/Day 2 sessions.
  * `expert_profile` & `curriculum_blueprints`: These tables utilize heavily nested `JSONB` columns to store the output of the LLM (e.g., arrays of "War Stories", "Mental Models", and "Course Modules").
  * `homework_ledger`: Tracks missing knowledge gaps the AI couldn't fill.
  * `knowledge_chunks`: Stores the 1536-dimensional vector embeddings for RAG document retrieval.

---

## 7. Security, Auth, & File Management
* **Authentication:** Currently operating as a rapid prototype. True authentication (OAuth/JWTs) is bypassed. The system relies on a **pseudo-session** approach where the `expert_id` is stored in the browser's `localStorage` to navigate between pages.
* **Authorization:** No Role-Based Access Control (RBAC) is enforced yet; all endpoints utilize the anonymous Supabase key.
* **File Management:** Files are **ephemeral**. Audio blobs and uploaded PDFs are held in RAM or temporary OS folders just long enough to extract text/vectors, and are then explicitly destroyed. There is no permanent file storage (like S3 buckets) in this application.
