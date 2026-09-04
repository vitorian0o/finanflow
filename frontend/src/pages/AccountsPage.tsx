import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { AccountSummary, Paginated, Transaction } from "../api/types";
import { Card, PageHeader, PrimaryButton, StatusBadge } from "../components/ui";
import { formatBRL, formatDate } from "../lib/format";

export function AccountsPage({ kind }: { kind: "payable" | "receivable" }) {
  const [summary, setSummary] = useState<AccountSummary | null>(null);
  const [items, setItems] = useState<Paginated<Transaction> | null>(null);
  const path = kind === "payable" ? "/api/v1/accounts/payable" : "/api/v1/accounts/receivable";

  const load = async () => {
    const [summaryData, list] = await Promise.all([
      api<AccountSummary>("/api/v1/accounts/summary"),
      api<Paginated<Transaction>>(path),
    ]);
    setSummary(summaryData);
    setItems(list);
  };

  useEffect(() => {
    void load();
  }, [kind]);

  const title = kind === "payable" ? "Contas a pagar" : "Contas a receber";

  return (
    <div>
      <PageHeader title={title} subtitle="Acompanhe vencimentos, atrasos e previsões de caixa." />
      {summary ? (
        <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <SummaryCard label="Vencidas" value={formatBRL(summary.overdue_amount)} hint={`${summary.overdue_count} contas`} />
          <SummaryCard label="Vence hoje" value={formatBRL(summary.due_today_amount)} hint={`${summary.due_today_count} contas`} />
          <SummaryCard label="Próximos 7 dias" value={formatBRL(summary.due_soon_amount)} hint={`${summary.due_soon_count} contas`} />
          <SummaryCard
            label={kind === "payable" ? "Saídas previstas" : "Recebimentos previstos"}
            value={formatBRL(kind === "payable" ? summary.expected_outflow : summary.expected_inflow)}
            hint="Pendentes em aberto"
          />
        </div>
      ) : null}
      <Card className="overflow-x-auto p-0">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="border-b border-line text-muted">
            <tr>
              <th className="px-4 py-3 font-medium">{kind === "receivable" ? "Cliente" : "Fornecedor"}</th>
              <th className="px-4 py-3 font-medium">Descrição</th>
              <th className="px-4 py-3 font-medium">Categoria</th>
              <th className="px-4 py-3 font-medium">Vencimento</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium text-right">Valor</th>
              <th className="px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {items?.items.map((item) => (
              <tr key={item.id} className="border-b border-line last:border-0">
                <td className="px-4 py-3">{item.party_name || "—"}</td>
                <td className="px-4 py-3">{item.description}</td>
                <td className="px-4 py-3">{item.category_name}</td>
                <td className="px-4 py-3">{formatDate(item.due_date)}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={item.status} />
                </td>
                <td className="px-4 py-3 text-right tabular">{formatBRL(item.amount)}</td>
                <td className="px-4 py-3 text-right">
                  <PrimaryButton
                    onClick={async () => {
                      await api(`/api/v1/transactions/${item.id}/settle`, { method: "POST" });
                      await load();
                    }}
                  >
                    Marcar como {kind === "payable" ? "pago" : "recebido"}
                  </PrimaryButton>
                </td>
              </tr>
            ))}
            {items && items.items.length === 0 ? (
              <tr>
                <td className="px-4 py-8 text-center text-muted" colSpan={7}>
                  Nenhuma conta pendente.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

function SummaryCard({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <Card>
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-2 text-lg font-semibold tabular">{value}</p>
      <p className="mt-1 text-xs text-muted">{hint}</p>
    </Card>
  );
}
