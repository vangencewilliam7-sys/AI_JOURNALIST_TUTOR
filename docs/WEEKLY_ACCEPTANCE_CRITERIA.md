# AI Journalist Digital Twin — Acceptance Criteria & Test Scenarios

## Overview
This document specifies the formal Acceptance Criteria (AC) and Behavior-Driven Development (BDD) test scenarios required to validate the **Weekly Requirements Specification** across all Functional Requirements (FRs) and Edge Cases.

---

## Requirement 1: Homework Ledger & Knowledge Verification

### AC-1.1: Automatic Reference Extraction (FR-1)
* **Given** an active interview session in Chapter 1 where the expert states: *"I followed the principles from Andy Grove's High Output Management book"*,
* **When** the session concludes and transitions to `/homework`,
* **Then** the backend extraction engine generates an AI Open Loop entry with `resource_mentioned: "High Output Management by Andy Grove"`.

### AC-1.2: Evidence Classification & Status Tracking (FR-2, FR-3)
* **Given** an AI Open Loop requesting verification materials,
* **When** the expert submits a valid web link (`https://example.com/grove-summary`),
* **Then** the system records the evidence in `submitted_materials` with `verification_status: "verifying"`,
* **And** triggers `background_verify_evidence()` asynchronously.

### AC-1.3: Asynchronous Non-Blocking UI (FR-5, FR-6)
* **Given** an evidence submission request dispatched by the expert,
* **When** the API returns `200 OK`,
* **Then** the UI displays `⏳ Ingesting in Background...` without freezing browser interaction,
* **And** allows immediate navigation to Chapter Part 2.

---

## Requirement 2: Structured Knowledge Extraction (7-Slot Taxonomy)

### AC-2.1: Complete Category Mapping (FR-1 to FR-8)
* **Given** a raw interview transcript covering technical architecture,
* **When** `generate_homework` executes during session closure,
* **Then** the output JSON successfully maps text into all 7 structured educational categories:
  1. `concept`
  2. `breakdown`
  3. `action_items`
  4. `reference_guides`
  5. `edge_cases`
  6. `constraints`
  7. `evaluation_path`

### AC-2.2: Handling Multiple & Nested Concepts (Edge Case)
* **Given** an expert answer containing two distinct architectural concepts in a single paragraph,
* **When** structured extraction executes,
* **Then** both concepts are separated into distinct bulleted objects inside the `concept` and `breakdown` arrays.

---

## Requirement 3: Session Management & Handoff Continuity

### AC-3.1: Complete State Snapshot Rehydration (FR-1 to FR-4)
* **Given** an active interview session at Question 4 of Block 2 with 2 recorded tangents,
* **When** the expert clicks **Pause Session** or refreshes the browser window,
* **Then** the backend updates `interview_sessions` storing the exact 2D pointer coordinates in `snapshot`,
* **And** upon reloading `/interview`, the teleprompter restores Question 4 of Block 2 without losing chat history.

### AC-3.2: Seamless Chapter Chaining Flywheel (FR-8)
* **Given** an expert who has completed Chapter 1 (`iteration_number = 1`),
* **When** the chapter closes,
* **Then** Chapter 1 is stamped with `status: "completed"`,
* **And** Chapter 2 (`iteration_number = 2`) is automatically spawned with `status: "paused"`, inheriting the parent chapter's `script` blueprint.

### AC-3.3: Login Priority Resolution (FR-8, FR-9)
* **Given** an expert re-authenticating on the login screen after Chapter 1 is finished,
* **When** `GET /sessions/active` is invoked,
* **Then** the query sorts by `iteration_number DESC`, returning Chapter 2,
* **And** drops the user directly into Session Iteration 2 bypassing first-session onboarding.

---

## Definition of Done (DoD) Checklist
- [x] All database DDL migrations executed and RLS policies enforced.
- [x] Python backend syntax verified clean (`python -m py_compile`).
- [x] TypeScript build verification passed (`tsc --noEmit`).
- [x] Executive brief and walkthrough documentation finalized.
