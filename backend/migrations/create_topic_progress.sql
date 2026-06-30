-- CREATE topic_progress table for deterministic topic and component progress tracking
CREATE TABLE IF NOT EXISTS topic_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
    module_id TEXT NOT NULL,
    module_title TEXT,
    topic_id TEXT NOT NULL,
    topic_title TEXT,
    components JSONB DEFAULT '{}'::jsonb,
    is_complete BOOLEAN DEFAULT false,
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (session_id, topic_id)
);

-- Enable RLS
ALTER TABLE topic_progress ENABLE ROW LEVEL SECURITY;

-- Dev policy - allow everything for local development
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'dev_all_topic_progress') THEN
        CREATE POLICY "dev_all_topic_progress" ON topic_progress FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;
