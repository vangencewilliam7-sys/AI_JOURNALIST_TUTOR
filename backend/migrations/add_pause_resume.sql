-- Add snapshot column for pause/resume state
ALTER TABLE interview_sessions
ADD COLUMN IF NOT EXISTS snapshot JSONB DEFAULT '{}'::jsonb;
