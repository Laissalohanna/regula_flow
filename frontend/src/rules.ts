export type RuleInfo = {
  code: string;
  severity: "ERROR" | "WARNING";
  title: string;
  detail: string;
};

export const RULES: RuleInfo[] = [
  {
    code: "VAL001",
    severity: "ERROR",
    title: "Campo obrigatório ausente",
    detail: "A operação precisa de identificador. Em branco, o registro não segue.",
  },
  {
    code: "VAL002",
    severity: "ERROR",
    title: "Valor inválido",
    detail: "O valor precisa ser finito e ter no máximo duas casas decimais.",
  },
  {
    code: "VAL003",
    severity: "WARNING",
    title: "Data fora do período",
    detail: "A data da operação está fora do mês de referência do lote. Gera aviso.",
  },
  {
    code: "VAL004",
    severity: "ERROR",
    title: "Operação duplicada",
    detail: "O mesmo identificador aparece mais de uma vez no lote.",
  },
  {
    code: "VAL005",
    severity: "ERROR",
    title: "Valor deve ser maior que zero",
    detail: "Valor zero ou negativo não é aceito como operação válida.",
  },
  {
    code: "VAL006",
    severity: "ERROR",
    title: "Identificador inválido",
    detail: "Use letras, números, hífen ou sublinhado, com até 64 caracteres.",
  },
];
