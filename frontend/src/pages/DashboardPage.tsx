import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, query } from "../api/client";
import type { Dashboard } from "../api/types";
import { Card, PageHeader } from "../components/ui";
import { PERIODS, formatBRL } from "../lib/format";

const PIE_COLORS = ["#0f766e", "#115e59", "#0f4c5c", "#c2410c", "#b45309", "#334155", "#64748b"];

function moneyTick(value: unknown) {
  return formatBRL(Number(value ?? 0));
}

export function DashboardPage() {
  const [period, setPeriod] = useState("this_month");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      setError("");
      try {
        const payload = await api<Dashboard>(
          `/api/v1/dashboard${query({
            period,
            date_from: period === "custom" ? dateFrom : undefined,
            date_to: period === "custom" ? dateTo : undefined,
          })}`,
        );
        setData(payload);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao carregar dashboard");
      }
    };
    if (period !== "custom" || (dateFrom && dateTo)) void load();
  }, [period, dateFrom, dateTo]);

  const kpis = data
    ? [
        { label: "Receita", value: formatBRL(data.total_income), tone: "text-income" },
        { label: "Despesas", value: formatBRL(data.total_expense), tone: "text-expense" },
        { label: "Lucro", value: formatBRL(data.profit), tone: data.profit >= 0 ? "text-income" : "text-expense" },
        { label: "Margem", value: `${data.margin.toFixed(1)}%`, tone: "" },
        { label: "A pagar", value: formatBRL(data.payable_total), tone: "" },
        { label: "A receber", value: formatBRL(data.receivable_total), tone: "" },
        { label: "Saldo atual", value: formatBRL(data.current_balance), tone: "text-ink" },
      ]
    : [];

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="Visão do caixa, categorias e alertas do período selecionado."
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
          </div>
        }
      />

      {error ? <p className="mb-4 text-sm text-red-700">{error}</p> : null}

      {data?.insights.length ? (
        <div className="mb-6 grid gap-3 md:grid-cols-2">
          {data.insights.slice(0, 4).map((insight) => (
            <div key={insight.type + insight.title} className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
              <p className="text-sm font-medium text-amber-950">{insight.title}</p>
              <p className="text-sm text-amber-900/80">{insight.message}</p>
            </div>
          ))}
        </div>
      ) : null}

      <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4 xl:grid-cols-7">
        {kpis.map((kpi) => (
          <Card key={kpi.label} className="p-4">
            <p className="text-xs uppercase tracking-wide text-muted">{kpi.label}</p>
            <p className={`mt-2 text-lg font-semibold tabular ${kpi.tone}`}>{kpi.value}</p>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <h2 className="mb-4 text-sm font-medium">Receita × despesa</h2>
          <div className="h-64">
            <ResponsiveContainer>
              <BarChart data={data?.income_vs_expense ?? []}>
                <CartesianGrid stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip formatter={moneyTick} />
                <Bar dataKey="income" name="Receita" fill="#0f766e" radius={[4, 4, 0, 0]} />
                <Bar dataKey="expense" name="Despesa" fill="#c2410c" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card>
          <h2 className="mb-4 text-sm font-medium">Evolução do saldo</h2>
          <div className="h-64">
            <ResponsiveContainer>
              <AreaChart data={data?.balance_evolution ?? []}>
                <CartesianGrid stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip formatter={moneyTick} />
                <Area type="monotone" dataKey="balance" name="Saldo" stroke="#115e59" fill="#ccfbf1" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card>
          <h2 className="mb-4 text-sm font-medium">Receita por categoria</h2>
          <CategoryPie data={data?.income_by_category ?? []} />
        </Card>
        <Card>
          <h2 className="mb-4 text-sm font-medium">Despesa por categoria</h2>
          <CategoryPie data={data?.expense_by_category ?? []} />
        </Card>
        <Card className="xl:col-span-2">
          <h2 className="mb-4 text-sm font-medium">Fluxo de caixa mensal</h2>
          <div className="h-64">
            <ResponsiveContainer>
              <BarChart data={data?.monthly_cash_flow ?? []}>
                <CartesianGrid stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip formatter={moneyTick} />
                <Bar dataKey="net" name="Resultado" fill="#0f4c5c" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
}

function CategoryPie({ data }: { data: { name: string; amount: number }[] }) {
  if (!data.length) {
    return <p className="h-64 flex items-center justify-center text-sm text-muted">Sem dados no período.</p>;
  }
  return (
    <div className="h-64">
      <ResponsiveContainer>
        <PieChart>
          <Pie data={data} dataKey="amount" nameKey="name" innerRadius={50} outerRadius={80} paddingAngle={2}>
            {data.map((entry, index) => (
              <Cell key={entry.name} fill={PIE_COLORS[index % PIE_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={moneyTick} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
