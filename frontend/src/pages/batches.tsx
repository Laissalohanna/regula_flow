import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { listBatches, type BatchSummary } from "../api";
import { statusLabel } from "../format";
import { BatchTable, Notice, PageHeader } from "../ui";

export function BatchList() {
  const [batches, setBatches] = useState<BatchSummary[]>([]);
  const [error, setError] = useState("");
  const [term, setTerm] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    listBatches()
      .then(setBatches)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  const statuses = useMemo(
    () => [...new Set(batches.map((batch) => batch.status))],
    [batches],
  );
  const visible = batches.filter((batch) => {
    const folded = term.trim().toLocaleLowerCase();
    const matchesTerm =
      folded.length === 0 ||
      batch.identifier.toLocaleLowerCase().includes(folded) ||
      batch.file_name.toLocaleLowerCase().includes(folded);
    return matchesTerm && (status === "" || batch.status === status);
  });

  return (
    <section>
      <PageHeader kicker="Recebimento" title="Lotes" lede="Busque pelo identificador ou pelo arquivo.">
        <Link className="button" to="/lotes/novo">
          Novo lote
        </Link>
      </PageHeader>
      {error ? <Notice message={error} /> : null}
      <div className="toolbar">
        <label>
          Busca
          <input
            value={term}
            placeholder="LOTE-SP ou movimentacoes"
            onChange={(event) => setTerm(event.target.value)}
          />
        </label>
        <label>
          Status
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">Todos</option>
            {statuses.map((item) => (
              <option key={item} value={item}>
                {statusLabel(item)}
              </option>
            ))}
          </select>
        </label>
        <p className="muted toolbar-count">
          {visible.length} de {batches.length}
        </p>
      </div>
      <div className="panel">
        <BatchTable batches={visible} empty="Nenhum lote com esse filtro." />
      </div>
    </section>
  );
}
