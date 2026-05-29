"""
Centralized configuration for the AI Course Architect backend.
All environment variables, constants, and client initialization live here.
"""

import os
import logging
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path, override=True)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("course_architect")

# ---------------------------------------------------------------------------
# Supabase
# ---------------------------------------------------------------------------
SUPABASE_URL: str = os.getenv("SUPABASE_URL") or os.getenv("SUPABASE_DB_URL", "")
SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")

# ---------------------------------------------------------------------------
# OpenAI / LLM
# ---------------------------------------------------------------------------
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_FAST_MODEL: str = os.getenv("LLM_FAST_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# ---------------------------------------------------------------------------
# Deepgram (speech-to-text)
# ---------------------------------------------------------------------------
DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")

# ---------------------------------------------------------------------------
# RAG / Chunking
# ---------------------------------------------------------------------------
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
TOP_K_RAG: int = int(os.getenv("TOP_K_RAG", "4"))
RAG_MATCH_THRESHOLD: float = float(os.getenv("RAG_MATCH_THRESHOLD", "0.3"))

# ---------------------------------------------------------------------------
# Interview
# ---------------------------------------------------------------------------
MAX_FOLLOWUPS_PER_QUESTION: int = int(os.getenv("MAX_FOLLOWUPS_PER_QUESTION", "2"))
DEFAULT_TOPIC: str = "Domain expertise as identified from the ingested knowledge base"

# ---------------------------------------------------------------------------
# CORS – allowed origins (comma-separated in env, or sensible default)
# ---------------------------------------------------------------------------
_raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:9110,http://localhost:9111")
CORS_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]
