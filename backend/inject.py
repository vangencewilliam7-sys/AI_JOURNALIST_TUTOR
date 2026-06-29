import os
import re

interview_file = r"c:\Users\Kusuma\OneDrive\Desktop\AI JOURNALIST\AI_JOURNALIST_TUTOR\backend\domains\interview.py"
scratch_file = r"c:\Users\Kusuma\OneDrive\Desktop\AI JOURNALIST\AI_JOURNALIST_TUTOR\backend\scratch_live_turn.py"

with open(interview_file, 'r', encoding='utf-8') as f:
    content = f.read()

with open(scratch_file, 'r', encoding='utf-8') as f:
    scratch_content = f.read()

# Find async def live_turn
start_idx = content.find("    async def live_turn(")
if start_idx == -1:
    print("Could not find live_turn")
    exit(1)

# Find next method start (def _build_conversation_history)
end_idx = content.find("    def _build_conversation_history(", start_idx)
if end_idx == -1:
    print("Could not find end of live_turn")
    exit(1)

new_content = content[:start_idx] + scratch_content + "\n" + content[end_idx:]

with open(interview_file, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Injected live_turn successfully.")
