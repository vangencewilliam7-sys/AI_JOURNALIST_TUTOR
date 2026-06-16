-- ============================================================
-- MIGRATION: Add homework_ledger + update schema for production prompts
-- ============================================================
-- Run this in: Supabase Dashboard > SQL Editor > New Query
--
-- This migration:
--   CREATES 1 new table (homework_ledger)
--   ALTERS 1 existing table (tacit_knowledge_reports — rename column)
-- ============================================================


-- ============================================================
-- 1. HOMEWORK_LEDGER — Stores open loops + human research notes
-- ============================================================
-- Written to by the HOMEWORK_GENERATOR_PROMPT (Phase 5)
-- Read by the FLYWHEEL_BRIDGE_PROMPT (Phase 6)
-- The human_manual_notes column is filled by the host on the
-- Homework Dashboard (Screen 5) BEFORE Day 2 can begin.

CREATE TABLE IF NOT EXISTS homework_ledger (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id UUID NOT NULL,
    session_id TEXT REFERENCES conversation_sessions(session_id) ON DELETE CASCADE,
    iteration_number INTEGER DEFAULT 1,
    
    -- AI-generated open loops (from HOMEWORK_GENERATOR_PROMPT)
    ai_open_loops JSONB DEFAULT '[]'::jsonb,
    
    -- Human-written overnight research notes (filled on Homework Dashboard)
    human_manual_notes TEXT DEFAULT '',
    
    -- Whether the host has validated/committed their homework
    -- Progress is LOCKED until this is true (human-in-the-loop gatekeeper)
    is_validated BOOLEAN DEFAULT false,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_homework_expert ON homework_ledger(expert_id);
CREATE INDEX IF NOT EXISTS idx_homework_session ON homework_ledger(session_id);

-- Enable RLS
ALTER TABLE homework_ledger ENABLE ROW LEVEL SECURITY;

-- Dev policy — allow everything (replace with proper auth later)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'dev_all_homework') THEN
        CREATE POLICY "dev_all_homework" ON homework_ledger FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;


-- ============================================================
-- 2. RENAME knowledge_gaps → weak_coverage_areas in tacit_knowledge_reports
-- ============================================================
-- This aligns with the updated GENERAL_SYNTHESIS_PROMPT which now
-- outputs "weak_coverage_areas" instead of "knowledge_gaps" to avoid
-- confusion with the separate "ai_open_loops" in homework_ledger.
-- 
-- NOTE: Since knowledge_gaps is a JSONB column, the rename is safe.
-- Existing data structure remains identical.

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tacit_knowledge_reports' 
        AND column_name = 'knowledge_gaps'
    ) THEN
        ALTER TABLE tacit_knowledge_reports 
        RENAME COLUMN knowledge_gaps TO weak_coverage_areas;
    END IF;
END $$;


-- ============================================================
-- 3. VERIFICATION — Check homework_ledger was created
-- ============================================================

SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns c 
        WHERE c.table_name = t.table_name 
        AND c.table_schema = 'public') as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_name IN ('homework_ledger', 'tacit_knowledge_reports')
ORDER BY table_name;
