const STATUS_LABEL: Record<string, string> = {
  RECEIVED: "Recebido",
  PROCESSING: "Processando",
  COMPLETED: "Concluído",
  COMPLETED_WITH_ERRORS: "Concluído com erros",
  FAILED: "Falhou",
  REPROCESSING: "Reprocessando",
};

export function statusLabel(status: string): string {
  return STATUS_LABEL[status] ?? status;
}

export function formatDay(value: string): string {
  const [year, month, day] = value.split("-");
  if (!year || !month || !day) {
    return value;
  }
  return `${day}/${month}/${year}`;
}

export function formatWhen(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

export function canReprocess(status: string): boolean {
  return status === "FAILED" || status === "COMPLETED_WITH_ERRORS";
}
