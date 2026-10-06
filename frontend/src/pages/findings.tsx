import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listFindings, type FindingFilters, type FindingHit } from "../api";
import { formatWhen } from "../format";
import { Notice, PageHeader, Status } from "../ui";

const EMPTY: FindingFilters = {
  lote: "",
  operacao: "",
  regra: "",
  severidade: "",
  desde: "",
  ate: "",
};

export function FindingsPage() {
  const [draft, setDraft] = useState<FindingFilters>(EMPTY);
  const [filters, setFilters] = useState<FindingFilters>(EMPTY);
  const [hits, setHits] = useState<FindingHit[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    listFindings(toQuery(filters))
      .then(setHits)
      .catch((reason: Error) => setError(reason.message));
  }, [filters]);

  function update(field: keyof FindingFilters, value: string) {
    setDraft((current) => ({ ...current, [field]: value }));
  }

  return (
    <section>
      <PageHeader
        kicker="Consulta"
        title="Inconsistências"
        lede="Filtre o resultado da última execução de cada lote."
      >
        <button className="button-secondary" type="button" onClick={() => downloadCsv(hits)}>
          Exportar CSV
        </button>
      </PageHeader>
      {error ? <Notice message={error} /> : null}
      <form
        className="toolbar"
        onSubmit={(event) => {
          event.preventDefault();
          setFilters(draft);
        }}
      >
        <label>
          Lote ou arquivo
          <input value={draft.lote} onChange={(event) => update("lote", event.target.value)} />
        </label>
        <label>
          Operação
          <input value={draft.operacao} onChange={(event) => update("operacao", event.target.value)} />
        </label>
        <label>
          Regra
          <input value={draft.regra} placeholder="VAL005" onChange={(event) => update("regra", event.target.value)} />
        </label>
        <label>
          Severidade
          <select value={draft.severidade} onChange={(event) => update("severidade", event.target.value)}>
            <option value="">Todas</option>
            <option value="ERROR">Erro</option>
            <option value="WARNING">Aviso</option>
          </select>
        </label>
        <label>
          De
          <input type="date" value={draft.desde} onChange={(event) => update("desde", event.target.value)} />
        </label>
        <label>
          Até
          <input type="date" value={draft.ate} onChange={(event) => update("ate", event.target.value)} />
        </label>
        <div className="toolbar-actions">
          <button className="button" type="submit">
            Filtrar
          </button>
          <button
            className="button-secondary"
            type="button"
            onClick={() => {
              setDraft(EMPTY);
              setFilters(EMPTY);
            }}
          >
            Limpar
          </button>
        </div>
      </form>
      <div className="panel">
        {hits.length === 0 ? (
          <p className="empty">Nenhuma inconsistência para esse filtro.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Lote</th>
                <th>Regra</th>
                <th>Severidade</th>
                <th>Operação</th>
                <th>Descrição</th>
                <th>Quando</th>
              </tr>
            </thead>
            <tbody>
              {hits.map((hit) => (
                <tr key={`${hit.batch_id}-${hit.code}-${hit.operation_identifier}-${hit.description}`}>
                  <td>
                    <Link to={`/lotes/${hit.batch_id}`}>{hit.batch_identifier}</Link>
                    <div className="muted">{hit.file_name}</div>
                  </td>
                  <td className="code">{hit.code}</td>
                  <td>
                    <Status value={hit.severity} />
                  </td>
                  <td>{hit.operation_identifier.trim() || "—"}</td>
                  <td>{hit.description}</td>
                  <td>{formatWhen(hit.occurred_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}

function toQuery(filters: FindingFilters): FindingFilters {
  return {
    lote: filters.lote,
    operacao: filters.operacao,
    regra: filters.regra,
    severidade: filters.severidade,
    desde: filters.desde ? `${filters.desde}T00:00:00` : "",
    ate: filters.ate ? `${filters.ate}T23:59:59` : "",
  };
}

function downloadCsv(hits: FindingHit[]) {
  const rows = [
    ["lote", "arquivo", "regra", "severidade", "operacao", "descricao", "quando"],
    ...hits.map((hit) => [
      hit.batch_identifier,
      hit.file_name,
      hit.code,
      hit.severity,
      hit.operation_identifier,
      hit.description,
      hit.occurred_at,
    ]),
  ];
  const csv = rows.map((row) => row.map(escapeCell).join(";")).join("\n");
  const blob = new Blob([`\uFEFF${csv}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "inconsistencias.csv";
  link.click();
  URL.revokeObjectURL(url);
}

function escapeCell(value: string) {
  return `"${value.replaceAll('"', '""')}"`;
}
