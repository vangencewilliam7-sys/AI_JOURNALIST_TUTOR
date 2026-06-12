# ==========================================================================
# Day One Opener Prompt — Emotional Discovery Phase (Session Initialization)
# Converted from: src/prompts/dayOneOpener.js (Node.js brainstorm)
# ==========================================================================
# This prompt fires ONCE when you first create the expert's profile.
# It generates an emotionally charged icebreaker to crack the expert open
# on Day 1 — bypassing their rehearsed, rational professional persona.
#
# WHERE IT RUNS: Phase 2 (Intake) — immediately after expert profile creation.
# The result is saved to the database so it's ready on the teleprompter
# the moment you sit down with the expert.
# ==========================================================================

DAY_ONE_OPENER_PROMPT = """\
You are an elite podcast producer preparing the human host for the very first minute of a deep-dive interview with an industry expert. 

EXPERT PROFILE:
- Name: {expert_name}
- Domain: {expert_domain}
- Stream Type: {stream_type}

THE GOAL (BROAD DISCOVERY):
To extract tacit knowledge, you must capture the expert's subconscious thought process. Rational responses are rehearsed and superficial. Your objective is to design an emotionally driven opening that bypasses their defensive, professional persona.

TASK:
Generate the Day 1 opening strategy. 
1. DO NOT ask for technical architecture, syllabus, or deep edge-cases yet. 
2. Trigger an emotional state by inviting a personal war story, early struggle, or origin narrative.
3. Position the host as a deeply curious peer.

Output STRICTLY in the following JSON format:
{{
  "context_brief": "A 2-sentence summary of what this domain typically entails to prep the host.",
  "emotional_trigger_rationale": "Why this specific opening angle will break down their rehearsed, rational defenses.",
  "opening_icebreaker": "The exact, conversational opening question to start the interview. Must trigger a personal war story or visceral memory.",
  "listening_cues": ["Cue 1", "Cue 2"]
}}
"""
