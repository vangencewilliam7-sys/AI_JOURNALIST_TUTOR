-- add_hybrid_memory.sql
-- Run this in Supabase SQL Editor to set up the 6-Layer Memory Architecture

-- 1. UPDATE INTERVIEW SESSIONS TABLE (For the Working Memory / Scratchpad)
ALTER TABLE interview_sessions
ADD COLUMN IF NOT EXISTS live_scratchpad JSONB DEFAULT '{
    "current_topic": "",
    "topics_covered": [],
    "interesting_threads": [],
    "open_questions": [],
    "expert_profile": {}
}'::jsonb,
ADD COLUMN IF NOT EXISTS scratchpad_turns_processed INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS live_transcript_source_id UUID REFERENCES knowledge_sources(id) ON DELETE SET NULL;



