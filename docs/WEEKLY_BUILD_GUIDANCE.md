# AI Journalist Digital Twin — Developer Build Guidance

## Overview
This document provides practical implementation steps, module wiring patterns, prompt engineering specifications, and error-handling strategies to guide developers in building and extending the **Homework Ledger**, **Knowledge Extraction Engine**, and **Session Continuity Framework**.

---

## 1. Module Wiring & Core Dependencies

### Backend Directory Structure
```text
backend/
├── app.py                     # Route handlers & WebSocket session manager
├── dependencies.py            # Supabase JWT auth verification (`get_current_expert_id`)
├── domains/
│   └── interview.py           # Core domain state machine (`InterviewDomain`)
└── migrations/
    └── verification_evidence_schema.sql # Postgres DDL tables & RLS policies
```

### Key Python Libraries
* **`fastapi.BackgroundTasks`**: Used to execute evidence scraping and LLM claim cross-referencing out-of-band.
* **`langchain_google_genai.ChatGoogleGenerativeAI`**: Powers automated structured extraction and synthesis.
* **`supabase.Client`**: Manages relational records and vector embeddings.

---

## 2. Step-by-Step Implementation Guidance

### Step 1: Database Initialization & RLS Security
Run `backend/migrations/verification_evidence_schema.sql` in the Supabase SQL editor.
* **Crucial Tip**: Ensure Row Level Security (RLS) policies check `auth.uid() = expert_id` so experts can never view or modify another expert's submitted evidence.
* **Fallback Pattern**: In `interview.py` (`submit_evidence`), wrap table inserts in a `try/except` block. If the table is missing on local dev instances, generate a mock `MAT-DEMO` ID so frontend flows do not crash.

### Step 2: Implementing the 7-Slot Knowledge Taxonomy (Req 2)
In `domains/interview.py`, the `generate_homework` method must evaluate transcripts against the 7 core knowledge categories defined in the weekly specification:
1. **`concept`**: High-level domain theory or rule.
2. **`breakdown`**: Step-by-step structural explanation.
3. **`action_items`**: Tactical execution steps.
4. **`reference_guides`**: External tools, books, or documentation cited.
5. **`edge_cases`**: Rare failure modes or boundary anomalies.
6. **`constraints`**: Financial, physical, or technical limitations.
7. **`evaluation_path`**: Verification metrics to test success.

**Prompt Specification Strategy**:
Instruct the LLM to return valid JSON mapping each category to extracted markdown snippets. If a category was not discussed, output `null` or an empty string, flagging it as an outstanding gap for the next session.

### Step 3: Asynchronous Evidence Verification Pipeline (Req 1)
Never run blocking network calls inside synchronous FastAPI route handlers.
```python
# Correct Pattern in app.py
@app.post("/homework/submit-evidence")
async def submit_evidence(req: SubmitEvidenceRequest, bg_tasks: BackgroundTasks):
    # 1. Synchronous record creation (Fast, <50ms)
    record = await interview_domain.submit_evidence(...)
    
    # 2. Attach heavy scraping/LLM task to background queue
    bg_tasks.add_task(interview_domain.background_verify_evidence, record["material_id"], ...)
    
    return record # Returns immediately to UI
```

### Step 4: Session Priority Auto-Resume Handshake (Req 3)
When an expert logs in, `LoginPage.tsx` hits `GET /sessions/active`.
* **The Pitfall**: If an expert completed Chapter 1 (`status: 'completed'`) and spawned Chapter 2 (`status: 'paused'`), querying without sorting might return an old session.
* **The Fix**: Always order by chapter iteration number descending:
  ```python
  res = supabase.table("interview_sessions")\
      .select("*").eq("expert_id", current_expert_id)\
      .in_("status", ["active", "paused"])\
      .order("iteration_number", desc=True)\
      .order("created_at", desc=True).limit(1).execute()
  ```

---

## 3. Frontend UI/UX Best Practices

### Dynamic Studio Header (`InterviewPage.tsx`)
Never hardcode expert names or day numbers in JSX markup.
Bind React state directly to Supabase Auth metadata:
```tsx
const expertName = session?.user?.user_metadata?.name || session?.user?.email?.split('@')[0] || "Expert";
```

### Non-Blocking Verification Badges (`HomeworkPage.tsx`)
When submitting open loop evidence:
1. Set card state to `status = 'verifying'`.
2. Display instant positive feedback: `✓ Background Verification Engine triggered. You do not need to wait!`
3. Allow the user to click **"Launch Day 2 Session"** immediately while backend ingestion finishes.
