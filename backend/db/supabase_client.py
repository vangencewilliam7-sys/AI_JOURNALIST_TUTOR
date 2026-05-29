"""
Supabase client singleton + LLM / Embeddings initialization.
"""

from supabase import create_client, Client
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from config import (
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_FAST_MODEL,
    EMBEDDING_MODEL,
)

# ---------------------------------------------------------------------------
# Supabase
# ---------------------------------------------------------------------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ---------------------------------------------------------------------------
# LLM clients
# ---------------------------------------------------------------------------
llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
llm_fast = ChatOpenAI(model=LLM_FAST_MODEL, temperature=0.0, max_tokens=30)
embeddings_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)
