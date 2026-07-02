import json

def build_prompt(variables: dict) -> str:
    question = variables.get("question", "")
    answer = variables.get("answer", "")
    
    knowledge_types = [
        "background_context", "belief_evolution", "core_work",
        "workflow_knowledge", "tool_checklist_knowledge", "knowledge_source",
        "tacit_signal", "decision_principle", "beginner_mistake",
        "experience_memory", "persona_style", "validation_feedback",
        "homework_gap"
    ]

    return f"""You are a Knowledge Extraction Engine for an AI Journalist system.

Extract structured Expert Intelligence from the following expert answer.

AI Question: {question}
Expert Answer: {answer}

RULES:
1. Every knowledge item MUST have a raw_quote — an exact or near-exact quote from the expert's answer.
2. If there is no supporting quote, DO NOT create the knowledge item.
3. Separate what the expert actually said (raw_quote) from your inference (clean_insight).
4. Set validation_status to "unvalidated" for all items.
5. Include missing_fields for each item when signal/action/example/exception is missing.
6. Do not invent knowledge the expert did not express.
7. For every item, you MUST output the following three classification fields:
   - "knowledge_type": Choose exactly ONE from the list below (e.g., "decision_principle", "experience_memory").
   - "topic": The broad subject matter being discussed (e.g., "Infrastructure Design", "Team Management"). Do NOT put the knowledge_type here.
   - "title": A specific, catchy headline for this particular insight (e.g., "Proactive Infrastructure Design").
Knowledge types to use: {json.dumps(knowledge_types)}

For tacit_signal items, also fill: signal, interpretation, expert_action
For decision_principle items, also fill: decision_rule, expert_action
For workflow_knowledge items, also fill: workflow_step (as an object with step_name and details)

Return your response strictly as a JSON array of objects. Do not include markdown formatting like ```json.
"""
