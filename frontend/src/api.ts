export type BatchSummary = {
  id: string;
  identifier: string;
  file_name: string;
  reference_date: string;
  created_at: string;
  status: string;
  operation_count: number;
  error_count: number;
  warning_count: number;
};

export type Finding = {
  code: string;
  description: string;
  severity: string;
  operation_identifier: string;
};

export type AuditEvent = {
  action: string;
  created_at: string;
};

export type Run = {
  id: string;
  status: string;
  started_at: string;
  finished_at: string;
  operation_count: number;
  error_count: number;
  warning_count: number;
  findings: Finding[];
  events: AuditEvent[];
};

export type Operation = {
  identifier: string;
  amount: string;
  occurred_on: string;
};

export type Batch = {
  id: string;
  identifier: string;
  file_name: string;
  reference_date: string;
  created_at: string;
  status: string;
  operations: Operation[];
  runs: Run[];
};

export type Metrics = {
  total: number;
  success_rate: number;
  error_rate: number;
  inconsistency_rate: number;
  average_seconds: number;
};

export type BatchInput = {
  identifier: string;
  file_name: string;
  reference_date: string;
  operations: Operation[];
};

async function fail(response: Response): Promise<never> {
  const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
  if (body && typeof body.detail === "string") {
    throw new Error(body.detail);
  }
  throw new Error("Não foi possível concluir a operação.");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    return fail(response);
  }
  return (await response.json()) as T;
}

export function listBatches(): Promise<BatchSummary[]> {
  return request("/api/lotes");
}

export function getBatch(id: string): Promise<Batch> {
  return request(`/api/lotes/${id}`);
}

export function getMetrics(): Promise<Metrics> {
  return request("/api/metricas");
}

export function createBatch(payload: BatchInput): Promise<Batch> {
  return request("/api/lotes", { method: "POST", body: JSON.stringify(payload) });
}

export function reprocessBatch(id: string): Promise<Batch> {
  return request(`/api/lotes/${id}/reprocessamentos`, { method: "POST" });
}
