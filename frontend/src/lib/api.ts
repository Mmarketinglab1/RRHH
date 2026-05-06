export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://rrhh-api-udcvzoylva-uc.a.run.app";

export type Evaluation = {
  id: string;
  title: string;
  description: string | null;
  status: string;
  starts_at: string | null;
  ends_at: string | null;
  created_at: string;
};

export type Competency = {
  id: string;
  evaluation_id: string;
  name: string;
  description: string | null;
  weight: string;
};

export type Question = {
  id: string;
  evaluation_id: string;
  competency_id: string;
  text: string;
  position: number;
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
};

export type PublicSurvey = {
  evaluation_title: string;
  evaluatee_name: string;
  evaluator_name: string;
  questions: Array<{ id: string; text: string; competency: string }>;
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
