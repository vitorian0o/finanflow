export function formatBRL(value: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value || 0);
}

export function formatDate(value?: string | null) {
  if (!value) return "—";
  const [year, month, day] = value.slice(0, 10).split("-");
  if (!year || !month || !day) return value;
  return `${day}/${month}/${year}`;
}

export function typeLabel(type: string) {
  return type === "income" ? "Receita" : "Despesa";
}

export function statusLabel(status: string) {
  if (status === "paid") return "Pago";
  if (status === "pending") return "Pendente";
  return "Cancelado";
}

export const PERIODS = [
  { value: "this_month", label: "Este mês" },
  { value: "last_month", label: "Último mês" },
  { value: "last_3_months", label: "Últimos 3 meses" },
  { value: "last_6_months", label: "Últimos 6 meses" },
  { value: "this_year", label: "Este ano" },
  { value: "custom", label: "Personalizado" },
];
