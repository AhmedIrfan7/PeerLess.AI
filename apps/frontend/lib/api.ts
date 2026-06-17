/**
 * Typed fetch wrapper. Reads NEXT_PUBLIC_BACKEND_URL from env.
 * Throws ApiError on non-2xx; surfaces network failures without crashing.
 */

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "") ||
  (() => {
    if (typeof window !== "undefined") {
      console.warn("[api] NEXT_PUBLIC_BACKEND_URL not set — falling back to http://localhost:8000");
    }
    return "http://localhost:8000";
  })();

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class NetworkError extends Error {
  constructor(cause?: unknown) {
    super("Could not reach the backend. Check your connection and try again.");
    this.name = "NetworkError";
    this.cause = cause;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BACKEND_URL}${path}`, {
      headers: { "Content-Type": "application/json", ...init?.headers },
      ...init,
    });
  } catch (err) {
    throw new NetworkError(err);
  }

  if (!response.ok) {
    let code = "unknown_error";
    let message = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      code = body?.error?.code ?? code;
      message = body?.error?.message ?? message;
    } catch {
      // ignore parse failure
    }
    throw new ApiError(response.status, code, message);
  }

  return response.json() as Promise<T>;
}

// ── Papers ────────────────────────────────────────────────────────────────────

export async function uploadPaper(
  file: File,
  opts?: { submitterEmail?: string; optInEmail?: boolean },
): Promise<{ paper_id: string; sha256: string; byte_size: number; duplicate: boolean }> {
  const form = new FormData();
  form.append("file", file);
  if (opts?.submitterEmail) form.append("submitter_email", opts.submitterEmail);
  if (opts?.optInEmail !== undefined) form.append("opt_in_email", String(opts.optInEmail));

  let response: Response;
  try {
    response = await fetch(`${BACKEND_URL}/api/v1/papers/`, { method: "POST", body: form });
  } catch (err) {
    throw new NetworkError(err);
  }

  if (!response.ok) {
    let code = "upload_error";
    let message = `Upload failed (HTTP ${response.status})`;
    try {
      const body = await response.json();
      code = body?.error?.code ?? code;
      message = body?.error?.message ?? message;
    } catch {
      // ignore
    }
    throw new ApiError(response.status, code, message);
  }

  return response.json();
}

export const getPaper = (id: string) =>
  request<PaperResponse>(`/api/v1/papers/${id}`);

export const reparsePaper = (id: string) =>
  request<PaperResponse>(`/api/v1/papers/${id}/reparse`, { method: "POST" });

export const analyzePaper = (id: string) =>
  request<{ report_id: string }>(`/api/v1/papers/${id}/analyze`, { method: "POST" });

// ── Reports ───────────────────────────────────────────────────────────────────

export const getReport = (id: string) =>
  request<ReportResponse>(`/api/v1/reports/${id}`);

// ── Findings ──────────────────────────────────────────────────────────────────

export const reviewFinding = (id: string, action: "approve" | "reject", note?: string) =>
  request(`/api/v1/findings/${id}/review`, {
    method: "POST",
    body: JSON.stringify({ action, note }),
  });

// ── Health ────────────────────────────────────────────────────────────────────

export const healthCheck = () =>
  request<{ status: string; llm_available: boolean; db: string; redis: string }>("/healthz");

// ── Export ────────────────────────────────────────────────────────────────────

export async function downloadReportPdf(reportId: string): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${BACKEND_URL}/api/v1/reports/${reportId}/export`);
  } catch (err) {
    throw new NetworkError(err);
  }
  if (!response.ok) {
    let code = "export_error";
    let message = `Export failed (HTTP ${response.status})`;
    try {
      const body = await response.json();
      code = body?.error?.code ?? code;
      message = body?.error?.message ?? message;
    } catch { /* ignore */ }
    throw new ApiError(response.status, code, message);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `peerless_report_${reportId.slice(0, 8)}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// ── Types ─────────────────────────────────────────────────────────────────────

export type PaperStatus = "uploaded" | "parsing" | "parsed" | "parse_failed";
export type ReportStatus = "pending" | "partial" | "complete" | "failed";

export interface PaperMetadata {
  title: string | null;
  authors: string[];
  abstract: string | null;
  doi: string | null;
  page_count: number | null;
  language: string | null;
  truncated: boolean;
}

export interface PaperResponse {
  id: string;
  original_filename: string;
  byte_size: number;
  status: PaperStatus;
  language: string | null;
  parsed_metadata: PaperMetadata | null;
  uploaded_at: string;
  error_message: string | null;
}

export interface FindingResponse {
  id: string;
  agent: string;
  severity: "info" | "low" | "medium" | "high";
  confidence: number;
  title: string;
  summary: string;
  evidence: Array<{ kind: string; content: Record<string, unknown> }>;
  requires_human_review: boolean;
  status: "draft" | "approved" | "rejected";
  reviewer_note: string | null;
  reviewed_at: string | null;
}

export interface ReportResponse {
  id: string;
  paper_id: string;
  status: ReportStatus;
  overall_confidence: "low" | "medium" | "high" | null;
  findings: FindingResponse[];
  plain_language_summary: string | null;
  created_at: string;
  completed_at: string | null;
  error: string | null;
}
