-- ============================================================
-- AI JOURNALIST TUTOR — PRODUCTION DATABASE SCHEMA
-- ============================================================
-- Run this in: Supabase Dashboard > SQL Editor > New Query
-- 
-- This migration:
--   CREATES 6 new tables (tutors, courses, course_modules, 
--           course_topics, tacit_insights, tutor_personas)
--   ALTERS 3 existing tables (interview_scripts, 
--           conversation_sessions, conversation_messages)
--   KEEPS 2 tables unchanged (knowledge_sources, knowledge_chunks)
-- ============================================================


-- ============================================================
-- 1. TUTORS — The expert being interviewed
-- ============================================================
-- Previously: tutor identity was buried inside 
-- interview_scripts.tutor_profile (JSONB blob)
-- Now: proper table, reusable across multiple courses

CREATE TABLE IF NOT EXISTS tutors (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT,
    expertise_streams TEXT[] DEFAULT '{}',
    years_of_experience INTEGER DEFAULT 0,
    short_bio TEXT,
    linkedin_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tutors_name ON tutors(full_name);


-- ============================================================
-- 2. COURSES — The course being built from the interview
-- ============================================================
-- One tutor can create multiple courses
-- Each interview session builds exactly ONE course

CREATE TABLE IF NOT EXISTS courses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tutor_id UUID NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    subtitle TEXT,
    description TEXT,
    target_audience TEXT,
    estimated_duration TEXT,
    transformation_promise TEXT,
    status TEXT DEFAULT 'draft' 
        CHECK (status IN ('draft', 'interviewing', 'completed')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_courses_tutor ON courses(tutor_id);
CREATE INDEX IF NOT EXISTS idx_courses_status ON courses(status);


-- ============================================================
-- 3. COURSE_MODULES — Each module = one row
-- ============================================================
-- Previously: modules only existed inside synthesis JSONB output
-- Now: created DURING the interview as the expert lists them
-- drill_status tracks whether we've drilled into this module

CREATE TABLE IF NOT EXISTS course_modules (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    module_index INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    learning_outcomes TEXT[] DEFAULT '{}',
    drill_status TEXT DEFAULT 'not_started' 
        CHECK (drill_status IN ('not_started', 'in_progress', 'done')),
    created_at TIMESTAMPTZ DEFAULT now(),

    -- Prevent duplicate module indexes within same course
    UNIQUE (course_id, module_index)
);

CREATE INDEX IF NOT EXISTS idx_modules_course ON course_modules(course_id);


-- ============================================================
-- 4. COURSE_TOPICS — Each topic inside a module = one row
-- ============================================================
-- Created DURING the interview as the expert describes 
-- what each module contains

CREATE TABLE IF NOT EXISTS course_topics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    module_id UUID NOT NULL REFERENCES course_modules(id) ON DELETE CASCADE,
    topic_index INTEGER NOT NULL,
    title TEXT NOT NULL,
    key_concepts TEXT[] DEFAULT '{}',
    suggested_format TEXT DEFAULT 'video_lecture' 
        CHECK (suggested_format IN (
            'video_lecture', 'hands_on', 'case_study', 
            'quiz', 'project', 'discussion', 'workshop'
        )),
    tutor_insight TEXT,
    is_inferred BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),

    -- Prevent duplicate topic indexes within same module
    UNIQUE (module_id, topic_index)
);

CREATE INDEX IF NOT EXISTS idx_topics_module ON course_topics(module_id);


-- ============================================================
-- 5. TACIT_INSIGHTS — Each insight = one searchable row
-- ============================================================
-- Previously: all insights dumped as JSONB arrays inside
-- tacit_knowledge_reports (tacit_insights, mental_models, 
-- pattern_breaks, war_stories columns)
-- Now: each insight is its own row, filterable by type/theme

CREATE TABLE IF NOT EXISTS tacit_insights (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    theme TEXT NOT NULL,
    note_title TEXT NOT NULL,
    content TEXT NOT NULL,
    expert_quote TEXT,
    insight_type TEXT DEFAULT 'technique' 
        CHECK (insight_type IN (
            'mental_model', 'anti_pattern', 'war_story', 
            'technique', 'philosophy'
        )),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_insights_course ON tacit_insights(course_id);
CREATE INDEX IF NOT EXISTS idx_insights_type ON tacit_insights(insight_type);


-- ============================================================
-- 6. TUTOR_PERSONAS — The generated AI system prompt
-- ============================================================
-- Slim table: just the system_prompt that's actually used
-- No extra columns we don't need (as discussed)

CREATE TABLE IF NOT EXISTS tutor_personas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tutor_id UUID NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    system_prompt TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_personas_tutor ON tutor_personas(tutor_id);
CREATE INDEX IF NOT EXISTS idx_personas_course ON tutor_personas(course_id);


-- ============================================================
-- 7. ALTER EXISTING TABLES — Add new columns
-- ============================================================

-- 7a. interview_scripts: add course link + drill-down state
ALTER TABLE interview_scripts
ADD COLUMN IF NOT EXISTS course_id UUID REFERENCES courses(id) ON DELETE SET NULL;

ALTER TABLE interview_scripts
ADD COLUMN IF NOT EXISTS drilled_modules JSONB DEFAULT '{}'::jsonb;

ALTER TABLE interview_scripts
ADD COLUMN IF NOT EXISTS tangent_turns_used INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_scripts_course ON interview_scripts(course_id);


-- 7b. conversation_sessions: add course link
ALTER TABLE conversation_sessions
ADD COLUMN IF NOT EXISTS course_id UUID REFERENCES courses(id) ON DELETE SET NULL;


-- 7c. conversation_messages: add decision metadata
ALTER TABLE conversation_messages
ADD COLUMN IF NOT EXISTS decision_metadata JSONB DEFAULT '{}'::jsonb;


-- ============================================================
-- 8. ROW LEVEL SECURITY (RLS)
-- ============================================================
-- Enable RLS on all new tables
-- Using permissive policies for development
-- TODO: tighten these with auth.uid() checks for production

ALTER TABLE tutors ENABLE ROW LEVEL SECURITY;
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE course_modules ENABLE ROW LEVEL SECURITY;
ALTER TABLE course_topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE tacit_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutor_personas ENABLE ROW LEVEL SECURITY;

-- Dev policies — allow everything (replace with proper auth later)
DO $$
BEGIN
    -- tutors
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'dev_all_tutors') THEN
        CREATE POLICY "dev_all_tutors" ON tutors FOR ALL USING (true) WITH CHECK (true);
    END IF;
    -- courses
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'dev_all_courses') THEN
        CREATE POLICY "dev_all_courses" ON courses FOR ALL USING (true) WITH CHECK (true);
    END IF;
    -- course_modules
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'dev_all_modules') THEN
        CREATE POLICY "dev_all_modules" ON course_modules FOR ALL USING (true) WITH CHECK (true);
    END IF;
    -- course_topics
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'dev_all_topics') THEN
        CREATE POLICY "dev_all_topics" ON course_topics FOR ALL USING (true) WITH CHECK (true);
    END IF;
    -- tacit_insights
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'dev_all_insights') THEN
        CREATE POLICY "dev_all_insights" ON tacit_insights FOR ALL USING (true) WITH CHECK (true);
    END IF;
    -- tutor_personas
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'dev_all_personas') THEN
        CREATE POLICY "dev_all_personas" ON tutor_personas FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;


-- ============================================================
-- 9. VERIFICATION — Check everything was created
-- ============================================================

SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns c 
        WHERE c.table_name = t.table_name 
        AND c.table_schema = 'public') as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_name IN (
    'tutors', 'courses', 'course_modules', 'course_topics',
    'tacit_insights', 'tutor_personas', 'interview_scripts',
    'conversation_sessions', 'conversation_messages',
    'knowledge_sources', 'knowledge_chunks'
)
ORDER BY table_name;
