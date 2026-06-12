# ==========================================================================
# Live Follow-Up Prompts — Used during the live interview loop
# Converted from: src/prompts/liveFollowUp.js (Node.js brainstorm)
# ==========================================================================
# These prompts control the live conversational loop when the human clicks
# "Stop & Process" on the UI.
#
# INTENT_CLASSIFIER_PROMPT  — classifies expert response as substantive/skip
# LIVE_FOLLOWUP_PROMPT      — generates the next conversational question
# ==========================================================================

INTENT_CLASSIFIER_PROMPT = """\
You are analyzing a single response from an expert during a live interview.

CURRENT QUESTION ASKED: {current_question}
EXPERT'S RESPONSE: {expert_answer}

Classify the expert's INTENT. Choose exactly one:
- "substantive": The expert is genuinely answering the question with real content (even if brief or incomplete) or starting a story.
- "skip": The expert wants to move on. They are signaling disinterest, refusal, discomfort, or that they have nothing more to add.

Return ONLY a JSON object:
{{"intent": "substantive" | "skip"}}
"""

LIVE_FOLLOWUP_PROMPT = """\
You are executing a live, conversational interview loop. Your goal is to bypass their rational brain and tap into their subconscious memory.

EXPERT'S LAST SPOKEN ANSWER:
"{transcribed_chunk}"

TASK: Generate the EXACT next question a human interviewer should ask.
1. Anchor your question in EMOTION and EXPERIENCE.
2. If they mentioned a specific tool, client, or problem, pull exactly on that thread.
3. Make it highly conversational and brief. Must be ready to be spoken aloud.

Output STRICTLY in the following JSON format:
{{
  "internal_reasoning": "A 1-sentence explanation of why you chose this follow-up.",
  "display_question": "The exact conversational question the host should say out loud next."
}}
"""
