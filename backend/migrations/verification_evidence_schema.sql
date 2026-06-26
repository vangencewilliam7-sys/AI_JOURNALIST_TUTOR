-- Migration: Create submitted_materials table for Homework Evidence Cross-Referencing Engine
CREATE TABLE IF NOT EXISTS public.submitted_materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id TEXT REFERENCES public.experts(id) ON DELETE CASCADE,
    session_id UUID REFERENCES public.interview_sessions(id) ON DELETE CASCADE,
    iteration_number INT DEFAULT 1,
    loop_topic TEXT NOT NULL,
    material_type TEXT NOT NULL CHECK (material_type IN ('file', 'url', 'text_description', 'book_reference')),
    content_or_url TEXT NOT NULL,
    verification_status TEXT DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verifying', 'verified', 'inconsistent', 'needs_review')),
    verification_insights JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.submitted_materials ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage own submitted materials" ON public.submitted_materials;
CREATE POLICY "Users can manage own submitted materials" ON public.submitted_materials
    FOR ALL USING (auth.uid() = expert_id) WITH CHECK (auth.uid() = expert_id);
