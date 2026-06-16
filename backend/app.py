import os
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
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi

from domains.interview import InterviewDomain

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path, override=True)
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
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

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
llm_fast = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, max_tokens=30, timeout=30)
embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")

# Domain Registry (Unified)
interview_domain = InterviewDomain(llm, supabase)

# ============================================================
# MODELS
# ============================================================

class ExpertIntakeRequest(BaseModel):
    name: str
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

# ============================================================
# PHASE 2: INTAKE & SCRIPT GENERATION
# ============================================================

@app.post("/intake")
async def intake_endpoint(request: ExpertIntakeRequest):
    """Phase 2: Save expert profile and generate Day 1 Icebreaker."""
    try:
        # Insert Expert
        expert_res = supabase.table("experts").insert({
            "name": request.name,
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
        
        expert_id = expert_res.data[0]["id"]
        
        # Fire Intake domain logic to get icebreaker
        icebreaker_data = await interview_domain.intake(expert_id)
        
        # Create Iteration 1 session
        session_res = supabase.table("interview_sessions").insert({
            "expert_id": expert_id,
            "iteration_number": 1,
            "status": "active"
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

@app.post("/generate-script/{expert_id}")
async def generate_script_endpoint(expert_id: str):
    """Generate interview script for the current session iteration."""
    try:
        expert_res = supabase.table("experts").select("*").eq("id", expert_id).execute()
        expert = expert_res.data[0] if expert_res.data else {}
        
        script_data = await interview_domain.generate_script(expert_id)
        return {"status": "success", "script": script_data, "expert": expert}
    except Exception as e:
        logger.error(f"Script generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# PHASE 3: LIVE INTERVIEW LOOP
# ============================================================

@app.get("/session/{session_id}")
async def get_session_endpoint(session_id: str):
    """Fetch session data including the generated script."""
    try:
        res = supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"status": "success", "session": res.data[0]}
    except Exception as e:
        logger.error(f"Get session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/live-turn")
async def live_turn_endpoint(request: LiveTurnRequest):
    """Phase 3: Classify intent and generate next conversational follow-up."""
    try:
        result = await interview_domain.live_turn(
            session_id=request.session_id,
            expert_answer=request.expert_answer,
            request_data={
                "current_script_question": request.current_script_question,
                "active_block": request.active_block,
                "tangent_count": request.tangent_count
            }
        )
        return result
    except Exception as e:
        logger.error(f"Live turn error: {e}")
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
async def end_session_endpoint(session_id: str):
    """Phase 4 & 5: Run extraction on full transcript and generate open loops."""
    try:
        # Mark ended_at
        supabase.table("interview_sessions").update({
            "ended_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", session_id).execute()

        # Run Synthesis (Phase 4)
        synth_result = await interview_domain.synthesize(session_id)
        
        # Run Homework Generator (Phase 5)
        hw_result = await interview_domain.generate_homework(session_id)
        
        return {
            "status": "success",
            "message": "Session synthesized and homework generated.",
            "synthesis": synth_result["session_synthesis"],
            "homework": hw_result["homework"]
        }
    except Exception as e:
        logger.error(f"End session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/homework/{expert_id}")
async def get_homework(expert_id: str):
    """Fetch latest homework ledger for dashboard."""
    try:
        res = supabase.table("homework_ledger").select("*").eq("expert_id", expert_id).order("created_at", desc=True).limit(1).execute()
        if not res.data:
            return {"status": "success", "homework": None}
        return {"status": "success", "homework": res.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/homework/{homework_id}")
async def put_homework(homework_id: str, request: HomeworkPutRequest):
    """Journalist saves manual research notes."""
    try:
        supabase.table("homework_ledger").update({
            "human_manual_notes": request.human_manual_notes,
            "status": "completed"
        }).eq("id", homework_id).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# PHASE 6: FLYWHEEL BRIDGE
# ============================================================

@app.post("/start-session/{expert_id}")
async def start_session_endpoint(expert_id: str):
    """Phase 6: Create new session iteration and generate trust-signal opener."""
    try:
        # Find latest iteration number
        sessions_res = supabase.table("interview_sessions").select("iteration_number").eq("expert_id", expert_id).order("iteration_number", desc=True).limit(1).execute()
        next_iter = 2
        if sessions_res.data:
            next_iter = sessions_res.data[0]["iteration_number"] + 1

        # Create new session
        session_res = supabase.table("interview_sessions").insert({
            "expert_id": expert_id,
            "iteration_number": next_iter,
            "status": "active"
        }).execute()
        session_id = session_res.data[0]["id"]
        
        # Fire Flywheel Bridge
        opener_data = await interview_domain.flywheel_bridge(expert_id)
        
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
# KNOWLEDGE REPORTS (DASHBOARD)
# ============================================================

@app.get("/knowledge-report/{expert_id}")
async def get_knowledge_report(expert_id: str):
    """Returns accumulated expert profile + curriculum blueprints."""
    try:
        ep_res = supabase.table("expert_profile").select("*").eq("expert_id", expert_id).execute()
        cb_res = supabase.table("curriculum_blueprints").select("*").eq("expert_id", expert_id).execute()
        
        return {
            "status": "success",
            "expert_profile": ep_res.data[0] if ep_res.data else {},
            "curriculum_blueprints": cb_res.data[0] if cb_res.data else {}
        }
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
                "source_type": "document",
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
    user_session_id: str = Form(...)
):
    try:
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
