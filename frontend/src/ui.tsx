import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";

import type { BatchSummary } from "./api";
import { formatDay, statusLabel } from "./format";

export function Notice({ message }: { message: string }) {
  return <p className="banner">{message}</p>;
}

export function Status({ value }: { value: string }) {
  return (
    <span className="status" data-status={value}>
      {statusLabel(value)}
    </span>
  );
}

export function PageHeader({
  kicker,
  title,
  lede,
  children,
}: {
  kicker: string;
  title: string;
  lede?: string;
  children?: ReactNode;
}) {
  return (
    <div className="page-head">
      <div>
        <p className="kicker">{kicker}</p>
        <h1>{title}</h1>
        {lede ? <p className="lede">{lede}</p> : null}
      </div>
      {children}
    </div>
  );
}

export function BatchTable({ batches, empty }: { batches: BatchSummary[]; empty: string }) {
  const navigate = useNavigate();
  if (batches.length === 0) {
    return <p className="empty">{empty}</p>;
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
          <tr key={batch.id} className="clickable" onClick={() => navigate(`/lotes/${batch.id}`)}>
            <td className="strong">{batch.identifier}</td>
            <td className="muted">{batch.file_name}</td>
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
