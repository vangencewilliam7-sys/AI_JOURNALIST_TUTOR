ALTER TABLE knowledge_sources 
ADD COLUMN IF NOT EXISTS author_or_channel TEXT,
ADD COLUMN IF NOT EXISTS global_summary TEXT;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS live_transcript_source_id UUID REFERENCES knowledge_sources(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS live_scratchpad JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS current_block TEXT DEFAULT 'Block 1',
ADD COLUMN IF NOT EXISTS ended_at TIMESTAMPTZ;
