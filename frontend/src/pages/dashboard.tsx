import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getMetrics, listBatches, type BatchSummary, type Metrics } from "../api";
import { countLabel, statusLabel } from "../format";
import { BatchTable, Notice, PageHeader } from "../ui";

const GROUPS = ["COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED"] as const;

export function Dashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [batches, setBatches] = useState<BatchSummary[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getMetrics(), listBatches()])
      .then(([nextMetrics, nextBatches]) => {
        setMetrics(nextMetrics);
        setBatches(nextBatches);
      })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  const total = batches.length || 1;

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
      <div className="split">
        <article className="panel pad">
          <h2>Composição dos lotes</h2>
          <div className="bar" aria-hidden="true">
            {GROUPS.map((status) => {
              const count = batches.filter((batch) => batch.status === status).length;
              if (count === 0) {
                return null;
              }
              return (
                <span
                  key={status}
                  data-status={status}
                  style={{ width: `${(count / total) * 100}%` }}
                />
              );
            })}
          </div>
          <ul className="legend">
            {GROUPS.map((status) => (
              <li key={status}>
                <StatusDot value={status} />
                {statusLabel(status)} · {batches.filter((batch) => batch.status === status).length}
              </li>
            ))}
          </ul>
          {metrics ? (
            <p className="muted">
              Tempo médio de {metrics.average_seconds.toLocaleString("pt-BR")} s por processamento.
            </p>
          ) : null}
        </article>
        <article className="panel pad">
          <h2>Leitura rápida</h2>
          <p>
            {countLabel(batches.length, "lote acompanhado", "lotes acompanhados")}. Um aviso sozinho
            não impede a conclusão. Erro de dado encerra o lote com inconsistência e permite
            reprocessar.
          </p>
          <p className="muted">A consulta detalhada filtra por lote, operação, regra e período.</p>
        </article>
      </div>
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

function StatusDot({ value }: { value: string }) {
  return <i className="dot" data-status={value} />;
}
