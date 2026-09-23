export type Level = "L1" | "L2" | "L3";
export type InterviewStatus = "created" | "in_progress" | "completed";

export interface EngineInfo {
  provider: string;
  model: string;
  embeddings: string | null;
  vector_store: string | null;
}

export interface InterviewSummary {
  id: string;
  created_at: string;
  updated_at: string;
  status: InterviewStatus;
  is_sample: boolean;
  candidate_name: string;
  role: string;
  num_questions: number;
  focus_areas: string[];
  overall: number | null;
}

export interface CurrentQuestion {
  index: number;
  number: number;
  text: string;
  topic: string;
  domain: string;
  difficulty: Level;
}

export interface Session {
  id: string;
  status: InterviewStatus;
  is_sample: boolean;
  candidate_name: string;
  role: string;
  num_questions: number;
  answered: number;
  started_at: string | null;
  engine: EngineInfo | null;
  current_question: CurrentQuestion | null;
  question_error: { message: string; code: string } | null;
}

export interface Evaluation {
  score: number;
  communication_score: number;
  verdict: "weak" | "average" | "strong";
  core_coverage: string[];
  advanced_coverage: string[];
  missed_core_signals: string[];
  misconceptions_detected: string[];
  ungrounded_removed: string[];
  score_capped_from: number | null;
}

export interface Turn {
  index: number;
  number: number;
  topic: string;
  domain: string;
  difficulty: Level;
  target_difficulty: Level | null;
  question: string;
  answer: string | null;
  skipped: boolean;
  answered: boolean;
  retrieval_mode: "semantic" | "catalog" | null;
  retrieval_note: string | null;
  evaluation: Evaluation | null;
}

export interface Report {
  overall: number | null;
  band: string;
  dimensions: {
    technical_knowledge: number | null;
    conceptual_depth: number | null;
    communication: number | null;
  };
  strengths: { title: string; detail: string }[];
  improvements: { title: string; detail: string }[];
  misconceptions: string[];
  coverage: { domain: string; label: string; score: number; questions: number }[];
  difficulty_progression: Level[];
  peak_difficulty: Level | null;
  questions_answered: number;
  questions_skipped: number;
  questions_planned: number;
  grounding: {
    ungrounded_claims_removed: number;
    scores_capped: number;
    semantic_retrievals: number;
    catalog_fallbacks: number;
  };
}

export interface InterviewDetail {
  id: string;
  status: InterviewStatus;
  is_sample: boolean;
  created_at: string;
  updated_at: string;
  candidate_name: string;
  role: string;
  config: {
    interview_type: string;
    difficulty_mode: "adaptive" | "fixed";
    start_difficulty: Level;
    num_questions: number;
    focus_areas: { id: string; label: string }[];
    has_job_description: boolean;
    resume_filename: string | null;
  };
  started_at: string | null;
  finished_at: string | null;
  engine: EngineInfo | null;
  turns: Turn[];
  report: Report | null;
}

export interface FocusArea {
  id: string;
  label: string;
  concepts: Record<Level, number>;
}

export interface Meta {
  focus_areas: FocusArea[];
  total_concepts: number;
  engine: EngineInfo;
}

export interface CreateInterviewInput {
  candidate_name: string;
  role: string;
  difficulty_mode: "adaptive" | "fixed";
  start_difficulty: Level;
  num_questions: number;
  focus_areas: string[];
  job_description: string;
  resume_text: string;
  resume_filename: string | null;
}
