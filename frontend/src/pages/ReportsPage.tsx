import { useEffect, useState } from "react";
import { api, query } from "../api/client";
import type { Report } from "../api/types";
import { Card, PageHeader, PrimaryButton } from "../components/ui";
import { PERIODS, formatBRL, formatDate, typeLabel } from "../lib/format";

export function ReportsPage() {
  const [period, setPeriod] = useState("this_month");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (period === "custom" && (!dateFrom || !dateTo)) return;
    api<Report>(`/api/v1/reports${query({ period, date_from: period === "custom" ? dateFrom : undefined, date_to: period === "custom" ? dateTo : undefined })}`)
      .then(setReport)
      .catch((err) => setError(err.message));
  }, [period, dateFrom, dateTo]);

  const exportCsv = async () => {
    const csv = await api<string>(
      `/api/v1/reports/export${query({ period, date_from: period === "custom" ? dateFrom : undefined, date_to: period === "custom" ? dateTo : undefined })}`,
    );
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "relatorio-finanflow.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <PageHeader
        title="Relatórios"
        subtitle="Resumo financeiro do período, pronto para apresentar ou exportar."
        actions={
          <div className="flex flex-wrap gap-2">
            <select className="rounded-lg border border-line px-3 py-2 text-sm" value={period} onChange={(e) => setPeriod(e.target.value)}>
              {PERIODS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
            {period === "custom" ? (
              <>
                <input className="rounded-lg border border-line px-3 py-2 text-sm" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
                <input className="rounded-lg border border-line px-3 py-2 text-sm" type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
              </>
            ) : null}
            <PrimaryButton onClick={() => void exportCsv()}>Exportar CSV</PrimaryButton>
          </div>
        }
      />
      {error ? <p className="mb-4 text-sm text-red-700">{error}</p> : null}
      {report ? (
        <>
          <p className="mb-4 text-sm text-muted">
            {report.company_name} · {formatDate(report.date_from)} a {formatDate(report.date_to)}
          </p>
          <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Stat label="Receitas" value={formatBRL(report.total_income)} />
            <Stat label="Despesas" value={formatBRL(report.total_expense)} />
            <Stat label="Lucro" value={formatBRL(report.profit)} />
            <Stat label="Saldo atual" value={formatBRL(report.current_balance)} />
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <h2 className="mb-3 text-sm font-medium">Categorias</h2>
              <ul className="space-y-2 text-sm">
                {report.categories.map((row) => (
                  <li key={`${row.type}-${row.name}`} className="flex justify-between border-b border-line pb-2 last:border-0">
                    <span>
                      {row.name} <span className="text-muted">· {typeLabel(row.type)}</span>
                    </span>
                    <span className="tabular">{formatBRL(row.amount)}</span>
                  </li>
                ))}
                {report.categories.length === 0 ? <li className="text-muted">Sem movimentos pagos no período.</li> : null}
              </ul>
            </Card>
            <Card>
              <h2 className="mb-3 text-sm font-medium">Contas e evolução</h2>
              <ul className="space-y-2 text-sm">
                <li className="flex justify-between"><span>Vencidas a pagar</span><span>{formatBRL(report.overdue_payables)}</span></li>
                <li className="flex justify-between"><span>Vencidas a receber</span><span>{formatBRL(report.overdue_receivables)}</span></li>
                <li className="flex justify-between"><span>Futuras a pagar (30 dias)</span><span>{formatBRL(report.upcoming_payables)}</span></li>
                <li className="flex justify-between"><span>Futuras a receber (30 dias)</span><span>{formatBRL(report.upcoming_receivables)}</span></li>
              </ul>
              <div className="mt-4 space-y-2 text-sm">
                {report.monthly_evolution.map((point) => (
                  <div key={point.label} className="flex justify-between border-b border-line pb-2">
                    <span>{point.label}</span>
                    <span className="tabular">{formatBRL(point.net)} · saldo {formatBRL(point.balance ?? 0)}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </>
      ) : null}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-2 text-lg font-semibold tabular">{value}</p>
    </Card>
  );
}
