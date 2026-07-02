-- ==============================================================================
-- Supabase Migration Audit & Readiness Remediation Script
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. Cleanup Phase (Removing the Junk)
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS public.conversation_messages CASCADE;
DROP TABLE IF EXISTS public.conversation_sessions CASCADE;
DROP TABLE IF EXISTS public.interview_scripts CASCADE;


-- ------------------------------------------------------------------------------
-- 2. Integrity Phase (Fixing Constraints & Table Creation)
-- ------------------------------------------------------------------------------

-- Add foreign key constraint to homework_ledger
ALTER TABLE public.homework_ledger
ADD CONSTRAINT fk_homework_ledger_expert
FOREIGN KEY (expert_id) REFERENCES public.experts(id) ON DELETE CASCADE;

-- Link experts table directly to Supabase auth.users for proper cascade deletion
ALTER TABLE public.experts
ADD CONSTRAINT fk_experts_auth
FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- Create submitted_materials table with correct types (resolving type mismatch)
CREATE TABLE IF NOT EXISTS public.submitted_materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id UUID REFERENCES public.experts(id) ON DELETE CASCADE,
    session_id UUID REFERENCES public.interview_sessions(id) ON DELETE CASCADE,
    iteration_number INT DEFAULT 1,
    loop_topic TEXT NOT NULL,
    material_type TEXT NOT NULL CHECK (material_type IN ('file', 'url', 'text')),
    content_or_url TEXT NOT NULL,
    verification_status TEXT DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'rejected')),
    verification_insights JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Note: knowledge_items was created in the previous step.
-- If not, ensure it exists:
CREATE TABLE IF NOT EXISTS public.knowledge_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    expert_id UUID REFERENCES experts(id) ON DELETE CASCADE,
    knowledge_type TEXT NOT NULL,
    topic TEXT,
    title TEXT,
    raw_quote TEXT NOT NULL, 
    clean_insight TEXT,
    signal TEXT,
    interpretation TEXT,
    expert_action TEXT,
    decision_rule TEXT,
    workflow_step JSONB DEFAULT '{}'::jsonb,
    source_or_origin TEXT,
    confidence TEXT DEFAULT 'medium',
    validation_status TEXT DEFAULT 'unvalidated',
    missing_fields TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);


-- ------------------------------------------------------------------------------
-- 3. Security Phase (Enforcing RLS & Applying Policies)
-- ------------------------------------------------------------------------------

-- Enable RLS database-wide
ALTER TABLE public.experts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.expert_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.homework_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.curriculum_blueprints ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.expert_tacit_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.topic_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tacit_knowledge_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.submitted_materials ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_items ENABLE ROW LEVEL SECURITY;

-- Apply expert policies (Users can only access their own data)
CREATE POLICY "Users can manage own homework" ON public.homework_ledger
    FOR ALL USING (auth.uid() = expert_id) WITH CHECK (auth.uid() = expert_id);

CREATE POLICY "Users can manage own insights" ON public.expert_tacit_insights
    FOR ALL USING (auth.uid() = expert_id) WITH CHECK (auth.uid() = expert_id);

CREATE POLICY "Users can manage own progress" ON public.topic_progress
    FOR ALL USING (auth.uid() = expert_id) WITH CHECK (auth.uid() = expert_id);

CREATE POLICY "Users can view own blueprints" ON public.curriculum_blueprints
    FOR SELECT USING (auth.uid() = expert_id);

CREATE POLICY "Users can view own profiles" ON public.expert_profile
    FOR SELECT USING (auth.uid() = expert_id);

CREATE POLICY "Users can view own reports" ON public.tacit_knowledge_reports
    FOR SELECT USING (auth.uid() = expert_id);

CREATE POLICY "Users can manage own submitted materials" ON public.submitted_materials
    FOR ALL USING (auth.uid() = expert_id) WITH CHECK (auth.uid() = expert_id);
    
CREATE POLICY "Users can manage own knowledge items" ON public.knowledge_items
    FOR ALL USING (auth.uid() = expert_id) WITH CHECK (auth.uid() = expert_id);


-- ------------------------------------------------------------------------------
-- 4. Performance Phase (Indexing)
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_sessions_expert ON public.interview_sessions(expert_id);
CREATE INDEX IF NOT EXISTS idx_blueprints_session ON public.curriculum_blueprints(session_id);
CREATE INDEX IF NOT EXISTS idx_insights_session ON public.expert_tacit_insights(session_id);
CREATE INDEX IF NOT EXISTS idx_progress_session ON public.topic_progress(session_id);
CREATE INDEX IF NOT EXISTS idx_chunks_source ON public.knowledge_chunks(source_id);
