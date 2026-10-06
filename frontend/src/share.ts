import { jsPDF } from "jspdf";
import QRCode from "qrcode";

import { getBatch, type Batch } from "./api";
import { formatAmount, formatDay, movementLabel, statusLabel } from "./format";

export function reportMessage(batch: Batch): string {
  const latest = batch.runs[batch.runs.length - 1];
  const codes = [...new Set(latest.findings.map((finding) => finding.code))].sort();
  return [
    "Relatório RegulaFlow (demonstração fictícia)",
    `Lote: ${batch.identifier}`,
    `Arquivo: ${batch.file_name}`,
    `Status: ${statusLabel(batch.status)}`,
    `Erros: ${latest.error_count}`,
    `Avisos: ${latest.warning_count}`,
    `Regras: ${codes.length > 0 ? codes.join(", ") : "nenhuma"}`,
  ].join("\n");
}

export function whatsappUrl(batch: Batch): string {
  return `https://wa.me/?text=${encodeURIComponent(reportMessage(batch))}`;
}

export function qrDataUrl(batch: Batch): Promise<string> {
  return QRCode.toDataURL(whatsappUrl(batch), {
    errorCorrectionLevel: "M",
    margin: 1,
    width: 280,
    color: { dark: "#1A1814", light: "#F3EDE3" },
  });
}

export function errorFileCsv(batch: Batch): string {
  const latest = batch.runs[batch.runs.length - 1];
  const lines = ["identificador;valor;data;tipo;regras;severidade;descricao"];
  for (const operation of batch.operations) {
    const related = latest.findings.filter(
      (finding) => finding.operation_identifier.trim() === operation.identifier.trim(),
    );
    lines.push(
      [
        cell(operation.identifier.trim() || "-"),
        operation.amount,
        operation.occurred_on,
        cell(movementLabel(operation.movement_type)),
        cell(related.map((finding) => finding.code).join(",")),
        cell(related.map((finding) => finding.severity).join(",")),
        cell(related.map((finding) => finding.description).join(" | ")),
      ].join(";"),
    );
  }
  return `\uFEFF${lines.join("\n")}\n`;
}

export async function downloadErrorFile(id: string): Promise<void> {
  const batch = await getBatch(id);
  const name = batch.file_name.toLowerCase().endsWith(".csv")
    ? batch.file_name
    : `${batch.file_name}.csv`;
  saveBlob(new Blob([errorFileCsv(batch)], { type: "text/csv;charset=utf-8" }), name);
}

export async function downloadBatchReport(batch: Batch, qr: string): Promise<void> {
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  await useOutfit(doc);
  const latest = batch.runs[batch.runs.length - 1];
  doc.setFillColor(22, 21, 19);
  doc.rect(0, 0, 210, 34, "F");
  doc.setFillColor(176, 141, 78);
  doc.rect(0, 34, 210, 1.4, "F");
  doc.setFillColor(243, 237, 227);
  doc.roundedRect(14, 8, 16, 16, 2, 2, "F");
  doc.setTextColor(26, 24, 20);
  doc.setFont("Outfit", "bold");
  doc.setFontSize(13);
  doc.text("R", 22, 18.5, { align: "center" });
  doc.setTextColor(243, 237, 227);
  doc.setFontSize(18);
  doc.text("RegulaFlow", 34, 15);
  doc.setFont("Outfit", "normal");
  doc.setFontSize(9);
  doc.setTextColor(198, 163, 106);
  doc.text("CASA DE VALIDACAO", 34, 21);
  doc.setTextColor(26, 24, 20);
  doc.setFont("Outfit", "bold");
  doc.setFontSize(16);
  doc.text("Relatório de validação", 14, 48);
  doc.setFont("Outfit", "normal");
  doc.setFontSize(11);
  const intro = [
    `Lote ${batch.identifier}`,
    `Arquivo ${batch.file_name}`,
    `Referência ${formatDay(batch.reference_date)}`,
    `Status ${statusLabel(batch.status)}`,
    `${latest.operation_count} registros · ${latest.error_count} erros · ${latest.warning_count} avisos`,
    "Documento fictício, para demonstração.",
  ];
  doc.text(intro, 14, 58);
  doc.setFont("Outfit", "bold");
  doc.text("Inconsistências", 14, 96);
  doc.setFont("Outfit", "normal");
  let y = 104;
  if (latest.findings.length === 0) {
    doc.text("Nenhuma inconsistência nesta execução.", 14, y);
    y += 8;
  }
  for (const finding of latest.findings) {
    const line = `${finding.code} · ${finding.severity} · ${finding.operation_identifier.trim() || "-"} · ${finding.description}`;
    const wrapped = doc.splitTextToSize(line, 120);
    doc.text(wrapped, 14, y);
    y += wrapped.length * 5 + 2;
  }
  doc.addImage(qr, "PNG", 150, 54, 42, 42);
  doc.setFontSize(8);
  doc.text("Escaneie para enviar\no resumo no WhatsApp.", 150, 100);
  doc.setFontSize(10);
  doc.setFont("Outfit", "bold");
  doc.text("Operações", 14, y + 6);
  doc.setFont("Outfit", "normal");
  y += 14;
  for (const operation of batch.operations) {
    const related = latest.findings.filter(
      (finding) => finding.operation_identifier.trim() === operation.identifier.trim(),
    );
    const mark = related.length > 0 ? related.map((finding) => finding.code).join(", ") : "válida";
    doc.text(
      `${operation.identifier.trim() || "-"}  ${formatAmount(operation.amount)}  ${formatDay(operation.occurred_on)}  ${mark}`,
      14,
      y,
    );
    y += 6;
  }
  doc.save(`relatorio-${batch.identifier}.pdf`);
}

function cell(value: string): string {
  return value.replaceAll(";", ",").replaceAll("\n", " ");
}

function saveBlob(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
}

async function useOutfit(doc: jsPDF) {
  const regular = await fontBinary("/fonts/Outfit-Regular.ttf");
  const bold = await fontBinary("/fonts/Outfit-SemiBold.ttf");
  doc.addFileToVFS("Outfit-Regular.ttf", regular);
  doc.addFileToVFS("Outfit-SemiBold.ttf", bold);
  doc.addFont("Outfit-Regular.ttf", "Outfit", "normal");
  doc.addFont("Outfit-SemiBold.ttf", "Outfit", "bold");
  doc.setFont("Outfit", "normal");
}

async function fontBinary(path: string): Promise<string> {
  const buffer = await fetch(path).then((response) => response.arrayBuffer());
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let index = 0; index < bytes.length; index += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(index, index + 0x8000));
  }
  return binary;
}
