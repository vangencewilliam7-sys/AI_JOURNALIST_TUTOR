# Move this to the very top!
import os
env_path = os.path.join(os.path.dirname(__file__), '.env')
from dotenv import load_dotenv
load_dotenv(dotenv_path=env_path, override=True)

import re
import json
import logging
import httpx
import base64
import tempfile
import shutil
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from supabase import create_client, Client
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from youtube_transcript_api import YouTubeTranscriptApi

from domains.interview import InterviewDomain
from dependencies import get_current_expert_id

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Loading .env from: {os.path.abspath(env_path)}")

# --- MONKEY PATCH FOR SSL INTERCEPTION ---
# Disables SSL verification globally for httpx to bypass local Antivirus/VPN issues
_original_async_init = httpx.AsyncClient.__init__
def _new_async_init(self, *args, **kwargs):
    kwargs['verify'] = False
    kwargs['timeout'] = httpx.Timeout(60.0)
    _original_async_init(self, *args, **kwargs)
httpx.AsyncClient.__init__ = _new_async_init

_original_sync_init = httpx.Client.__init__
def _new_sync_init(self, *args, **kwargs):
    kwargs['verify'] = False
    kwargs['timeout'] = httpx.Timeout(60.0)
    _original_sync_init(self, *args, **kwargs)
httpx.Client.__init__ = _new_sync_init
# -----------------------------------------

# Database Setup
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

# Fallback in case Windows os.environ fails to update
if not SUPABASE_URL:
    from dotenv import dotenv_values
    config = dotenv_values(env_path)
    SUPABASE_URL = config.get("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY = config.get("SUPABASE_SERVICE_ROLE_KEY") or config.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL:
    raise ValueError(f"CRITICAL: Could not find SUPABASE_URL in {env_path}")


# WARNING: If RLS is enabled, you MUST use the SERVICE_ROLE_KEY here for the backend to bypass RLS,
# or pass the user token to the client on a per-request basis. We use service_role here.
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = FastAPI(title="AI Journalist Platform - Backend (6-Phase Framework)")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI components
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, timeout=300)
llm_fast = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, max_tokens=1500, timeout=60)
embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")

# Domain Registry (Unified)
interview_domain = InterviewDomain(llm, supabase, llm_fast, embeddings_model)

# ============================================================
# MODELS
# ============================================================

class ExpertIntakeRequest(BaseModel):
    name: Optional[str] = None
    domain: str
    stream_type: str  # 'general' or 'tutor'
    # Tutor specific
    course_title: Optional[str] = None
    course_description: Optional[str] = None
    target_audience: Optional[str] = None
    expertise_streams: Optional[List[str]] = []
    years_of_experience: Optional[int] = 0
    short_bio: Optional[str] = None
    linkedin_url: Optional[str] = None

class LiveTurnRequest(BaseModel):
    session_id: str
    expert_answer: str
    current_script_question: Optional[str] = ""
    active_block: Optional[str] = "Block 1: Personal Origin & Persona"
    tangent_count: Optional[int] = 0

class HomeworkPutRequest(BaseModel):
    human_manual_notes: str

class PauseSessionRequest(BaseModel):
    current_script_question: str
    active_block: str
    tangent_count: int

class SubmitEvidenceRequest(BaseModel):
    session_id: str
    iteration_number: int
    loop_topic: str
    material_type: str
    content_or_url: str
    resource_mentioned: Optional[str] = ""
    what_expert_claimed: Optional[str] = ""

class InsightVerifyItem(BaseModel):
    id: str
    status: str  # 'approved', 'modified', 'rejected'
    title: Optional[str] = None
    content: Optional[str] = None
    expert_quote: Optional[str] = None

class VerifyInsightsRequest(BaseModel):
    insights: List[InsightVerifyItem]

# ============================================================
# PHASE 2: INTAKE & SCRIPT GENERATION
# ============================================================

@app.post("/intake")
async def intake_endpoint(request: ExpertIntakeRequest, current_expert_id: str = Depends(get_current_expert_id)):
    """Phase 2: Save expert profile and generate Day 1 Icebreaker."""
    try:
        # Fetch existing expert row or auth metadata to preserve name if not provided in request
        existing_expert = supabase.table("experts").select("name").eq("id", current_expert_id).execute()
        auth_user_name = None
        try:
            auth_res = supabase.auth.admin.get_user_by_id(current_expert_id)
            if auth_res and auth_res.user:
                meta = auth_res.user.user_metadata or {}
                auth_user_name = meta.get("name") or (auth_res.user.email.split("@")[0] if auth_res.user.email else None)
        except Exception:
            pass

        expert_name = request.name or (existing_expert.data[0]["name"] if existing_expert.data and existing_expert.data[0].get("name") else auth_user_name) or "Expert"

        # Upsert Expert (handle case where row might not have been created by Auth Trigger)
        expert_res = supabase.table("experts").upsert({
            "id": current_expert_id,
            "name": expert_name,
            "domain": request.domain,
            "stream_type": request.stream_type,
            "course_title": request.course_title,
            "course_description": request.course_description,
            "target_audience": request.target_audience,
            "expertise_streams": request.expertise_streams,
            "years_of_experience": request.years_of_experience,
            "short_bio": request.short_bio,
            "linkedin_url": request.linkedin_url
        }).execute()
        
        expert_id = current_expert_id
        
        # Fire Intake domain logic to get icebreaker
        icebreaker_data = await interview_domain.intake(expert_id)
        
        # Create a dedicated knowledge source for this session's vector embeddings
        source_res = supabase.table("knowledge_sources").insert({
            "source_type": "transcript",
            "title": f"Live Interview - {expert_name} - Iteration 1",
            "global_summary": "Auto-generated vector memory for live interview session.",
            "author_or_channel": "AI Journalist"
        }).execute()
        source_id = source_res.data[0]["id"]
        
        # Create Iteration 1 session
        session_res = supabase.table("interview_sessions").insert({
            "expert_id": expert_id,
            "iteration_number": 1,
            "status": "active",
            "live_transcript_source_id": source_id
        }).execute()
        
        logger.info(f"session_res.data: {session_res.data}")
        
        return {
            "status": "success",
            "expert_id": expert_id,
            "session_id": session_res.data[0]["id"],
            "icebreaker": icebreaker_data
        }
    except Exception as e:
        logger.error(f"Intake error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-script")
async def generate_script_endpoint(current_expert_id: str = Depends(get_current_expert_id)):
    """Generate interview script for the current session iteration."""
    try:
        expert_res = supabase.table("experts").select("*").eq("id", current_expert_id).execute()
        expert = expert_res.data[0] if expert_res.data else {}
        
        script_data = await interview_domain.generate_script(current_expert_id)
        return {"status": "success", "script": script_data, "expert": expert}
    except Exception as e:
        logger.error(f"Script generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# PHASE 1: COURSE DISCOVERY ENGINE
# ============================================================

class CourseDiscoveryRequest(BaseModel):
    session_id: str
    expert_answer: str

@app.post("/course-discovery-turn")
async def course_discovery_turn_endpoint(
    request: CourseDiscoveryRequest,
    current_expert_id: str = Depends(get_current_expert_id)
):
    """
    Phase 1 — Course Discovery Engine.

    Accepts one expert answer at a time and returns the next podcast-style
    question that naturally discovers the course identity.

    Sequence: course_context → student_personas → duration_weeks → course_title.

    When phase_complete=True, all four fields have been synthesized and written
    to the existing DB columns. The frontend should transition to Module 3
    (Module Discovery) at this point.
    """
    try:
        # Ownership check
        session_res = supabase.table("interview_sessions").select("expert_id").eq("id", request.session_id).execute()
        if not session_res.data or session_res.data[0]["expert_id"] != current_expert_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        result = await interview_domain.course_discovery_turn(
            session_id=request.session_id,
            expert_answer=request.expert_answer
        )
        return {"status": "success", **result}
    except Exception as e:
        logger.error(f"Course discovery turn error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# PHASE 2: MODULE DISCOVERY ENGINE
# ============================================================

class ModuleDiscoveryRequest(BaseModel):
    session_id: str
    expert_answer: str

@app.post("/module-discovery-turn")
async def module_discovery_turn_endpoint(
    request: ModuleDiscoveryRequest,
    current_expert_id: str = Depends(get_current_expert_id)
):
    """
    Phase 2 — Module Discovery Engine.

    Accepts one expert answer at a time and discovers module titles
    through natural podcast-style conversation.

    Owns ONLY module_title. Never touches topics, context, or other fields.

    Includes a Curriculum Saturation Check before exit:
    - If saturation passes → phase_complete=True, modules persisted to DB.
    - If saturation fails  → a recovery question is returned.

    When phase_complete=True, the frontend should transition to per-module
    topic extraction (live-turn with Module Discovery in script).
    """
    try:
        # Ownership check
        session_res = supabase.table("interview_sessions").select("expert_id").eq("id", request.session_id).execute()
        if not session_res.data or session_res.data[0]["expert_id"] != current_expert_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        result = await interview_domain.module_discovery_turn(
            session_id=request.session_id,
            expert_answer=request.expert_answer
        )
        return {"status": "success", **result}
    except Exception as e:
        logger.error(f"Module discovery turn error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# PHASE 3: MODULE ENRICHMENT ENGINE
# ============================================================

class ModuleEnrichmentRequest(BaseModel):
    session_id: str
    expert_answer: str

@app.post("/module-enrichment-turn")
async def module_enrichment_turn_endpoint(
    request: ModuleEnrichmentRequest,
    current_expert_id: str = Depends(get_current_expert_id)
):
    """
    Phase 3 — Module Enrichment Engine.

    Enriches modules one-by-one with:
      - module_context    (why this module exists)
      - learning_outcomes (what learners become capable of)
      - module_constraints (prerequisites and learning boundaries)

    Owns ONLY these three fields. Never touches topics.

    Advances automatically to the next module when the current one
    is fully enriched. Signals phase_complete=True when all modules
    have been enriched.

    Response includes current_module_idx / total_modules so the
    frontend can render a progress indicator.
    """
    try:
        # Ownership check
        session_res = supabase.table("interview_sessions").select("expert_id").eq("id", request.session_id).execute()
        if not session_res.data or session_res.data[0]["expert_id"] != current_expert_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        result = await interview_domain.module_enrichment_turn(
            session_id=request.session_id,
            expert_answer=request.expert_answer
        )
        return {"status": "success", **result}
    except Exception as e:
        logger.error(f"Module enrichment turn error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# PHASE 4: TOPIC DISCOVERY ENGINE
# ============================================================

class TopicDiscoveryRequest(BaseModel):
    session_id: str
    expert_answer: str

@app.post("/topic-discovery-turn")
async def topic_discovery_turn_endpoint(
    request: TopicDiscoveryRequest,
    current_expert_id: str = Depends(get_current_expert_id)
):
    """
    Phase 4 — Topic Discovery Engine.

    Discovers topic_titles for each module, one module at a time.
    Owns ONLY topics[].topic_title — never touches any deeper field.

    Exit gate: Learning Outcome Coverage Validator cross-checks every
    discovered topic against every module learning_outcome before advancing.
    If any outcome is uncovered, a recovery question is returned.

    Returns current_module_idx / total_modules for frontend progress bar.
    phase_complete=True when every module has its full topic list validated.
    """
    try:
        # Ownership check
        session_res = supabase.table("interview_sessions").select("expert_id").eq("id", request.session_id).execute()
        if not session_res.data or session_res.data[0]["expert_id"] != current_expert_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        result = await interview_domain.topic_discovery_turn(
            session_id=request.session_id,
            expert_answer=request.expert_answer
        )
        return {"status": "success", **result}
    except Exception as e:
        logger.error(f"Topic discovery turn error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# PHASE 5: CURRICULUM VALIDATION & LOCK ENGINE
# ============================================================

class CurriculumValidationRequest(BaseModel):
    session_id: str

@app.post("/curriculum-validation")
async def curriculum_validation_endpoint(
    request: CurriculumValidationRequest,
    current_expert_id: str = Depends(get_current_expert_id)
):
    """
    Phase 5 — Curriculum Validation & Lock Engine.

    Validates the entire curriculum structure and decides whether to lock.
    Does NOT conduct interviews or accept/generate follow-up questions.

    Returns the lock decision, detailed validation report, and next_state.
    """
    try:
        # Ownership check
        session_res = supabase.table("interview_sessions").select("expert_id").eq("id", request.session_id).execute()
        if not session_res.data or session_res.data[0]["expert_id"] != current_expert_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        result = await interview_domain.validate_and_lock_curriculum(
            session_id=request.session_id
        )
        return {"status": "success", **result}
    except Exception as e:
        logger.error(f"Curriculum validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# PHASE 6: TOPIC INITIALIZATION ENGINE
# ============================================================

class TopicInitializationRequest(BaseModel):
    session_id: str
    expert_answer: Optional[str] = None

@app.post("/topic-initialization")
async def topic_initialization_endpoint(
    request: TopicInitializationRequest,
    current_expert_id: str = Depends(get_current_expert_id)
):
    """
    Phase 6 — Topic Initialization Engine.

    Prepares the interview for exploring exactly one incomplete topic.
    Selects the next highest-priority incomplete topic and returns a
    warm conversationaltransition question.

    Sets state: current_module, current_topic, status = "IN_PROGRESS".
    """
    try:
        # Ownership check
        session_res = supabase.table("interview_sessions").select("expert_id").eq("id", request.session_id).execute()
        if not session_res.data or session_res.data[0]["expert_id"] != current_expert_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        result = await interview_domain.topic_initialization_turn(
            session_id=request.session_id,
            expert_answer=request.expert_answer
        )
        return {"status": "success", **result}
    except Exception as e:
        logger.error(f"Topic initialization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# PHASE 7-11: TOPIC KNOWLEDGE EXPLORATION ENGINE
# ============================================================

class TopicExplorationRequest(BaseModel):
    session_id: str
    expert_answer: str

@app.post("/topic-exploration")
async def topic_exploration_endpoint(
    request: TopicExplorationRequest,
    current_expert_id: str = Depends(get_current_expert_id)
):
    """
    Phase 7-11 — Topic Knowledge Exploration Engine.

    Accepts the expert's answer and evaluates coverage, manages gaps,
    transitions through the 5 natural conversation lenses, and extracts
    structured JSON to the blueprint once the topic is completed.

    Lenses: understanding → teaching → failure → experience → mastery.
    """
    try:
        # Ownership check
        session_res = supabase.table("interview_sessions").select("expert_id").eq("id", request.session_id).execute()
        if not session_res.data or session_res.data[0]["expert_id"] != current_expert_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        result = await interview_domain.topic_exploration_turn(
            session_id=request.session_id,
            expert_answer=request.expert_answer
        )
        return {"status": "success", **result}
    except Exception as e:
        logger.error(f"Topic exploration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# PHASE 12: LIVE INTERVIEW LOOP
# ============================================================

@app.get("/session/{session_id}")
async def get_session_endpoint(session_id: str, current_expert_id: str = Depends(get_current_expert_id)):
    """Fetch session data including the generated script and topic progress."""
    try:
        res = supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
        if not res.data or res.data[0]["expert_id"] != current_expert_id:
            raise HTTPException(status_code=404, detail="Session not found")
        tp_res = supabase.table("topic_progress").select("*").eq("session_id", session_id).execute()
        return {
            "status": "success",
            "session": res.data[0],
            "topic_progress": tp_res.data or []
        }
    except Exception as e:
        logger.error(f"Get session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/live-turn")
async def live_turn_endpoint(request: LiveTurnRequest, background_tasks: BackgroundTasks, current_expert_id: str = Depends(get_current_expert_id)):
    """Phase 3: Classify intent and generate next conversational follow-up."""
    try:
        # Check ownership
        session_res = supabase.table("interview_sessions").select("expert_id").eq("id", request.session_id).execute()
        if not session_res.data or session_res.data[0]["expert_id"] != current_expert_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        result = await interview_domain.live_turn(
            session_id=request.session_id,
            expert_answer=request.expert_answer,
            request_data={
                "current_script_question": request.current_script_question,
                "active_block": request.active_block,
                "tangent_count": request.tangent_count  # Used as boundary signal (== 0 means new script Q)
            }
        )

        # Long-Term Vector Memory: embed the expert's answer semantically (background is fine here)
        background_tasks.add_task(
            interview_domain.background_embed_turn,
            request.session_id,
            request.expert_answer,
            embeddings_model
        )
        
        # Real-Time Atomic Tacit Knowledge Extraction
        background_tasks.add_task(
            interview_domain.background_extract_and_save_knowledge,
            request.session_id,
            current_expert_id,
            request.current_script_question,
            request.expert_answer,
            request.active_block,
            "General Topic"
        )
        
        # Fetch updated topic progress checklist
        tp_res = supabase.table("topic_progress").select("*").eq("session_id", request.session_id).execute()
        result["topic_progress"] = tp_res.data or []

        return result
    except Exception as e:
        logger.error(f"Live turn error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/insights/{session_id}")
async def get_insights_endpoint(session_id: str, current_expert_id: str = Depends(get_current_expert_id)):
    """Fetch granular insights extracted for verification."""
    try:
        # Check ownership of session
        session_res = supabase.table("interview_sessions").select("expert_id").eq("id", session_id).execute()
        if not session_res.data or session_res.data[0]["expert_id"] != current_expert_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        res = supabase.table("expert_tacit_insights").select("*").eq("session_id", session_id).execute()
        return {"status": "success", "insights": res.data or []}
    except Exception as e:
        logger.error(f"Get insights error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/insights/verify")
async def verify_insights_endpoint(request: VerifyInsightsRequest, current_expert_id: str = Depends(get_current_expert_id)):
    """Submit verifications (Approve/Reject/Modify) for extracted insights."""
    try:
        for item in request.insights:
            # Check ownership of the insight first
            insight_res = supabase.table("expert_tacit_insights").select("expert_id").eq("id", item.id).execute()
            if not insight_res.data or insight_res.data[0]["expert_id"] != current_expert_id:
                continue
            
            update_data = {
                "status": item.status
            }
            if item.title:
                update_data["title"] = item.title
            if item.content:
                update_data["content"] = item.content
            if item.expert_quote:
                update_data["expert_quote"] = item.expert_quote

            supabase.table("expert_tacit_insights").update(update_data).eq("id", item.id).execute()

        return {"status": "success", "message": "Insights verification updated successfully."}
    except Exception as e:
        logger.error(f"Verify insights error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio via Deepgram."""
    if not DEEPGRAM_API_KEY:
        raise HTTPException(status_code=500, detail="Deepgram API key not configured.")
    try:
        audio_bytes = await audio.read()
        if not audio_bytes or len(audio_bytes) < 100:
            logger.warning(f"Empty or tiny audio received: {len(audio_bytes)} bytes")
            return {"transcript": ""}
        
        logger.info(f"Transcribing audio: {len(audio_bytes)} bytes, type={audio.content_type}")
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&language=en",
                headers={"Authorization": f"Token {DEEPGRAM_API_KEY}", "Content-Type": audio.content_type or "audio/webm"},
                content=audio_bytes,
            )
        if resp.status_code != 200:
            logger.error(f"Deepgram API error: {resp.status_code} - {resp.text[:200]}")
            raise HTTPException(status_code=502, detail=f"Deepgram API error: {resp.status_code}")
        transcript = resp.json().get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")
        return {"transcript": transcript}
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Transcription timed out.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {type(e).__name__}")

# ============================================================
# PHASE 4+5: POST-SESSION SYNTHESIS & HOMEWORK
# ============================================================

@app.post("/end-session/{session_id}")
async def end_session_endpoint(session_id: str, current_expert_id: str = Depends(get_current_expert_id)):
    """Phase 4 & 5: Run extraction on full transcript, generate open loops, and auto-create Part 2."""
    try:
        session_res = supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
        if not session_res.data or session_res.data[0]["expert_id"] != current_expert_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Mark ended_at and update status to completed
        supabase.table("interview_sessions").update({
            "status": "completed",
            "ended_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", session_id).execute()

        # Run Synthesis (Phase 4)
        synth_result = await interview_domain.synthesize(session_id)
        
        # Run Homework Generator (Phase 5)
        hw_result = await interview_domain.generate_homework(session_id)
        
        # Auto-create Session Part 2
        prior_session = session_res.data[0]
        next_iter = prior_session.get("iteration_number", 1) + 1
        expert_res = supabase.table("experts").select("name").eq("id", current_expert_id).execute()
        expert_name = expert_res.data[0]["name"] if expert_res.data else "Expert"

        source_res = supabase.table("knowledge_sources").insert({
            "source_type": "transcript",
            "title": f"Live Interview - {expert_name} - Iteration {next_iter}",
            "global_summary": "Auto-generated vector memory for live interview session part 2.",
            "author_or_channel": "AI Journalist"
        }).execute()
        source_id = source_res.data[0]["id"]

        prior_block = prior_session.get("current_block") or "Block 1"
        next_block_num = next_iter
        next_block_str = f"Block {next_block_num}"

        # Get flat list of themes from script to locate the next block and its opener question
        prior_script = prior_session.get("script") or {}
        extracted_themes = []
        module_backlog = prior_script.get("module_backlog") or []
        
        if module_backlog:
            global_idx = 0
            for mod in module_backlog:
                mod_title = mod.get("module_title", "")
                for topic in mod.get("topics") or []:
                    topic_title = topic.get("topic_title", "")
                    extracted_themes.append({
                        "theme_id": global_idx,
                        "theme_title": f"{mod_title} - {topic_title}".strip(" -"),
                        "questions": [{"id": "opener", "question_text": topic.get("opener_question", "")}]
                    })
                    global_idx += 1
        elif prior_script.get("topic_backlog"):
            for idx, block in enumerate(prior_script.get("topic_backlog") or []):
                topic_title = block.get("topic_title") or f"Block {idx+1}"
                extracted_themes.append({
                    "theme_id": idx,
                    "theme_title": topic_title,
                    "questions": [{"id": "opener", "question_text": block.get("opener_question", "")}]
                })
        elif isinstance(prior_script.get("interview_arc"), list):
            extracted_themes = prior_script.get("interview_arc")

        # Determine next theme title and opener question
        next_theme_title = next_block_str
        next_opener_q = ""
        target_idx = next_block_num - 1
        
        if extracted_themes and 0 <= target_idx < len(extracted_themes):
            next_theme_title = extracted_themes[target_idx].get("theme_title", next_block_str)
            questions = extracted_themes[target_idx].get("questions", [])
            if questions:
                next_opener_q = questions[0].get("question_text", "")
        else:
            # Fallback: string matching
            for t in extracted_themes:
                title = t.get("theme_title", "").lower()
                if next_block_str.lower() in title:
                    next_theme_title = t.get("theme_title")
                    questions = t.get("questions", [])
                    if questions:
                        next_opener_q = questions[0].get("question_text", "")
                    break

        initial_snapshot = {
            "current_script_question": next_opener_q,
            "active_block": next_theme_title,
            "tangent_count": 0,
            "paused_at": datetime.now(timezone.utc).isoformat()
        }

        next_sess_res = supabase.table("interview_sessions").insert({
            "expert_id": current_expert_id,
            "iteration_number": next_iter,
            "status": "paused",
            "live_transcript_source_id": source_id,
            "script": prior_session.get("script"),
            "current_block": next_theme_title,
            "raw_transcript": prior_session.get("raw_transcript"),
            "snapshot": initial_snapshot
        }).execute()
        next_session_id = next_sess_res.data[0]["id"] if next_sess_res.data else None

        hw_loops = (hw_result.get("homework") or {}).get("ai_open_loops", [])
        return {
            "status": "success",
            "message": "Session synthesized and next chapter prepared.",
            "synthesis": synth_result["session_synthesis"],
            "homework": hw_result["homework"],
            "has_pending_homework": len(hw_loops) > 0,
            "next_session_id": next_session_id
        }
    except Exception as e:
        logger.error(f"End session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# SESSION MANAGEMENT (PAUSE / RESUME)
# ============================================================

@app.get("/sessions/active")
async def get_active_session(current_expert_id: str = Depends(get_current_expert_id)):
    """Finds the most recent paused or active session for auto-resume after login."""
    res = supabase.table("interview_sessions")\
        .select("id, status, script, raw_transcript, snapshot, iteration_number")\
        .eq("expert_id", current_expert_id)\
        .in_("status", ["active", "paused"])\
        .order("iteration_number", desc=True)\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()
    
    if not res.data:
        return {"status": "none"}
        
    return {"status": "found", "session": res.data[0]}

@app.post("/pause-session/{session_id}")
async def pause_session_endpoint(session_id: str, request: PauseSessionRequest, current_expert_id: str = Depends(get_current_expert_id)):
    """Marks a session as paused and saves the exact current state snapshot."""
    # Verify ownership
    session_res = supabase.table("interview_sessions").select("expert_id").eq("id", session_id).execute()
    if not session_res.data or session_res.data[0]["expert_id"] != current_expert_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    snapshot_data = {
        "current_script_question": request.current_script_question,
        "active_block": request.active_block,
        "tangent_count": request.tangent_count,
        "paused_at": datetime.now(timezone.utc).isoformat()
    }
    
    supabase.table("interview_sessions").update({
        "status": "paused",
        "snapshot": snapshot_data
    }).eq("id", session_id).execute()
    
    return {"status": "paused"}

@app.post("/resume-session/{session_id}")
async def resume_session_endpoint(session_id: str, current_expert_id: str = Depends(get_current_expert_id)):
    """Restores a session and generates a contextual re-entry statement."""
    session_res = supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
    if not session_res.data or session_res.data[0]["expert_id"] != current_expert_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    session = session_res.data[0]
    snapshot = session.get("snapshot", {}) or {}
    
    # Update status to active
    supabase.table("interview_sessions").update({
        "status": "active"
    }).eq("id", session_id).execute()
    
    # Generate contextual re-entry statement
    raw_transcript = session.get("raw_transcript", "")
    last_question = snapshot.get("current_script_question", "We were discussing your expertise.")
    
    # Determine if the last turn was the expert (i.e., the last question was already answered)
    last_turn_was_expert = False
    if raw_transcript:
        # Clean trailing whitespace
        normalized_transcript = raw_transcript.strip()
        # Find the last occurrence of AI and EXPERT tags
        last_ai_idx = normalized_transcript.rfind("[AI JOURNALIST]:")
        last_expert_idx = normalized_transcript.rfind("[EXPERT]:")
        if last_expert_idx > last_ai_idx:
            last_turn_was_expert = True

    # If the last turn was the AI (meaning they paused mid-question, before answering),
    # extract and re-ask the exact last question the AI asked from the transcript.
    if raw_transcript and not last_turn_was_expert:
        parts = raw_transcript.split("[AI JOURNALIST]:")
        if len(parts) > 1:
            last_ai_part = parts[-1].split("[EXPERT]:")[0].strip()
            if last_ai_part:
                last_question = last_ai_part

    # Provide recent context for the summary, limit to 4000 chars to avoid prompt bloat
    transcript_context = raw_transcript[-4000:] if raw_transcript else "No prior conversation history."

    system_prompt = (
        "You are an expert journalist. The user has just returned from a break and resumed the interview session.\n"
        "Your task is to generate a natural, conversational 'Welcome back' re-entry statement.\n"
        "Do NOT use any markdown formatting, bullet points, numbers, or bold text. Just plain text.\n\n"
        "Your response MUST be separated into exactly 3 paragraphs (separated by blank lines):\n"
        "Paragraph 1: A brief, friendly greeting (e.g., 'Welcome back!').\n"
        "Paragraph 2: A 1-2 sentence summary of what the expert was discussing recently (based on the transcript context provided below).\n"
        f"Paragraph 3: Re-ask this exact question word-for-word: '{last_question}'\n\n"
        "Here is the recent transcript context for you to summarize:\n"
        f"{transcript_context}"
    )
    
    try:
        response = await llm.ainvoke(system_prompt)
        reentry_statement = response.content
    except Exception as e:
        import logging
        logging.error(f"Failed to generate re-entry statement: {e}")
        reentry_statement = f"Welcome back! Before we paused, you were discussing '{last_question}'. Let's pick up where we left off."

    # Append the welcome back statement to the database raw_transcript so it persists across focus / tab refreshes
    new_transcript = raw_transcript
    if new_transcript:
        new_transcript = new_transcript.strip() + f"\n\n[AI JOURNALIST]: {reentry_statement}"
    else:
        new_transcript = f"[AI JOURNALIST]: {reentry_statement}"

    # Update status to active and save the updated transcript
    supabase.table("interview_sessions").update({
        "status": "active",
        "raw_transcript": new_transcript
    }).eq("id", session_id).execute()
    
    return {
        "status": "resumed",
        "reentry_statement": reentry_statement,
        "snapshot": snapshot,
        "raw_transcript": new_transcript,
        "script": session.get("script", {})
    }


@app.get("/homework")
async def get_homework(current_expert_id: str = Depends(get_current_expert_id)):
    """Fetch latest homework ledger for dashboard."""
    try:
        res = supabase.table("homework_ledger").select("*").eq("expert_id", current_expert_id).order("created_at", desc=True).limit(1).execute()
        if not res.data:
            return {"status": "success", "homework": None}
        return {"status": "success", "homework": res.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/homework/{homework_id}")
async def put_homework(homework_id: str, request: HomeworkPutRequest, current_expert_id: str = Depends(get_current_expert_id)):
    """Journalist saves manual research notes."""
    try:
        # Verify ownership
        hw_res = supabase.table("homework_ledger").select("expert_id").eq("id", homework_id).execute()
        if not hw_res.data or hw_res.data[0]["expert_id"] != current_expert_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        supabase.table("homework_ledger").update({
            "human_manual_notes": request.human_manual_notes,
            "status": "completed"
        }).eq("id", homework_id).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/homework/submit-evidence")
async def submit_evidence_endpoint(request: SubmitEvidenceRequest, background_tasks: BackgroundTasks, current_expert_id: str = Depends(get_current_expert_id)):
    result = await interview_domain.submit_evidence(
        expert_id=current_expert_id,
        session_id=request.session_id,
        iteration_number=request.iteration_number,
        loop_topic=request.loop_topic,
        material_type=request.material_type,
        content_or_url=request.content_or_url,
        resource_mentioned=request.resource_mentioned or "",
        what_expert_claimed=request.what_expert_claimed or ""
    )
    background_tasks.add_task(
        interview_domain.background_verify_evidence,
        result["material_id"],
        request.loop_topic,
        request.material_type,
        request.content_or_url,
        request.resource_mentioned or "",
        request.what_expert_claimed or ""
    )
    return result

@app.get("/homework/verification-status/{session_id}")
async def get_verification_status(session_id: str, current_expert_id: str = Depends(get_current_expert_id)):
    try:
        res = supabase.table("submitted_materials").select("*").eq("session_id", session_id).execute()
        return {"status": "success", "materials": res.data or []}
    except Exception:
        return {"status": "success", "materials": []}

# ============================================================
# PHASE 6: FLYWHEEL BRIDGE
# ============================================================

@app.post("/start-session")
async def start_session_endpoint(current_expert_id: str = Depends(get_current_expert_id)):
    """Phase 6: Create new session iteration and generate trust-signal opener."""
    try:
        # Find latest session
        sessions_res = supabase.table("interview_sessions").select("*").eq("expert_id", current_expert_id).order("iteration_number", desc=True).limit(1).execute()
        prior_session = sessions_res.data[0] if sessions_res.data else {}
        next_iter = (prior_session.get("iteration_number") or 1) + 1 if prior_session else 2
        prior_script = prior_session.get("script")
        prior_transcript = prior_session.get("raw_transcript") or ""

        expert_res = supabase.table("experts").select("*").eq("id", current_expert_id).execute()
        expert_name = expert_res.data[0]["name"] if expert_res.data else "Expert"

        # Create a dedicated knowledge source for this session's vector embeddings
        source_res = supabase.table("knowledge_sources").insert({
            "source_type": "transcript",
            "title": f"Live Interview - {expert_name} - Iteration {next_iter}",
            "global_summary": "Auto-generated vector memory for live interview session.",
            "author_or_channel": "AI Journalist"
        }).execute()
        source_id = source_res.data[0]["id"]

        # Create new session
        session_res = supabase.table("interview_sessions").insert({
            "expert_id": current_expert_id,
            "iteration_number": next_iter,
            "status": "active",
            "live_transcript_source_id": source_id,
            "script": prior_script,
            "current_block": "Block 2"
        }).execute()
        session_id = session_res.data[0]["id"]
        
        # Fire Flywheel Bridge
        opener_data = await interview_domain.flywheel_bridge(current_expert_id)
        bridge_opener = opener_data.get("bridge_opener", "") if isinstance(opener_data, dict) else ""
        if bridge_opener:
            new_transcript = prior_transcript.rstrip() + f"\n[AI]: {bridge_opener}" if prior_transcript else f"[AI]: {bridge_opener}"
            try:
                supabase.table("interview_sessions").update({
                    "raw_transcript": new_transcript
                }).eq("id", session_id).execute()
            except Exception as e:
                logger.warning(f"Could not update raw_transcript on new session: {e}")
        
        return {
            "status": "success",
            "session_id": session_id,
            "iteration_number": next_iter,
            "opener": opener_data
        }
    except Exception as e:
        logger.error(f"Start session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# FIELD SUGGESTIONS (AUTOCOMPLETE CACHE)
# ============================================================

@app.get("/field-suggestions")
async def get_field_suggestions(current_expert_id: str = Depends(get_current_expert_id)):
    """Returns previously used distinct values for intake form fields from all experts."""
    try:
        res = supabase.table("experts").select(
            "domain, target_audience, short_bio, years_of_experience"
        ).order("created_at", desc=True).limit(50).execute()

        domains, audiences, bios, years = set(), set(), set(), set()
        for row in res.data:
            if row.get("domain"): domains.add(row["domain"])
            if row.get("target_audience"): audiences.add(row["target_audience"])
            if row.get("short_bio"): bios.add(row["short_bio"])
            if row.get("years_of_experience") is not None:
                years.add(row["years_of_experience"])

        return {
            "status": "success",
            "suggestions": {
                "domain": sorted(list(domains)),
                "target_audience": sorted(list(audiences)),
                "short_bio": sorted(list(bios)),
                "years_of_experience": sorted(list(years))
            }
        }
    except Exception as e:
        logger.error(f"Field suggestions error: {e}")
        return {"status": "success", "suggestions": {}}

# ============================================================
# KNOWLEDGE REPORTS (DASHBOARD)
# ============================================================

@app.get("/knowledge-report")
async def get_knowledge_report(current_expert_id: str = Depends(get_current_expert_id)):
    """Returns the unified knowledge output:
       { persona, course (modules→topics→7 slots), tacit_insights, war_stories, mental_models }
    """
    try:
        # Primary source: tacit_knowledge_reports
        tk_res = (
            supabase.table("tacit_knowledge_reports")
            .select("*")
            .eq("expert_id", current_expert_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if tk_res.data:
            report = tk_res.data[0]
            stn = report.get("structured_tacit_notes", {})
            ko = {
                "persona": report.get("persona_snapshot", {}),
                "course": report.get("course_structure", {}),
                "tacit_insights": stn.get("tacit_insights", []),
                "war_stories": stn.get("war_stories", []),
                "mental_models": stn.get("mental_models", []),
                "pattern_breaks": stn.get("pattern_breaks", []),
                "structured_tacit_notes": stn.get("tutor_notes", [])
            }
            return {"status": "success", "knowledge_output": ko}

        # Fallback: latest synthesized session for this expert
        sess_res = (
            supabase.table("interview_sessions")
            .select("session_synthesis, status, iteration_number")
            .eq("expert_id", current_expert_id)
            .eq("status", "synthesized")
            .order("iteration_number", desc=True)
            .limit(1)
            .execute()
        )

        if sess_res.data and sess_res.data[0].get("session_synthesis"):
            synth = sess_res.data[0]["session_synthesis"]
            ko = synth.get("knowledge_output")
            if ko:
                return {"status": "success", "knowledge_output": ko}
            # Legacy fallback: sessions synthesized before the knowledge_output key existed
            general = synth.get("general", {})
            tutor = synth.get("tutor", {})
            persona_raw = tutor.get("tutor_persona", {})
            ko = {
                "persona": {
                    "system_prompt": persona_raw.get("system_prompt", ""),
                    "teaching_style": persona_raw.get("teaching_style", ""),
                    "linguistic_fingerprint": persona_raw.get("linguistic_fingerprint", {})
                },
                "course": tutor.get("course_structure", {}),
                "tacit_insights": general.get("tacit_insights", []),
                "war_stories": general.get("war_stories", []),
                "mental_models": general.get("mental_models", []),
                "pattern_breaks": general.get("pattern_breaks", []),
                "structured_tacit_notes": tutor.get("structured_tacit_notes", [])
            }
            return {"status": "success", "knowledge_output": ko}

        # Final fallback: read raw from expert_profile + curriculum_blueprints tables
        ep_res = supabase.table("expert_profile").select("*").eq("expert_id", current_expert_id).execute()
        cb_res = supabase.table("curriculum_blueprints").select("*").eq("expert_id", current_expert_id).execute()
        ep = ep_res.data[0] if ep_res.data else {}
        cb = cb_res.data[0] if cb_res.data else {}
        ko = {
            "persona": {
                "system_prompt": ep.get("system_prompt", ""),
                "teaching_style": ep.get("teaching_style", ""),
                "linguistic_fingerprint": ep.get("linguistic_fingerprint", {})
            },
            "course": {"modules": cb.get("course_modules", [])},
            "tacit_insights": ep.get("tacit_insights", []),
            "war_stories": ep.get("war_stories", []),
            "mental_models": ep.get("mental_models", []),
            "pattern_breaks": ep.get("pattern_breaks", []),
            "structured_tacit_notes": []
        }
        return {"status": "success", "knowledge_output": ko}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# RAG INGESTION HELPERS (KEPT AS-IS)
# ============================================================

def fetch_youtube_transcript(url: str) -> str:
    video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    if not video_id_match:
        raise ValueError("Invalid YouTube URL")
    video_id = video_id_match.group(1)
    api = YouTubeTranscriptApi()
    try:
        transcript_list = api.fetch(video_id, languages=['en', 'hi', 'te'])
    except Exception as e:
        try:
            transcripts = api.list(video_id)
            transcript_list = transcripts.find_transcript(['en', 'hi', 'te']).fetch()
        except:
            transcripts = api.list(video_id)
            transcript_list = next(iter(transcripts)).fetch()
    full_text = " ".join([item.text for item in transcript_list])
    return full_text, video_id

async def background_ingest_documents(session_id: str, file_paths: List[str], filenames: List[str], domain: str):
    try:
        from ingest_data import chunk_by_characters
        for fp, fname in zip(file_paths, filenames):
            ext = os.path.splitext(fname)[1].lower()
            text = ""
            if ext == '.txt':
                with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            elif ext == '.docx':
                from ingest_data import read_docx_file
                text = read_docx_file(fp)
            elif ext == '.pdf':
                import fitz
                doc = fitz.open(fp)
                text = "\\n".join(page.get_text() for page in doc)
            else:
                logger.warning(f"Unsupported extension: {ext}")
                continue
            
            chunks = chunk_by_characters(text)
            
            source_res = supabase.table("knowledge_sources").insert({
                "source_type": "transcript",
                "title": fname,
                "global_summary": f"Uploaded document for session {session_id}",
                "author_or_channel": "User Upload"
            }).execute()
            source_id = source_res.data[0]["id"]
            
            for c in chunks:
                emb = embeddings_model.embed_query(c["content"])
                supabase.table("knowledge_chunks").insert({
                    "source_id": source_id,
                    "content": c["content"],
                    "embedding": emb,
                    "location_marker": c["location_marker"]
                }).execute()
            
            os.remove(fp)
        logger.info(f"Finished ingesting documents for {session_id}")
    except Exception as e:
        logger.error(f"Error in background ingest: {e}")

@app.post("/ingest")
async def ingest_documents_endpoint(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    domain: str = Form(...),
    user_session_id: str = Form(...),
    current_expert_id: str = Depends(get_current_expert_id)
):
    try:
        # Check ownership
        session_res = supabase.table("interview_sessions").select("expert_id").eq("id", user_session_id).execute()
        if not session_res.data or session_res.data[0]["expert_id"] != current_expert_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        temp_paths = []
        filenames = []
        for file in files:
            fd, path = tempfile.mkstemp(suffix=os.path.splitext(file.filename)[1])
            with os.fdopen(fd, 'wb') as f:
                shutil.copyfileobj(file.file, f)
            temp_paths.append(path)
            filenames.append(file.filename)
            
        background_tasks.add_task(background_ingest_documents, user_session_id, temp_paths, filenames, domain)
        return {"status": "success", "message": f"Processing {len(files)} files in the background."}
    except Exception as e:
        logger.error(f"Ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9120)
