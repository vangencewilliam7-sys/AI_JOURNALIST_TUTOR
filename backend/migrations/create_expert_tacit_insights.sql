-- Migration: Create expert_tacit_insights table for the verification dashboard
CREATE TABLE IF NOT EXISTS public.expert_tacit_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id UUID REFERENCES public.experts(id) ON DELETE CASCADE,
    session_id UUID REFERENCES public.interview_sessions(id) ON DELETE CASCADE,
    classification TEXT NOT NULL CHECK (
        classification IN (
            'mental_model', 'heuristic', 'decision_rule', 'failure_pattern', 
            'misconception', 'tradeoff', 'evaluation_signal', 'constraint', 
            'belief', 'turning_point', 'workflow', 'tool_or_technology'
        )
    ),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    expert_quote TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'modified', 'rejected')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.expert_tacit_insights ENABLE ROW LEVEL SECURITY;

-- Dev policy - allow everything for development
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'dev_all_expert_tacit_insights') THEN
        CREATE POLICY "dev_all_expert_tacit_insights" ON public.expert_tacit_insights FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;
