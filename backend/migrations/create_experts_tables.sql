-- create_experts_tables.sql

-- 1. Create the experts table
CREATE TABLE IF NOT EXISTS experts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT,
    stream_type TEXT,
    course_title TEXT,
    course_description TEXT,
    target_audience TEXT,
    expertise_streams TEXT,
    years_of_experience INTEGER,
    short_bio TEXT,
    linkedin_url TEXT,
    archetype TEXT DEFAULT 'balanced',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create the expert_profile table (used for synthesized knowledge)
CREATE TABLE IF NOT EXISTS expert_profile (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
    persona_traits JSONB DEFAULT '[]'::jsonb,
    war_stories JSONB DEFAULT '[]'::jsonb,
    mental_models JSONB DEFAULT '[]'::jsonb,
    edge_cases JSONB DEFAULT '[]'::jsonb,
    pattern_breaks JSONB DEFAULT '[]'::jsonb,
    tacit_insights JSONB DEFAULT '[]'::jsonb,
    teaching_style TEXT,
    linguistic_fingerprint JSONB DEFAULT '{}'::jsonb,
    system_prompt TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
