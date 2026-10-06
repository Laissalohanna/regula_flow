import { useEffect, useState, type ReactNode } from "react";
import { useParams } from "react-router-dom";

import { getBatch, reprocessBatch, type Batch, type Finding } from "../api";
import { canReprocess, countLabel, formatAmount, formatDay, formatWhen, movementLabel } from "../format";
import { downloadBatchReport, downloadErrorFile, qrDataUrl, whatsappUrl } from "../share";
import { Notice, PageHeader, Status } from "../ui";

type Tab = "operacoes" | "inconsistencias" | "historico";

export function BatchDetail() {
  const params = useParams();
  const [batch, setBatch] = useState<Batch | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [tab, setTab] = useState<Tab>("operacoes");
  const [rule, setRule] = useState("");
  const [severity, setSeverity] = useState("");
  const [qr, setQr] = useState("");

  useEffect(() => {
    if (!params.id) {
      return;
    }
    setQr("");
    getBatch(params.id)
      .then((next) => {
        setBatch(next);
        return qrDataUrl(next);
      })
      .then(setQr)
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
      setTab("historico");
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
  const findings = latest.findings.filter((finding) => {
    const matchesRule = rule === "" || finding.code.toLocaleLowerCase().includes(rule.toLocaleLowerCase());
    return matchesRule && (severity === "" || finding.severity === severity);
  });

  return (
    <section>
      <PageHeader
        kicker={batch.file_name}
        title={batch.identifier}
        lede={`Referência ${formatDay(batch.reference_date)} · ${countLabel(batch.operations.length, "operação", "operações")}`}
      >
        <Status value={batch.status} />
      </PageHeader>
      {error ? <Notice message={error} /> : null}
      <div className="report-row">
        <div className="detail-actions">
          {canReprocess(batch.status) ? (
            <button className="button" type="button" onClick={() => void reprocess()} disabled={pending}>
              Reprocessar
            </button>
          ) : (
            <p className="muted">Este lote não aceita reprocessamento.</p>
          )}
          {latest.error_count > 0 ? (
            <button
              className="button-secondary"
              type="button"
              onClick={() =>
                void downloadErrorFile(batch.id).catch((reason: Error) => setError(reason.message))
              }
            >
              Baixar arquivo
            </button>
          ) : null}
          <button
            className="button-secondary"
            type="button"
            disabled={qr === ""}
            onClick={() =>
              void downloadBatchReport(batch, qr).catch((reason: Error) => setError(reason.message))
            }
          >
            Relatório PDF
          </button>
          <a className="button-secondary" href={whatsappUrl(batch)} target="_blank" rel="noreferrer">
            Enviar no WhatsApp
          </a>
        </div>
        <aside className="qr-card">
          {qr ? <img src={qr} alt="QR Code para enviar o relatório no WhatsApp" /> : <p>Gerando QR Code.</p>}
          <p>Aponte a câmera para abrir o WhatsApp com o resumo deste lote.</p>
        </aside>
      </div>
      <div className="tabs" role="tablist">
        <TabButton current={tab} name="operacoes" onSelect={setTab}>
          Operações
        </TabButton>
        <TabButton current={tab} name="inconsistencias" onSelect={setTab}>
          Inconsistências ({latest.findings.length})
        </TabButton>
        <TabButton current={tab} name="historico" onSelect={setTab}>
          Histórico ({batch.runs.length})
        </TabButton>
      </div>
      {tab === "operacoes" ? <Operations batch={batch} findings={latest.findings} /> : null}
      {tab === "inconsistencias" ? (
        <div className="stack">
          <div className="toolbar">
            <label>
              Regra
              <input value={rule} placeholder="VAL" onChange={(event) => setRule(event.target.value)} />
            </label>
            <label>
              Severidade
              <select value={severity} onChange={(event) => setSeverity(event.target.value)}>
                <option value="">Todas</option>
                <option value="ERROR">Erro</option>
                <option value="WARNING">Aviso</option>
              </select>
            </label>
          </div>
          <div className="panel">
            {findings.length === 0 ? (
              <p className="empty">Nenhuma inconsistência.</p>
            ) : (
              <FindingTable findings={findings} />
            )}
          </div>
        </div>
      ) : null}
      {tab === "historico" ? (
        <div className="stack">
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
        </div>
      ) : null}
    </section>
  );
}

function TabButton({
  current,
  name,
  onSelect,
  children,
}: {
  current: Tab;
  name: Tab;
  onSelect: (name: Tab) => void;
  children: ReactNode;
}) {
  return (
    <button type="button" role="tab" aria-selected={current === name} onClick={() => onSelect(name)}>
      {children}
    </button>
  );
}

function Operations({ batch, findings }: { batch: Batch; findings: Finding[] }) {
  return (
    <div className="panel">
      <table>
        <thead>
          <tr>
          <th>Operação</th>
          <th>Tipo</th>
          <th>Valor</th>
          <th>Data</th>
          <th>Resultado</th>
          </tr>
        </thead>
        <tbody>
          {batch.operations.map((operation, index) => {
            const related = findings.filter(
              (finding) => finding.operation_identifier.trim() === operation.identifier.trim(),
            );
            return (
              <tr key={`${operation.identifier}-${index}`}>
                <td className="strong">{operation.identifier.trim() || "—"}</td>
                <td>{movementLabel(operation.movement_type)}</td>
                <td className="num">{formatAmount(operation.amount)}</td>
                <td>{formatDay(operation.occurred_on)}</td>
                <td>
                  {related.length === 0 ? (
                    <span className="ok">Válida</span>
                  ) : (
                    <span className="codes">
                      {related.map((finding, findingIndex) => (
                        <span className="code" key={`${finding.code}-${findingIndex}`}>
                          {finding.code}
                        </span>
                      ))}
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function FindingTable({ findings }: { findings: Finding[] }) {
  return (
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
        {findings.map((finding, index) => (
          <tr key={`${finding.code}-${finding.operation_identifier}-${index}`}>
            <td className="code">{finding.code}</td>
            <td>
              <Status value={finding.severity} />
            </td>
            <td>{finding.operation_identifier.trim() || "—"}</td>
            <td>{finding.description}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
