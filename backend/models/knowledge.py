from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class KnowledgeItem(BaseModel):
    knowledge_type: str
    topic: Optional[str] = None
    title: Optional[str] = None
    raw_quote: Optional[str] = None
    clean_insight: Optional[str] = None
    
    # Tacit Framework Fields
    signal: Optional[str] = None
    interpretation: Optional[str] = None
    expert_action: Optional[str] = None
    decision_rule: Optional[str] = None
    workflow_step: Optional[Dict[str, Any]] = None
    source_or_origin: Optional[str] = None
    
    # Metadata
    confidence: Optional[str] = None
    validation_status: str = "unvalidated"
    missing_fields: List[str] = Field(default_factory=list)
