# ==========================================================================
# Prompt Package — Master Export / Routing
# ==========================================================================
#
# FILE MAP (from prompt_change.md brainstorm):
# ─────────────────────────────────────────────────────────────────────────
#   Python File                   │  What It Contains
# ─────────────────────────────────────────────────────────────────────────
#   system_persona.py             │  ARCHETYPE_RULES + get_base_persona()
#   live_follow_up.py             │  INTENT_CLASSIFIER_PROMPT + LIVE_FOLLOWUP_PROMPT
#   post_session_synthesis.py     │  GENERAL_SYNTHESIS + TUTOR_SYNTHESIS + HOMEWORK_GENERATOR
#   flywheel_bridge.py            │  FLYWHEEL_BRIDGE_PROMPT
# ─────────────────────────────────────────────────────────────────────────
#
# PROMPT ROUTING BY PHASE:
# ─────────────────────────────────────────────────────────────────────────
#   Phase 2 (Intake)            →  system_persona.get_base_persona()
#   Phase 3 (Live Interview)    →  live_follow_up.INTENT_CLASSIFIER_PROMPT
#                                  live_follow_up.LIVE_FOLLOWUP_PROMPT
#   Phase 4 (Post-Session)      →  post_session_synthesis.GENERAL_SYNTHESIS_PROMPT
#                                  post_session_synthesis.TUTOR_SYNTHESIS_PROMPT
#   Phase 5 (Homework)          →  post_session_synthesis.HOMEWORK_GENERATOR_PROMPT
#   Phase 6 (Day 2+ Bridge)     →  flywheel_bridge.FLYWHEEL_BRIDGE_PROMPT
# ─────────────────────────────────────────────────────────────────────────

# 1. System Persona (identity + archetype switching)
from .system_persona import ARCHETYPE_RULES, get_base_persona

# 2. Day One Opener (emotional icebreaker for Day 1)
from .day_one_opener import DAY_ONE_OPENER_PROMPT

# 3. Script Generator (for every iteration)
from .script_generator import ITERATION_SCRIPT_PROMPT

# 4. Live Follow-Up (pause/unpause engine during interview)
from .live_follow_up import INTENT_CLASSIFIER_PROMPT, LIVE_FOLLOWUP_PROMPT

# 5. Post-Session Synthesis (async extraction after "End Session")
from .post_session_synthesis import (
    GENERAL_SYNTHESIS_PROMPT,
    TUTOR_SYNTHESIS_PROMPT,
    HOMEWORK_GENERATOR_PROMPT,
)

# 6. Flywheel Bridge (Day 2+ session reactivation)
from .flywheel_bridge import FLYWHEEL_BRIDGE_PROMPT

__all__ = [
    "ARCHETYPE_RULES",
    "get_base_persona",
    "DAY_ONE_OPENER_PROMPT",
    "ITERATION_SCRIPT_PROMPT",
    "INTENT_CLASSIFIER_PROMPT",
    "LIVE_FOLLOWUP_PROMPT",
    "GENERAL_SYNTHESIS_PROMPT",
    "TUTOR_SYNTHESIS_PROMPT",
    "HOMEWORK_GENERATOR_PROMPT",
    "FLYWHEEL_BRIDGE_PROMPT",
]