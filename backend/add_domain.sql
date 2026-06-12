-- Migration: Add domain to conversation_sessions
ALTER TABLE conversation_sessions ADD COLUMN IF NOT EXISTS domain TEXT DEFAULT 'Tutor';
