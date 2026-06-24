-- 1. Add missing columns to expert_profile
ALTER TABLE expert_profile
  ADD COLUMN IF NOT EXISTS teaching_style TEXT,
  ADD COLUMN IF NOT EXISTS linguistic_fingerprint JSONB DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS structured_tacit_notes JSONB DEFAULT '[]'::jsonb;

-- 2. Add missing columns to curriculum_blueprints  
ALTER TABLE curriculum_blueprints
  ADD COLUMN IF NOT EXISTS report_title TEXT,
  ADD COLUMN IF NOT EXISTS course_title TEXT,
  ADD COLUMN IF NOT EXISTS structured_tacit_notes JSONB DEFAULT '[]'::jsonb;

-- 3. Create tacit_knowledge_reports since it doesn't exist
CREATE TABLE IF NOT EXISTS tacit_knowledge_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
  session_id_fk UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
  report_title TEXT,
  structured_tacit_notes JSONB DEFAULT '[]'::jsonb,
  persona_snapshot JSONB DEFAULT '{}'::jsonb,
  course_structure JSONB DEFAULT '{}'::jsonb
);

-- 4. Enable RLS on tables missing it
ALTER TABLE curriculum_blueprints ENABLE ROW LEVEL SECURITY;
ALTER TABLE expert_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE tacit_knowledge_reports ENABLE ROW LEVEL SECURITY;
