# Dynamic Session Boundary Engine: Architectural Specification

## Executive Summary
Fixed question counts (e.g., pausing rigidly at turn 12 or 15) fail to account for expert variance. Concise experts may need 25 turns to uncover deep tacit knowledge, whereas verbose experts can fill an LLM's optimal working memory (4,000+ tokens) in just 4 turns. 

The **Dynamic Session Boundary Engine** resolves this by continuously computing real-time **Conversation Saturation**. It guarantees that interview sessions pause based on *meaningful knowledge density* and *context window efficiency*, rather than arbitrary turn counts.

---

## 1. Core Mathematical Model (Composite Saturation Scoring)

On every live turn, the backend (`InterviewDomain.live_turn`) evaluates two live metrics to produce a unified Saturation Score ($0 - 100\%$):

$$\text{Saturation} = (0.60 \times \text{Token Pressure}) + (0.40 \times \text{Objective Completion})$$

### Metric Definitions:
1. **Token Pressure ($\in [0, 1.0]$)**:
   $$\text{Token Pressure} = \min\left(1.0, \frac{\text{Current Transcript Characters}}{16,000}\right)$$
   *Rationale*: 16,000 characters corresponds to ~4,000 tokens. Keeping post-processing input under 4k tokens ensures background synthesis jobs run in under 15 seconds and avoids LLM attention degradation.

2. **Objective Completion Rate ($\in [0, 1.0]$)**:
   $$\text{Objective Completion} = \min\left(1.0, \frac{\text{Satisfied Objectives in Block}}{\text{Total Target Objectives}}\right)$$
   *Rationale*: Measures real knowledge acquisition density rather than superficial conversational turns.

---

## 2. Operating Zones & AI Steering

Based on the real-time Saturation Percentage, the engine directs the AI Journalist into one of three behavioral zones:

```
[0% -------------- 69%] Active Mining Zone (Standard Copilot Extraction)
[70% ------------- 89%] Soft Landing Zone  (Inject Pacing Directive to Steer)
[90% ------------ 100%] Boundary Zone      (Evaluate Grace Period -> Auto-Pause)
```

- **Active Mining Zone ($<70\%$)**: The Copilot executes standard 3-gate follow-up generation and objective compass hunting.
- **Soft Landing Zone ($70\% - 89\%$)**: The Copilot receives a system directive:
  > *"[SESSION PACING NOTICE]: Session saturation is reaching optimal capacity. Begin steering the expert toward wrapping up their current train of thought."*
- **Boundary Zone ($\ge 90\%$ OR Block Satisfied)**: Trigger immediate auto-pause evaluation.

---

## 3. Mid-Thought Protection (Grace Period Protocol)

To ensure an expert is **never** interrupted mid-idea, the Boundary Zone runs an Incomplete Intent Gate before pausing. 

If the expert's latest response contains continuation markers (*"let me finish"*, *"one more thing"*, *"hold on"*, *"almost done"*, *"also"*), the engine intercepts the pause and grants **+1 final grace turn**:
> *"[GRACE PERIOD GRANTED]: The expert asked to finish their thought. Allow 1 final follow-up, then conclude."*

Once the grace thought completes (or if no continuation was requested), the backend emits `action: "system_auto_pause"`.

---

## 4. Asynchronous Flywheel & Seamless Part 2 Re-entry

When `system_auto_pause` fires:
1. **Frontend Overlay**: The UI transitions into a full-screen glassmorphism loader (*"✨ Chapter Fully Synthesized"*).
2. **Background Jobs (`POST /end-session`)**:
   - Synthesizes conversation into structured memory summary.
   - Generates homework verification questions for open loops.
   - Updates master `expert_profile` vector store.
   - **Auto-spawns Iteration $N+1$**: Inserts the next session part into Supabase (`status: 'paused'`), cloning the exact 2D teleprompter coordinates (`blockIdx`, `questionIdx`).
3. **Clean Re-entry**: When the expert clicks **"Continue to Session Part 2"**, the AI Journalist greets them with the synthesized memory summary (*"Welcome back! In Part 1 we established..."*) without re-ingesting raw chat logs.
