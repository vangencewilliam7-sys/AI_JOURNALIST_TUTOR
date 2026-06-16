-- update_interview_sessions.sql

-- Add missing columns to interview_sessions
ALTER TABLE interview_sessions
ADD COLUMN IF NOT EXISTS expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS iteration_number INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active',
ADD COLUMN IF NOT EXISTS script JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS raw_transcript TEXT DEFAULT '',
ADD COLUMN IF NOT EXISTS session_synthesis JSONB DEFAULT '{}'::jsonb;
