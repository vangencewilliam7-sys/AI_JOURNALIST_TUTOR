# ==========================================================================
# Flywheel Bridge Prompt — Day 2+ Session Reactivation
# Converted from: src/prompts/flywheelBridge.js (Node.js brainstorm)
# ==========================================================================
# This prompt spins the flywheel at the start of Day 2, Day 3, etc.
# It generates a "Trust-Signal Opener" that proves the system remembered
# yesterday's conversation by referencing the Homework Ledger.
# ==========================================================================

FLYWHEEL_BRIDGE_PROMPT = """\
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
{{
  "internal_reasoning": "Why this specific bridge establishes immediate executive competence.",
  "bridge_opener": "The exact conversational script the human host will say out loud to open the interview."
}}
"""
