import type {
  CreateInterviewInput,
  InterviewDetail,
  InterviewSummary,
  Meta,
  Session,
} from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code: string,
    public retryable: boolean,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api${path}`, {
      ...init,
      headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers },
      cache: "no-store",
    });
  } catch {
    throw new ApiError("Can't reach the interview server. Check that the backend is running.", 0, "network", true);
  }

  if (res.ok) return res.json() as Promise<T>;

  let body: { error?: { message?: string; code?: string; retryable?: boolean } } = {};
  try {
    body = await res.json();
  } catch {
    // Proxy/gateway errors come back as HTML; fall through to a generic message.
  }
  const unreachable = res.status === 500 && !body.error;
  throw new ApiError(
    body.error?.message ??
      (unreachable
        ? "Can't reach the interview server. Check that the backend is running."
        : "Something went wrong. Please try again."),
    res.status,
    body.error?.code ?? "unknown",
    body.error?.retryable ?? res.status >= 500,
  );
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  meta: () => request<Meta>("/meta"),
  listInterviews: () => request<{ interviews: InterviewSummary[] }>("/interviews").then((r) => r.interviews),
  getInterview: (id: string) => request<InterviewDetail>(`/interviews/${id}`),
  createInterview: (input: CreateInterviewInput) => post<InterviewDetail>("/interviews", input),
  createDemo: () => post<InterviewDetail>("/interviews/demo"),

  session: (id: string) => request<Session>(`/interviews/${id}/session`),
  start: (id: string) => post<Session>(`/interviews/${id}/start`),
  prepareQuestion: (id: string) => post<Session>(`/interviews/${id}/question`),
  answer: (id: string, question_index: number, answer: string) =>
    post<Session>(`/interviews/${id}/answer`, { question_index, answer }),
  skip: (id: string, question_index: number) => post<Session>(`/interviews/${id}/skip`, { question_index }),
  finish: (id: string) => post<Session>(`/interviews/${id}/finish`),

  parseResume: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ filename: string; text: string; truncated: boolean }>("/resume", { method: "POST", body: form });
  },
};

export function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
}
