import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { createBatch, type Operation } from "../api";
import { MOVEMENT_TYPES, movementLabel } from "../format";
import { Notice, PageHeader } from "../ui";

const EMPTY_OPERATION: Operation = {
  identifier: "",
  amount: "",
  occurred_on: "",
  movement_type: "ACQUISITION",
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
      <PageHeader kicker="Entrada" title="Novo lote" lede="O lote é validado assim que é recebido." />
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
            <label>
              Tipo
              <select
                value={operation.movement_type}
                onChange={(event) => updateOperation(index, "movement_type", event.target.value)}
              >
                {MOVEMENT_TYPES.map((kind) => (
                  <option key={kind} value={kind}>
                    {movementLabel(kind)}
                  </option>
                ))}
              </select>
            </label>
            <button
              className="button-secondary"
              type="button"
              onClick={() => setOperations((current) => current.filter((_, position) => position !== index))}
              disabled={operations.length === 1}
            >
              Remover
            </button>
          </div>
        ))}
        <div className="form-actions">
          <button
            className="button-secondary"
            type="button"
            onClick={() => setOperations((current) => [...current, { ...EMPTY_OPERATION }])}
          >
            Adicionar operação
          </button>
          <button className="button" type="submit" disabled={pending}>
            Receber lote
          </button>
        </div>
      </form>
    </section>
  );
}
