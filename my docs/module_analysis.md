# AI Journalist - Independent Module Analysis

**Crucial Context Check:** The AI Journalist platform is a specialized LLM-driven orchestration tool designed to interview domain experts and extract a syllabus. It is **not** a traditional Learning Management System (LMS). Therefore, while several of the requested modules exist, many (like Student Management or Cohorts) are inherently out of scope for the current codebase.

Below is the complete analysis of all requested modules based strictly on the current code.

---

## 1. Registration (Intake Module)
### 1. Business purpose
To capture the initial profile of the domain expert, determine their optimal interview archetype, and generate a customized Day 1 icebreaker question.
### 2. Frontend components
`LandingPage.tsx` (Intake Form capturing Name, Domain, Course Title, Experience).
### 3. Backend services
`InterviewDomain.intake()` in `backend/domains/interview.py`. Calls the `ARCHETYPE_CLASSIFIER_PROMPT`.
### 4. Database tables
`experts`, `interview_sessions`
### 5. APIs
`POST /intake`
### 6. Workflows
User submits form -> LLM calibrates archetype -> DB rows created -> UI stores `expert_id` in `localStorage` -> Redirects to Interview.
### 7. User actions
Filling out text fields, clicking "Start AI Interview".
### 8. Edge cases
User provides an extremely vague domain (e.g., "stuff"). The LLM handles this by defaulting to a generic `balanced` archetype.
### 9. Error handling
Frontend catches 500 errors and displays a toast notification. Backend returns 422 for missing required fields via Pydantic.
### 10. Dependencies
OpenAI API (GPT-4o-mini), Supabase.

---

## 2. Courses (Syllabus Extraction Module)
### 1. Business purpose
To dynamically extract, structure, and save a Coursera-style syllabus based entirely on the tacit knowledge discussed during the AI interview.
### 2. Frontend components
`DashboardPage.tsx` (Course Syllabus Tab rendering `curriculum_blueprints`).
### 3. Backend services
`InterviewDomain.synthesize()` -> specifically the `TUTOR_SYNTHESIS_PROMPT`.
### 4. Database tables
`curriculum_blueprints`, `courses` (V2 schema), `course_modules` (V2 schema).
### 5. APIs
`POST /end-session/{session_id}`, `GET /knowledge-report/{expert_id}`
### 6. Workflows
Host ends session -> Backend dumps transcript to LLM -> LLM formats JSON course structure -> UI renders modules and lessons.
### 7. User actions
Clicking "End Interview", viewing the generated syllabus on the dashboard.
### 8. Edge cases
The expert barely talked about course structure. The LLM is strictly instructed (Zero-Hallucination rule) to flag `knowledge_gaps` rather than hallucinate fake modules.
### 9. Error handling
If LLM outputs malformed JSON, backend falls back to regex extraction or logs the parsing failure.
### 10. Dependencies
LangChain, OpenAI GPT-4o.

---

## 3. Tutor Management (Expert Profiling Module)
### 1. Business purpose
To track the living identity of the expert across multiple sessions (Day 1, Day 2) and generate an AI system prompt that mimics their exact voice.
### 2. Frontend components
`DashboardPage.tsx` (Expert Persona Tab), `HomeworkPage.tsx`.
### 3. Backend services
`InterviewDomain.synthesize()`, `InterviewDomain.flywheel_bridge()`.
### 4. Database tables
`expert_profile`, `experts`, `homework_ledger`.
### 5. APIs
`GET /knowledge-report/{expert_id}`, `PUT /homework/{id}`, `POST /start-session/{id}`
### 6. Workflows
Session ends -> Traits and stories appended to profile -> AI identifies gaps -> Human fills gaps -> New session starts with context.
### 7. User actions
Journalist reviewing the extracted War Stories, inputting manual research notes into the Open Loops ledger.
### 8. Edge cases
Contradictory information between Day 1 and Day 2. Append-only JSON arrays handle this by retaining all instances.
### 9. Error handling
Missing database rows trigger 404s, gracefully caught by React Error Boundaries.
### 10. Dependencies
Supabase Python Client.

---

## 4. File Management (Ephemeral Processing Module)
### 1. Business purpose
To ingest syllabi or background documents to provide the AI with context without permanently storing sensitive files.
### 2. Frontend components
RAG Upload UI (if implemented; currently handled via backend utility scripts).
### 3. Backend services
`app.py -> background_ingest_documents()`, `ingest_data.py`.
### 4. Database tables
`knowledge_sources`, `knowledge_chunks`.
### 5. APIs
`POST /ingest`
### 6. Workflows
File uploaded -> Chunked by characters -> Embedded -> Vectors stored -> File deleted from OS.
### 7. User actions
Selecting files and clicking upload.
### 8. Edge cases
Massive PDFs causing OOM (Out of Memory) errors. Mitigated by streaming to temporary files on disk before processing.
### 9. Error handling
Unsupported file extensions (e.g., `.png`) are skipped with a warning log.
### 10. Dependencies
`fitz` (PyMuPDF), `python-docx`, `youtube_transcript_api`, OpenAI Embeddings.

---

## 5. ❌ Modules Not Implemented (Out of Scope)
The following modules were requested but **do not exist** in the AI Journalist codebase, as it is a syllabus-generation tool, not an LMS.

* **Assessment:** The system interviews the tutor; it does not grade students.
* **Cohorts:** There is no concept of grouping students.
* **Messaging:** There is no user-to-user chat functionality.
* **Analytics:** There is no tracking of user login times, video watch times, or completion rates.
* **Student Management:** There are no "Students" in the system, only "Experts/Tutors" and "Journalists".
* **Workshops:** No live event scheduling or video streaming components.
* **Notifications:** No email, SMS, or Push Notification integrations (e.g., SendGrid/Twilio are absent).
