"""
Pydantic request/response models for all API endpoints.
"""

from typing import Optional
from pydantic import BaseModel


class InterviewRequest(BaseModel):
    expert_answer: str
    user_session_id: str
    topic: Optional[str] = None
    input_source: Optional[str] = "text"


class PrepareRequest(BaseModel):
    user_session_id: str
    topic: Optional[str] = None
    tutor_name: Optional[str] = ""
    tutor_role: Optional[str] = ""
    tutor_experience: Optional[str] = ""
    course_title: Optional[str] = ""
    target_audience: Optional[str] = ""
    prerequisites: Optional[str] = ""
    completion_time: Optional[str] = ""
    north_star_outcome: Optional[str] = ""


class YoutubeIngestRequest(BaseModel):
    url: str
