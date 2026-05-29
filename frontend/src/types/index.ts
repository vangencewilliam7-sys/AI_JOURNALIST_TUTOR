// Common interfaces and types used across the application

export interface User {
  id: string;
  email?: string;
}

export interface DecisionLog {
  action?: string;
  internal_monologue?: string;
  scripted_question_resolved?: boolean;
  follow_up_reason?: string;
  next_action?: string;
}

export interface RagChunk {
  source_title: string;
  content: string;
  similarity: number;
}

export interface Message {
  id: string;
  role: 'ai' | 'expert' | 'system';
  text: string;
  decision?: DecisionLog;
  chunks?: RagChunk[];
}

export interface ScriptQuestion {
  question_id: string;
  question_text: string;
  theme_id: number;
  estimated_minutes: number;
}

export interface ScriptPhase {
  phase_goal: string;
  questions: ScriptQuestion[];
}

export interface InterviewArc {
  phase_1_genesis_audience: ScriptPhase;
  phase_2_module_breakdown: ScriptPhase;
  phase_3_deep_dives: ScriptPhase;
}

export interface InterviewScript {
  interview_arc: InterviewArc;
  metadata?: any;
}

export interface KnowledgeSource {
  id: string;
  title: string;
  source_type: string;
  chunk_count: number;
  created_at: string;
}

export interface CourseModule {
  module_number: number;
  module_title: string;
  description: string;
  lessons: Array<{
    lesson_title: string;
    details: string;
  }>;
  assignments_or_exercises: string[];
}

export interface CourseBlueprint {
  course_title: string;
  target_audience: string;
  tutor_name: string;
  tutor_motivation?: string;
  north_star_outcome?: string;
  learning_format?: string;
  summary: string;
  total_modules: number;
  course_modules: CourseModule[];
  learning_outcomes: string[];
  friction_points: Array<{
    concept: string;
    friction_detail: string;
    unblock_strategy: string;
  }>;
  teaching_frameworks: Array<{
    topic: string;
    framework_name: string;
    explanation: string;
  }>;
  edge_cases: Array<{
    scenario: string;
    solution: string;
  }>;
  anti_patterns: Array<{
    bad_habit: string;
    correction: string;
  }>;
  evaluation_methods: Array<{
    concept: string;
    assessment_task: string;
  }>;
  marketing_hooks: Array<{
    hook: string;
    why_it_works: string;
  }>;
}
