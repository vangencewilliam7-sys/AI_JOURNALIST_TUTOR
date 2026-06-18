# ==========================================================================
# Prompt Package — Master Export / Routing
# ==========================================================================
#
# FILE MAP:
# ─────────────────────────────────────────────────────────────────────────
#   Python File                   │  What It Contains
# ─────────────────────────────────────────────────────────────────────────
#   system_persona.py             │  ARCHETYPE_RULES + get_base_persona() + get_archetype_rules()
#   day_one_opener.py             │  DAY_ONE_OPENER_PROMPT
#   script_generator.py           │  ITERATION_SCRIPT_PROMPT (5-phase)
#   live_follow_up.py             │  LIVE_COPILOT_PROMPT (single-pass: intent + follow-up)
#   post_session_synthesis.py     │  GENERAL_SYNTHESIS + TUTOR_SYNTHESIS + HOMEWORK_GENERATOR
#   flywheel_bridge.py            │  FLYWHEEL_BRIDGE_PROMPT
# ─────────────────────────────────────────────────────────────────────────
#
# PROMPT ROUTING BY PHASE:
# ─────────────────────────────────────────────────────────────────────────
#   Phase 1 (Intake)            →  day_one_opener.DAY_ONE_OPENER_PROMPT
#   Phase 2 (Script)            →  script_generator.ITERATION_SCRIPT_PROMPT
#                                  system_persona.get_base_persona()
#   Phase 3 (Live Interview)    →  live_follow_up.LIVE_COPILOT_PROMPT
#   Phase 4 (Post-Session)      →  post_session_synthesis.GENERAL_SYNTHESIS_PROMPT
#                                  post_session_synthesis.TUTOR_SYNTHESIS_PROMPT
#   Phase 5 (Homework)          →  post_session_synthesis.HOMEWORK_GENERATOR_PROMPT
#   Phase 6 (Day 2+ Bridge)     →  flywheel_bridge.FLYWHEEL_BRIDGE_PROMPT
# ─────────────────────────────────────────────────────────────────────────

# 1. System Persona (identity + archetype switching)
from .system_persona import ARCHETYPE_RULES, get_base_persona, get_archetype_rules

# 2. Day One Opener (emotional icebreaker for Day 1)
from .day_one_opener import DAY_ONE_OPENER_PROMPT

# 3. Script Generator (5-phase interview blueprint)
from .script_generator import ITERATION_SCRIPT_PROMPT

# 4. Live Copilot (single-pass intent + follow-up during interview)
from .live_follow_up import LIVE_COPILOT_PROMPT

# 5. Post-Session Synthesis (async extraction after "End Session")
from .post_session_synthesis import GENERAL_SYNTHESIS_PROMPT, TUTOR_SYNTHESIS_PROMPT, HOMEWORK_GENERATOR_PROMPT, RESOURCE_VALIDATION_PROMPT
from .flywheel_bridge import FLYWHEEL_BRIDGE_PROMPT
from .archetype_classifier import ARCHETYPE_CLASSIFIER_PROMPT

__all__ = [
    'ARCHETYPE_RULES',
    'get_base_persona',
    'get_archetype_rules',
    'DAY_ONE_OPENER_PROMPT',
    'ITERATION_SCRIPT_PROMPT',
    'LIVE_COPILOT_PROMPT',
    'GENERAL_SYNTHESIS_PROMPT',
    'TUTOR_SYNTHESIS_PROMPT',
    'HOMEWORK_GENERATOR_PROMPT',
    'RESOURCE_VALIDATION_PROMPT',
    'FLYWHEEL_BRIDGE_PROMPT',
    'ARCHETYPE_CLASSIFIER_PROMPT'
]