import re
import sys

target = r'c:\Users\Kusuma\OneDrive\Desktop\AI JOURNALIST\AI_JOURNALIST_TUTOR\backend\prompts\knowledge_engines.py'
with open(target, 'r', encoding='utf-8') as f:
    content = f.read()

# Add DRIFT_DETECTOR_PROMPT at the top
drift_prompt = '''\
DRIFT_DETECTOR_PROMPT = """\\
PHASE 1.5
DRIFT DETECTOR ENGINE

ROLE
You are a conversational alignment monitor.
Your only job is to evaluate if the expert's response is aligned with the current interview topic, or if they have completely drifted into an unrelated subject.

INPUT
Current Topic: {current_topic}
Current Question: {current_question}
Expert Answer: {expert_answer}

OBJECTIVE
Determine the alignment score (0.0 to 1.0) between the expert's answer and the current topic/question.

OUTPUT FORMAT
Return a STRICT JSON object:
{{
  "alignment_score": 0.0,
  "detected_topic": "string"
}}
"""

'''

if "DRIFT_DETECTOR_PROMPT" not in content:
    content = content.replace("INSIGHT_DETECTION_PROMPT = ", drift_prompt + "INSIGHT_DETECTION_PROMPT = ")


# Replace COVERAGE_AND_GAP_PROMPT
cov_start = content.find("COVERAGE_AND_GAP_PROMPT =")
if cov_start != -1:
    content = content[:cov_start] + '''\
COVERAGE_AND_GAP_PROMPT = """\\
PHASE 5
COVERAGE & GAP ENGINE

ROLE
You are a Knowledge Coverage Evaluator.
Your job is to determine what required knowledge has been successfully extracted from the expert so far.

INPUT
Current Block: {current_block}
Current Topic: {current_topic}
Required Targets Schema: {required_targets}
Knowledge Nodes: {knowledge_nodes}
Conversation History: {conversation_history}

OBJECTIVE
Evaluate the Conversation History and Knowledge Nodes against the exact Required Targets Schema provided.

OUTPUT
Return a STRICT JSON object where the keys exactly match the array of Required Targets Schema. For each key, output true if substantive evidence exists in the conversation history or knowledge nodes. Otherwise, output false.

Example if Required Targets is ["Origin Story", "Turning Point"]:
{{
  "Origin Story": true,
  "Turning Point": false
}}
"""
'''
    
with open(target, 'w', encoding='utf-8') as f:
    f.write(content)

print("knowledge_engines.py patched successfully.")
