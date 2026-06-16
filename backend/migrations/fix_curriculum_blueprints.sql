-- fix_curriculum_blueprints.sql

ALTER TABLE curriculum_blueprints
ADD COLUMN IF NOT EXISTS expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS course_modules JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS iteration_last_updated INTEGER DEFAULT 1;

ALTER TABLE curriculum_blueprints ALTER COLUMN session_id DROP NOT NULL;
