import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  createBatch,
  getBatch,
  getMetrics,
  listBatches,
  reprocessBatch,
  type Batch,
  type BatchSummary,
  type Metrics,
  type Operation,
} from "./api";
import { canReprocess, formatDay, formatWhen, statusLabel } from "./format";

function countLabel(value: number, singular: string, plural: string) {
  return `${value} ${value === 1 ? singular : plural}`;
}

function Notice({ message }: { message: string }) {
  return <p className="banner">{message}</p>;
}

function Status({ value }: { value: string }) {
  return (
    <span className="status" data-status={value}>
      {statusLabel(value)}
    </span>
  );
}

function BatchTable({ batches }: { batches: BatchSummary[] }) {
  const navigate = useNavigate();
  if (batches.length === 0) {
    return <p className="empty">Nenhum lote recebido.</p>;
  }
  return (
    <table>
      <thead>
        <tr>
          <th>Lote</th>
          <th>Arquivo</th>
          <th>Referência</th>
          <th>Status</th>
          <th>Registros</th>
          <th>Erros</th>
          <th>Avisos</th>
        </tr>
      </thead>
      <tbody>
        {batches.map((batch) => (
          <tr
            key={batch.id}
            className="clickable"
            onClick={() => navigate(`/lotes/${batch.id}`)}
          >
            <td>
              <Link to={`/lotes/${batch.id}`}>{batch.identifier}</Link>
            </td>
            <td className="file">{batch.file_name}</td>
            <td>{formatDay(batch.reference_date)}</td>
            <td>
              <Status value={batch.status} />
            </td>
            <td className="num">{batch.operation_count}</td>
            <td className="num">{batch.error_count}</td>
            <td className="num">{batch.warning_count}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

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

  return (
    <section>
      <div className="page-head">
        <div>
          <p className="kicker">Outubro 2026</p>
          <h1>Qualidade dos lotes</h1>
          <p className="lede">Amostra fictícia para ver validação, erro e reprocessamento.</p>
        </div>
      </div>
      {error ? <Notice message={error} /> : null}
      {metrics ? (
        <div className="stats">
          <div className="stat">
            <strong>{metrics.total}</strong>
            <span>Processamentos</span>
          </div>
          <div className="stat good">
            <strong>{metrics.success_rate}%</strong>
            <span>Taxa de sucesso</span>
          </div>
          <div className="stat bad">
            <strong>{metrics.error_rate}%</strong>
            <span>Taxa de erro</span>
          </div>
          <div className="stat warn">
            <strong>{metrics.inconsistency_rate}%</strong>
            <span>Inconsistência</span>
          </div>
        </div>
      ) : null}
      {metrics ? (
        <p className="average">
          Tempo médio de {metrics.average_seconds.toLocaleString("pt-BR")} s por
          processamento.
        </p>
      ) : null}
      <h2>Lotes da amostra</h2>
      <div className="panel">
        <BatchTable batches={batches} />
      </div>
    </section>
  );
}

export function BatchList() {
  const [batches, setBatches] = useState<BatchSummary[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    listBatches()
      .then(setBatches)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  return (
    <section>
      <div className="page-head">
        <div>
          <p className="kicker">Operações</p>
          <h1>Lotes recebidos</h1>
        </div>
        <Link className="button" to="/lotes/novo">
          Novo lote
        </Link>
      </div>
      {error ? <Notice message={error} /> : null}
      <div className="panel">
        <BatchTable batches={batches} />
      </div>
    </section>
  );
}

const EMPTY_OPERATION: Operation = {
  identifier: "",
  amount: "",
  occurred_on: "",
};

export function BatchForm() {
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState("");
  const [fileName, setFileName] = useState("");
  const [referenceDate, setReferenceDate] = useState("");
  const [operations, setOperations] = useState<Operation[]>([{ ...EMPTY_OPERATION }]);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  function updateOperation(index: number, field: keyof Operation, value: string) {
    setOperations((current) =>
      current.map((operation, position) =>
        position === index ? { ...operation, [field]: value } : operation,
      ),
    );
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      const batch = await createBatch({
        identifier,
        file_name: fileName,
        reference_date: referenceDate,
        operations,
      });
      navigate(`/lotes/${batch.id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Falha ao receber o lote.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <p className="kicker">Entrada</p>
          <h1>Novo lote</h1>
        </div>
      </div>
      <form className="form panel form-card" onSubmit={(event) => void submit(event)}>
        {error ? <Notice message={error} /> : null}
        <div className="grid-3">
          <label>
            Identificador
            <input value={identifier} onChange={(event) => setIdentifier(event.target.value)} required />
          </label>
          <label>
            Arquivo
            <input value={fileName} onChange={(event) => setFileName(event.target.value)} required />
          </label>
          <label>
            Data de referência
            <input
              type="date"
              value={referenceDate}
              onChange={(event) => setReferenceDate(event.target.value)}
              required
            />
          </label>
        </div>
        <h2>Operações</h2>
        {operations.map((operation, index) => (
          <div className="operation" key={index}>
            <label>
              Identificador
              <input
                value={operation.identifier}
                onChange={(event) => updateOperation(index, "identifier", event.target.value)}
              />
            </label>
            <label>
              Valor
              <input
                value={operation.amount}
                onChange={(event) => updateOperation(index, "amount", event.target.value)}
                required
              />
            </label>
            <label>
              Data
              <input
                type="date"
                value={operation.occurred_on}
                onChange={(event) => updateOperation(index, "occurred_on", event.target.value)}
                required
              />
            </label>
            <button
              className="button-secondary"
              type="button"
              onClick={() =>
                setOperations((current) => current.filter((_, position) => position !== index))
              }
              disabled={operations.length === 1}
            >
              Remover
            </button>
          </div>
        ))}
        <div>
          <button
            className="button-secondary"
            type="button"
            onClick={() => setOperations((current) => [...current, { ...EMPTY_OPERATION }])}
          >
            Adicionar operação
          </button>
        </div>
        <div>
          <button className="button" type="submit" disabled={pending}>
            Receber lote
          </button>
        </div>
      </form>
    </section>
  );
}

export function BatchDetail() {
  const params = useParams();
  const [batch, setBatch] = useState<Batch | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (!params.id) {
      return;
    }
    getBatch(params.id)
      .then(setBatch)
      .catch((reason: Error) => setError(reason.message));
  }, [params.id]);

  async function reprocess() {
    if (!batch) {
      return;
    }
    setPending(true);
    setError("");
    try {
      setBatch(await reprocessBatch(batch.id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Falha ao reprocessar.");
    } finally {
      setPending(false);
    }
  }

  if (!batch) {
    return (
      <section>
        <h1>Lote</h1>
        {error ? <Notice message={error} /> : <p className="muted">Carregando.</p>}
      </section>
    );
  }

  const latest = batch.runs[batch.runs.length - 1];

  return (
    <section className="stack">
      <div className="page-head">
        <div>
          <h1>{batch.identifier}</h1>
          <p className="muted">
            {batch.file_name} · referência {formatDay(batch.reference_date)}
          </p>
        </div>
        <Status value={batch.status} />
      </div>
      {error ? <Notice message={error} /> : null}
      {canReprocess(batch.status) ? (
        <div>
          <button className="button" type="button" onClick={() => void reprocess()} disabled={pending}>
            Reprocessar
          </button>
        </div>
      ) : null}
      <h2>Inconsistências da última execução</h2>
      <div className="panel">
        {latest.findings.length === 0 ? (
          <p className="empty">Nenhuma inconsistência.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Regra</th>
                <th>Severidade</th>
                <th>Operação</th>
                <th>Descrição</th>
              </tr>
            </thead>
            <tbody>
              {latest.findings.map((finding, index) => (
                <tr key={`${finding.code}-${finding.operation_identifier}-${index}`}>
                  <td>{finding.code}</td>
                  <td>
                    <Status value={finding.severity} />
                  </td>
                  <td>{finding.operation_identifier || "—"}</td>
                  <td>{finding.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      <h2>Histórico</h2>
      {batch.runs.map((run, index) => (
        <article className="panel run-card" key={run.id}>
          <p>
            Execução {index + 1} · <Status value={run.status} /> · {formatWhen(run.started_at)} –{" "}
            {formatWhen(run.finished_at)}
          </p>
          <p className="muted">
            {countLabel(run.operation_count, "registro", "registros")} ·{" "}
            {countLabel(run.error_count, "erro", "erros")} ·{" "}
            {countLabel(run.warning_count, "aviso", "avisos")}
          </p>
          <ul className="events">
            {run.events.map((event, eventIndex) => (
              <li key={`${run.id}-${eventIndex}`}>
                {formatWhen(event.created_at)} · {event.action}
              </li>
            ))}
          </ul>
        </article>
      ))}
    </section>
  );
}
