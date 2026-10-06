const STATUS_LABEL: Record<string, string> = {
  RECEIVED: "Recebido",
  PROCESSING: "Processando",
  COMPLETED: "Concluído",
  COMPLETED_WITH_ERRORS: "Concluído com erros",
  FAILED: "Falhou",
  REPROCESSING: "Reprocessando",
  ERROR: "Erro",
  WARNING: "Aviso",
  INFO: "Informação",
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

export function formatAmount(value: string): string {
  const amount = Number(value);
  if (Number.isNaN(amount)) {
    return value;
  }
  return amount.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function countLabel(value: number, singular: string, plural: string): string {
  return `${value} ${value === 1 ? singular : plural}`;
}
