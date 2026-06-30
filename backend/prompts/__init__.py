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
#   flywheel_bridge.py             │  FLYWHEEL_BRIDGE_PROMPT
#   course_discovery_engine.py     │  COURSE_DISCOVERY_ENGINE_PROMPT
#                                  │  COURSE_IDENTITY_SYNTHESIZER_PROMPT
#                                  │  COURSE_IDENTITY_FIELD_DETECTOR_PROMPT
#   module_discovery_engine.py     │  MODULE_DISCOVERY_ENGINE_PROMPT
#                                  │  MODULE_LIST_EXTRACTOR_PROMPT
#                                  │  MODULE_SATURATION_CHECK_PROMPT
#   module_enrichment_engine.py    │  MODULE_ENRICHMENT_ENGINE_PROMPT
#                                  │  MODULE_ENRICHMENT_FIELD_DETECTOR_PROMPT
#                                  │  MODULE_ENRICHMENT_SYNTHESIZER_PROMPT
#   topic_discovery_engine.py      │  TOPIC_DISCOVERY_ENGINE_PROMPT
#                                  │  TOPIC_LIST_EXTRACTOR_PROMPT
#                                  │  TOPIC_COVERAGE_VALIDATOR_PROMPT
#   curriculum_validation_engine.py│  CURRICULUM_VALIDATION_PROMPT
#   coverage_controller.py         │  COVERAGE_CONTROLLER_PROMPT
#   coverage_controller_phase2.py  │  MODULE_COVERAGE_CONTROLLER_PROMPT
#   curriculum_classification_engine.py │ CURRICULUM_CLASSIFICATION_PROMPT
#   coverage_controller_phase3.py  │  MODULE_ENRICHMENT_COVERAGE_CONTROLLER_PROMPT
#   coverage_controller_phase4.py  │  TOPIC_COVERAGE_CONTROLLER_PROMPT
#   topic_initialization_engine.py │  TOPIC_INITIALIZATION_PROMPT
#   expert_understanding_engine.py │  EXPERT_UNDERSTANDING_PROMPT
#   knowledge_coverage_engine.py   │  KNOWLEDGE_COVERAGE_PROMPT
#   tacit_knowledge_extraction_engine.py │ TACIT_KNOWLEDGE_EXTRACTION_PROMPT
#   knowledge_gap_manager.py       │  KNOWLEDGE_GAP_MANAGER_PROMPT
#   topic_transition_engine.py     │  TOPIC_TRANSITION_PROMPT
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

# 9. Phase 1 — Course Discovery Engine
from .course_discovery_engine import (
    COURSE_DISCOVERY_ENGINE_PROMPT,
    COURSE_IDENTITY_SYNTHESIZER_PROMPT,
    COURSE_IDENTITY_FIELD_DETECTOR_PROMPT
)

# 10. Phase 2 — Module Discovery Engine
from .module_discovery_engine import (
    MODULE_DISCOVERY_ENGINE_PROMPT,
    MODULE_LIST_EXTRACTOR_PROMPT,
    MODULE_SATURATION_CHECK_PROMPT
)

# 11. Phase 3 — Module Enrichment Engine
from .module_enrichment_engine import (
    MODULE_ENRICHMENT_ENGINE_PROMPT,
    MODULE_ENRICHMENT_FIELD_DETECTOR_PROMPT,
    MODULE_ENRICHMENT_SYNTHESIZER_PROMPT
)

# 12. Phase 4 — Topic Discovery Engine
from .topic_discovery_engine import (
    TOPIC_DISCOVERY_ENGINE_PROMPT,
    TOPIC_LIST_EXTRACTOR_PROMPT,
    TOPIC_COVERAGE_VALIDATOR_PROMPT
)

# 13. Phase 5 — Curriculum Validation & Lock Engine
from .curriculum_validation_engine import CURRICULUM_VALIDATION_PROMPT

# 13b. Coverage Controller Prompt
from .coverage_controller import COVERAGE_CONTROLLER_PROMPT
from .coverage_controller_phase2 import MODULE_COVERAGE_CONTROLLER_PROMPT
from .curriculum_classification_engine import CURRICULUM_CLASSIFICATION_PROMPT
from .coverage_controller_phase3 import MODULE_ENRICHMENT_COVERAGE_CONTROLLER_PROMPT
from .coverage_controller_phase4 import TOPIC_COVERAGE_CONTROLLER_PROMPT

# 14. Phase 6 — Topic Initialization Engine
from .topic_initialization_engine import TOPIC_INITIALIZATION_PROMPT

# 15. Phase 7 — Expert Understanding Engine
from .expert_understanding_engine import EXPERT_UNDERSTANDING_PROMPT

# 16. Phase 8 — Knowledge Coverage Engine
from .knowledge_coverage_engine import KNOWLEDGE_COVERAGE_PROMPT

# 17. Phase 9 — Tacit Knowledge Extraction Engine
from .tacit_knowledge_extraction_engine import TACIT_KNOWLEDGE_EXTRACTION_PROMPT

# 18. Phase 10 — Knowledge Gap Manager
from .knowledge_gap_manager import KNOWLEDGE_GAP_MANAGER_PROMPT

# 19. Phase 11 — Topic Completion & Transition Engine
from .topic_transition_engine import TOPIC_TRANSITION_PROMPT
from .archetype_classifier import ARCHETYPE_CLASSIFIER_PROMPT
from .background_manager import (
    BACKGROUND_EMBED_FILTER_PROMPT, 
    RETRIEVAL_GATE_PROMPT, 
    SCRATCHPAD_UPDATE_PROMPT,
    OBJECTIVE_SATISFACTION_PROMPT,
    OBJECTIVE_REQUIREMENTS,
    COVERAGE_ENGINE_PROMPT,
    TOPIC_CONTROLLER_PROMPT
)

# 6. Real-Time Engines (Phases 1.5, 2-5)
from .knowledge_engines import (
    DRIFT_DETECTOR_PROMPT,
    INSIGHT_DETECTION_PROMPT,
    INSIGHT_PRIORITIZATION_PROMPT,
    KNOWLEDGE_GRAPH_UPDATE_PROMPT,
    COVERAGE_AND_GAP_PROMPT,
    CURRICULUM_EXTRACTOR_PROMPT
)

# 7. Orchestrator (Phases 6-7)
from .orchestrator import (
    MASTER_INTERVIEW_ORCHESTRATOR_PROMPT,
    ADAPTIVE_CURIOSITY_PROMPT
)

# 8. Post-Session Synthesis (Phase 4)
from .insights_synthesis import INSIGHTS_SYNTHESIS_PROMPT

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
    'ARCHETYPE_CLASSIFIER_PROMPT',
    'BACKGROUND_EMBED_FILTER_PROMPT',
    'RETRIEVAL_GATE_PROMPT',
    'SCRATCHPAD_UPDATE_PROMPT',
    'OBJECTIVE_SATISFACTION_PROMPT',
    'OBJECTIVE_REQUIREMENTS',
    'COVERAGE_ENGINE_PROMPT',
    'TOPIC_CONTROLLER_PROMPT',
    'DRIFT_DETECTOR_PROMPT',
    'INSIGHT_DETECTION_PROMPT',
    'INSIGHT_PRIORITIZATION_PROMPT',
    'KNOWLEDGE_GRAPH_UPDATE_PROMPT',
    'COVERAGE_AND_GAP_PROMPT',
    'CURRICULUM_EXTRACTOR_PROMPT',
    'MASTER_INTERVIEW_ORCHESTRATOR_PROMPT',
    'ADAPTIVE_CURIOSITY_PROMPT',
    'INSIGHTS_SYNTHESIS_PROMPT',
    'COURSE_DISCOVERY_ENGINE_PROMPT',
    'COURSE_IDENTITY_SYNTHESIZER_PROMPT',
    'COURSE_IDENTITY_FIELD_DETECTOR_PROMPT',
    'MODULE_DISCOVERY_ENGINE_PROMPT',
    'MODULE_LIST_EXTRACTOR_PROMPT',
    'MODULE_SATURATION_CHECK_PROMPT',
    'MODULE_ENRICHMENT_ENGINE_PROMPT',
    'MODULE_ENRICHMENT_FIELD_DETECTOR_PROMPT',
    'MODULE_ENRICHMENT_SYNTHESIZER_PROMPT',
    'TOPIC_DISCOVERY_ENGINE_PROMPT',
    'TOPIC_LIST_EXTRACTOR_PROMPT',
    'TOPIC_COVERAGE_VALIDATOR_PROMPT',
    'CURRICULUM_VALIDATION_PROMPT',
    'COVERAGE_CONTROLLER_PROMPT',
    'MODULE_COVERAGE_CONTROLLER_PROMPT',
    'CURRICULUM_CLASSIFICATION_PROMPT',
    'MODULE_ENRICHMENT_COVERAGE_CONTROLLER_PROMPT',
    'TOPIC_COVERAGE_CONTROLLER_PROMPT',
    'TOPIC_INITIALIZATION_PROMPT',
    'EXPERT_UNDERSTANDING_PROMPT',
    'KNOWLEDGE_COVERAGE_PROMPT',
    'TACIT_KNOWLEDGE_EXTRACTION_PROMPT',
    'KNOWLEDGE_GAP_MANAGER_PROMPT',
    'TOPIC_TRANSITION_PROMPT'
]