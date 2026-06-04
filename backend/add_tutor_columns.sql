-- Run this in your Supabase SQL Editor
-- Navigate to: Supabase Dashboard > SQL Editor > New Query

-- Add tutor_profile to interview_scripts
ALTER TABLE interview_scripts 
ADD COLUMN IF NOT EXISTS tutor_profile JSONB DEFAULT '{}'::jsonb;

-- Add new synthesis columns to tacit_knowledge_reports
ALTER TABLE tacit_knowledge_reports 
ADD COLUMN IF NOT EXISTS tutor_persona JSONB DEFAULT '{}'::jsonb;

ALTER TABLE tacit_knowledge_reports 
ADD COLUMN IF NOT EXISTS course_structure JSONB DEFAULT '{}'::jsonb;

ALTER TABLE tacit_knowledge_reports 
ADD COLUMN IF NOT EXISTS teaching_philosophy JSONB DEFAULT '{}'::jsonb;

ALTER TABLE tacit_knowledge_reports 
ADD COLUMN IF NOT EXISTS personal_journey JSONB DEFAULT '{}'::jsonb;
