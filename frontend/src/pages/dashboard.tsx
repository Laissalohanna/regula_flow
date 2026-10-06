import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  getDashboard,
  getMetrics,
  listBatches,
  type BatchSummary,
  type DashboardView,
  type Metrics,
} from "../api";
import { movementLabel, statusLabel } from "../format";
import { BatchTable, Notice, PageHeader } from "../ui";

export function Dashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [batches, setBatches] = useState<BatchSummary[]>([]);
  const [panel, setPanel] = useState<DashboardView | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getMetrics(), listBatches(), getDashboard()])
      .then(([nextMetrics, nextBatches, nextPanel]) => {
        setMetrics(nextMetrics);
        setBatches(nextBatches);
        setPanel(nextPanel);
      })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  return (
    <section>
      <PageHeader
        kicker="Operação"
        title="Painel"
        lede="Amostra fictícia de outubro de 2026. Os números saem dos lotes já processados."
      >
        <Link className="button" to="/inconsistencias">
          Ver inconsistências
        </Link>
      </PageHeader>
      {error ? <Notice message={error} /> : null}
      {metrics ? (
        <div className="stats">
          <Metric value={metrics.total} label="Processamentos" />
          <Metric value={metrics.record_count} label="Registros" />
          <Metric value={metrics.inconsistency_count} label="Inconsistências" />
          <Metric value={metrics.reprocess_count} label="Reprocessamentos" />
          <Metric value={`${metrics.success_rate}%`} label="Taxa de sucesso" />
          <Metric value={metrics.failure_count} label="Falhas técnicas" />
        </div>
      ) : null}
      {panel ? (
        <div className="chart-grid">
          <BarChart
            title="Performance"
            ceiling={100}
            rows={[
              { label: "Taxa de sucesso", value: panel.success_rate, hint: percent(panel.success_rate) },
              { label: "Taxa de erro", value: panel.error_rate, hint: percent(panel.error_rate) },
              {
                label: "Tempo médio",
                value: Math.min(100, panel.average_seconds * 10),
                hint: `${panel.average_seconds.toLocaleString("pt-BR")} s`,
              },
              {
                label: "Reprocessamentos",
                value: panel.reprocess_count === 0 ? 0 : Math.min(100, panel.reprocess_count * 20),
                hint: String(panel.reprocess_count),
              },
            ]}
          />
          <BarChart
            title="Tipos de arquivo"
            rows={panel.file_types.map((item) => ({
              label: fileLabel(item.label),
              value: item.count,
            }))}
          />
          <BarChart
            title="Etapa de validação"
            rows={panel.stages.map((item) => ({
              label: statusLabel(item.label),
              value: item.count,
            }))}
          />
          <BarChart
            title="Tipos de movimento"
            rows={panel.movements.map((item) => ({
              label: movementLabel(item.label),
              value: item.count,
            }))}
          />
        </div>
      ) : null}
      <h2>Lotes da amostra</h2>
      <div className="panel">
        <BatchTable batches={batches} empty="Nenhum lote recebido." />
      </div>
    </section>
  );
}

function Metric({ value, label }: { value: number | string; label: string }) {
  return (
    <article className="stat">
      <strong>{value}</strong>
      <span>{label}</span>
    </article>
  );
}

function BarChart({
  title,
  rows,
  ceiling,
}: {
  title: string;
  rows: { label: string; value: number; hint?: string }[];
  ceiling?: number;
}) {
  const scale = ceiling ?? Math.max(1, ...rows.map((row) => row.value));
  return (
    <article className="panel pad chart">
      <h2>{title}</h2>
      {rows.length === 0 ? (
        <p className="empty">Sem dados.</p>
      ) : (
        <ul>
          {rows.map((row) => (
            <li key={row.label}>
              <span>{row.label}</span>
              <span className="track">
                <span style={{ width: `${Math.max(0, (row.value / scale) * 100)}%` }} />
              </span>
              <strong>{row.hint ?? row.value}</strong>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

function percent(value: number): string {
  return `${value.toLocaleString("pt-BR")}%`;
}

function fileLabel(label: string): string {
  if (label === "sem_extensao") {
    return "Sem extensão";
  }
  return label.toUpperCase();
}
