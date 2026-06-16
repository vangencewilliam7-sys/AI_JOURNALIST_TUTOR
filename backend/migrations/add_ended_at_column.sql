-- add_ended_at_column.sql
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS ended_at TIMESTAMP WITH TIME ZONE;
