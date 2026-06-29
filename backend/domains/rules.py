# ==========================================================================
# Deterministic Exit Rules & Targets
# ==========================================================================

RULES = {
    "Block 1: Personal Origin & Persona": {
        "required": [
            "Origin Story",
            "Turning Point",
            "Core Motivation",
            "Identity Formation",
            "Core Beliefs"
        ],
        "exit_requirements": [
            "Origin Story",
            "Turning Point",
            "Core Motivation"
        ],
        "minimum_completion": 4
    },
    "Block 2: Learning Journey & Mentorship": {
        "required": [
            "Learning Process",
            "Skill Acquisition",
            "Mistakes",
            "Breakthroughs",
            "Learning Heuristics"
        ],
        "exit_requirements": [
            "Learning Process",
            "Skill Acquisition",
            "Learning Heuristics"
        ],
        "minimum_completion": 4
    },
    "Block 3: Defining the Core Curriculum": {
        "required": [
            "Modules",
            "Topics",
            "Dependencies",
            "Sequence",
            "Priority Topics"
        ],
        "exit_requirements": [
            "Modules",
            "Topics",
            "Dependencies"
        ],
        "minimum_completion": 5
    },
    "Block 4: Deep Extraction": {
        "required": [
            "Mental Models",
            "Heuristics",
            "Decision Rules",
            "Failure Patterns",
            "Tradeoffs",
            "Misconceptions",
            "Evaluation Signals",
            "Constraints"
        ],
        "exit_requirements": [
            "Mental Models",
            "Heuristics",
            "Decision Rules",
            "Failure Patterns"
        ],
        "minimum_completion": 6
    }
}

TANGENT_BUDGET_RULES = {
    "base_budget": 2,
    "high_value_threshold": 0.85,
    "max_high_value_followups": 2,
    "extra_for_high_value": 1
}

DRIFT_RULES = {
    "drift_threshold": 0.3
}

def get_block_rules(block_name: str):
    # Match by prefix or exact string
    for key, rule in RULES.items():
        if key in block_name or block_name in key:
            return rule
    # Default fallback
    return RULES["Block 4: Deep Extraction"]
