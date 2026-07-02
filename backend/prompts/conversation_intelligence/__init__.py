# ==========================================================================
# Conversation Intelligence Layer
# ==========================================================================
# Sits ABOVE every interview phase as a wrapping layer.
# Does NOT touch curriculum extraction logic.
# Controls HOW the conversation evolves, not WHAT is extracted.
#
# FILE MAP:
# ─────────────────────────────────────────────────────────────────────────
#   director.py           │  CONVERSATION_DIRECTOR_PROMPT
#   strategy_engine.py    │  STRATEGY_ENGINE_PROMPT
#   repetition_detector.py│  REPETITION_DETECTOR_PROMPT
#   bridge_engine.py      │  BRIDGE_ENGINE_PROMPT
#   reflection_engine.py  │  REFLECTION_ENGINE_PROMPT
# ─────────────────────────────────────────────────────────────────────────
#
# APPLIES TO:
#   Phase 3  — Module Enrichment (module_enrichment_turn)
#   Phase 4  — Topic Discovery (topic_discovery_turn)
#   Phase 6  — Topic Knowledge Exploration (topic_exploration_turn)
# ─────────────────────────────────────────────────────────────────────────

from .director import CONVERSATION_DIRECTOR_PROMPT
from .strategy_engine import STRATEGY_ENGINE_PROMPT
from .repetition_detector import REPETITION_DETECTOR_PROMPT
from .bridge_engine import BRIDGE_ENGINE_PROMPT
from .reflection_engine import REFLECTION_ENGINE_PROMPT
from .conversation_memory import CONVERSATION_MEMORY_PROMPT
from .podcast_personality import PODCAST_PERSONALITY_PROMPT
from .interview_producer import INTERVIEW_PRODUCER_PROMPT
from .lesson_initializer import LESSON_INITIALIZER_PROMPT
from .coverage_controller import LESSON_COVERAGE_CONTROLLER_PROMPT
from .tacit_detector import TACIT_OPPORTUNITY_DETECTOR_PROMPT
from .knowledge_extractor import KNOWLEDGE_EXTRACTION_ENGINE_PROMPT

__all__ = [
    'CONVERSATION_DIRECTOR_PROMPT',
    'STRATEGY_ENGINE_PROMPT',
    'REPETITION_DETECTOR_PROMPT',
    'BRIDGE_ENGINE_PROMPT',
    'REFLECTION_ENGINE_PROMPT',
    'CONVERSATION_MEMORY_PROMPT',
    'PODCAST_PERSONALITY_PROMPT',
    'INTERVIEW_PRODUCER_PROMPT',
    'LESSON_INITIALIZER_PROMPT',
    'LESSON_COVERAGE_CONTROLLER_PROMPT',
    'TACIT_OPPORTUNITY_DETECTOR_PROMPT',
    'KNOWLEDGE_EXTRACTION_ENGINE_PROMPT',
]
