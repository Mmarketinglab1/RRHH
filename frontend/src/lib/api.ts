export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://rrhh-api-udcvzoylva-uc.a.run.app";

export type Evaluation = {
  id: string;
  title: string;
  description: string | null;
  status: string;
  assessment_type?: string | null;
  starts_at: string | null;
  ends_at: string | null;
  created_at: string;
};

export type CompetencyBank = {
  id: string;
  name: string;
  description: string | null;
  company_id: string | null;
  created_at: string;
};

export type Competency = {
  id: string;
  evaluation_id: string;
  competency_bank_id: string | null;
  name: string;
  description: string | null;
  weight: string;
};

export type Question = {
  id: string;
  evaluation_id: string;
  competency_id: string;
  text: string;
  text_self?: string;
  text_evaluator?: string;
  tag_self?: string;
  tag_evaluator?: string;
  position: number;
  question_type: string;
  options: any;
  is_evaluative: boolean;
};

export type Participant = {
  id: string;
  email: string;
  full_name: string;
  role: string | null;
};

export type Assignment = {
  id: string;
  evaluation_id: string;
  evaluatee_id: string;
  evaluator_id: string;
  relationship: string;
  weight: string;
  is_completed?: boolean;
  survey_token?: string | null;
};

export type QuestionResult = {
  question_id: string;
  question_text: string;
  question_text_self?: string;
  question_text_evaluator?: string;
  tag_self?: string;
  tag_evaluator?: string;
  question_type: string;
  is_evaluative: boolean;
  competency_name: string;
  average: number | null;
  median: number | null;
  stddev: number | null;
  responses_count: number;
  distribution: Record<string, number>;
};

export type OutlierAlert = {
  evaluator_id: string;
  evaluator_name: string;
  evaluatee_id: string;
  evaluatee_name: string;
  evaluator_average: number;
  others_average: number;
  diff: number;
  alert_type: "high_outlier" | "low_outlier";
  message: string;
};

export type CompetencyScoreByRelation = {
  competency_id: string;
  competency_name: string;
  self_score: number | null;
  evaluators_score: number | null;
  by_relationship: Record<string, number>;
  gap: number | null;
};

export type QuestionDetailForParticipant = {
  question_id: string;
  question_text: string;
  competency_name: string;
  question_type: string;
  is_evaluative: boolean;
  self_score: number | null;
  evaluators_score: number | null;
  comments: Array<{
    relationship: string;
    evaluator_name: string;
    comment: string;
  }>;
};

export type ParticipantDetailResults = {
  participant_id: string;
  participant_name: string;
  participant_email: string;
  participant_role: string | null;
  overall_evaluators_score: number | null;
  overall_self_score: number | null;
  overall_gap: number | null;
  competencies: Array<CompetencyScoreByRelation>;
  questions: Array<QuestionDetailForParticipant>;
  top_strengths: Array<string>;
  opportunities: Array<string>;
};

export type EvaluationResults = {
  evaluation_id: string;
  average: number;
  median: number;
  stddev: number;
  competencies: Array<{
    competency_id: string;
    competency_name: string;
    average: number;
    weighted_average: number;
    median: number;
    stddev: number;
    responses: number;
  }>;
  ranking: Array<{
    participant_id: string;
    participant_name: string;
    average: number;
    rank: number;
  }>;
  questions: Array<QuestionResult>;
  outliers?: Array<OutlierAlert>;
};

export type ExecutiveParticipantMatrixRow = {
  participant_id: string;
  participant_name: string;
  role: string | null;
  business_line: string | null;
  performance_history: Record<string, string>;
  net_scores: Record<string, number>;
  net_average: number;
  weighted_scores: Record<string, number>;
  weighted_total: number;
  rank_net: number;
  rank_weighted: number;
};

export type ExecutiveReportResults = {
  evaluation_id: string;
  evaluation_title: string;
  company_name: string;
  client_logo_url: string | null;
  consultant_logo_url: string | null;
  scale_type: string;
  total_evaluados: number;
  net_overall: { average?: number; median?: number; stddev?: number };
  weighted_overall: { average?: number; median?: number; stddev?: number };
  thresholds: { high: number; medium: number };
  competencies: Array<{
    competency_id: string;
    competency_name: string;
    weight: number;
    weight_pct: number;
    net_average: number;
    net_median: number;
    net_stddev: number;
    weighted_average: number;
    weighted_median: number;
    weighted_stddev: number;
    responses_count: number;
    items: Array<{
      question_id: string;
      question_text: string;
      competency_id: string;
      competency_name: string;
      average: number;
      position: number;
    }>;
  }>;
  participants_matrix: Array<ExecutiveParticipantMatrixRow>;
  business_lines: Array<{
    line_name: string;
    count: number;
    net_average: number;
    net_median: number;
    net_stddev: number;
    weighted_average: number;
  }>;
  insights: {
    strongest_competency: string;
    weakest_competency: string;
    highest_dispersion_competency: string;
    lowest_dispersion_competency: string;
    summary_bullets: Array<string>;
    reactivos_bullets: Array<string>;
  };
};

export type PublicSurvey = {
  evaluation_title: string;
  evaluatee_name: string;
  evaluator_name: string;
  relationship: string;
  questions: Array<{
    id: string;
    text: string;
    text_self?: string;
    text_evaluator?: string;
    tag_self?: string;
    tag_evaluator?: string;
    competency: string;
    question_type: string;
    options: any;
    is_evaluative: boolean;
  }>;
};

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = await response.json();
      message = body.detail || message;
    } catch {
      // Keep response status text.
    }
    if (response.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("rrhh_token");
      window.dispatchEvent(new Event("rrhh_auth_invalid"));
    }
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function downloadFile(
  path: string,
  defaultFilename: string,
  token?: string | null,
): Promise<void> {
  const headers = new Headers();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = await response.json();
      message = body.detail || message;
    } catch {}
    throw new ApiError(response.status, message);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  
  // Parse filename from Content-Disposition if present
  const disposition = response.headers.get("content-disposition");
  let filename = defaultFilename;
  if (disposition && disposition.includes("filename=")) {
    const matches = /filename="?([^"]+)"?/.exec(disposition);
    if (matches && matches[1]) {
      filename = matches[1];
    }
  }

  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

