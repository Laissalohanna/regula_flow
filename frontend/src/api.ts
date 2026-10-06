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
  failure_count: number;
  record_count: number;
  inconsistency_count: number;
  reprocess_count: number;
};

export type FindingHit = {
  batch_id: string;
  batch_identifier: string;
  file_name: string;
  code: string;
  description: string;
  severity: string;
  operation_identifier: string;
  occurred_at: string;
};

export type FindingFilters = {
  lote?: string;
  operacao?: string;
  regra?: string;
  severidade?: string;
  desde?: string;
  ate?: string;
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

export function listFindings(filters: FindingFilters = {}): Promise<FindingHit[]> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value) {
      params.set(key, value);
    }
  }
  const query = params.toString();
  return request(`/api/inconsistencias${query ? `?${query}` : ""}`);
}

export function createBatch(payload: BatchInput): Promise<Batch> {
  return request("/api/lotes", { method: "POST", body: JSON.stringify(payload) });
}

export function reprocessBatch(id: string): Promise<Batch> {
  return request(`/api/lotes/${id}/reprocessamentos`, { method: "POST" });
}
