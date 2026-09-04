import { useEffect, useMemo, useState, type FormEvent } from "react";
import { api, query } from "../api/client";
import type { Category, Paginated, Transaction } from "../api/types";
import { Card, Field, GhostButton, Modal, PageHeader, PrimaryButton, StatusBadge, inputClass } from "../components/ui";
import { formatBRL, formatDate, typeLabel } from "../lib/format";

const emptyForm = {
  date: new Date().toISOString().slice(0, 10),
  description: "",
  type: "expense" as "income" | "expense",
  category_id: "",
  amount: "",
  status: "paid" as "paid" | "pending" | "cancelled",
  due_date: "",
  party_name: "",
  notes: "",
};

export function TransactionsPage() {
  const [items, setItems] = useState<Paginated<Transaction> | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [filters, setFilters] = useState({ search: "", type: "", status: "", category_id: "", date_from: "", date_to: "", page: 1 });
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Transaction | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");

  const filteredCategories = useMemo(
    () => categories.filter((item) => item.type === form.type),
    [categories, form.type],
  );

  const load = async () => {
    const data = await api<Paginated<Transaction>>(
      `/api/v1/transactions${query({ ...filters, page_size: 20 })}`,
    );
    setItems(data);
  };

  useEffect(() => {
    void api<Category[]>("/api/v1/categories").then(setCategories);
  }, []);

  useEffect(() => {
    void load().catch((err) => setError(err.message));
  }, [filters]);

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setOpen(true);
  };

  const openEdit = (item: Transaction) => {
    setEditing(item);
    setForm({
      date: item.date,
      description: item.description,
      type: item.type,
      category_id: item.category_id,
      amount: String(item.amount),
      status: item.status,
      due_date: item.due_date ?? "",
      party_name: item.party_name ?? "",
      notes: item.notes ?? "",
    });
    setOpen(true);
  };

  const save = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    const payload = {
      ...form,
      amount: Number(form.amount),
      due_date: form.due_date || null,
      party_name: form.party_name || null,
      notes: form.notes || null,
    };
    try {
      if (editing) {
        await api(`/api/v1/transactions/${editing.id}`, { method: "PUT", body: JSON.stringify(payload) });
      } else {
        await api("/api/v1/transactions", { method: "POST", body: JSON.stringify(payload) });
      }
      setOpen(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar");
    }
  };

  return (
    <div>
      <PageHeader
        title="Lançamentos"
        subtitle="Registre receitas e despesas, com filtros por período, tipo e status."
        actions={<PrimaryButton onClick={openCreate}>Novo lançamento</PrimaryButton>}
      />
      <Card className="mb-4">
        <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
          <input className={inputClass} placeholder="Buscar descrição" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value, page: 1 })} />
          <select className={inputClass} value={filters.type} onChange={(e) => setFilters({ ...filters, type: e.target.value, page: 1 })}>
            <option value="">Todos os tipos</option>
            <option value="income">Receita</option>
            <option value="expense">Despesa</option>
          </select>
          <select className={inputClass} value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value, page: 1 })}>
            <option value="">Todos os status</option>
            <option value="paid">Pago</option>
            <option value="pending">Pendente</option>
            <option value="cancelled">Cancelado</option>
          </select>
          <select className={inputClass} value={filters.category_id} onChange={(e) => setFilters({ ...filters, category_id: e.target.value, page: 1 })}>
            <option value="">Todas as categorias</option>
            {categories.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
          <input className={inputClass} type="date" value={filters.date_from} onChange={(e) => setFilters({ ...filters, date_from: e.target.value, page: 1 })} />
          <input className={inputClass} type="date" value={filters.date_to} onChange={(e) => setFilters({ ...filters, date_to: e.target.value, page: 1 })} />
        </div>
      </Card>

      {error ? <p className="mb-3 text-sm text-red-700">{error}</p> : null}

      <Card className="overflow-x-auto p-0">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="border-b border-line text-muted">
            <tr>
              <th className="px-4 py-3 font-medium">Data</th>
              <th className="px-4 py-3 font-medium">Descrição</th>
              <th className="px-4 py-3 font-medium">Categoria</th>
              <th className="px-4 py-3 font-medium">Tipo</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium text-right">Valor</th>
              <th className="px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {items?.items.map((item) => (
              <tr key={item.id} className="border-b border-line last:border-0">
                <td className="px-4 py-3">{formatDate(item.date)}</td>
                <td className="px-4 py-3">
                  <p>{item.description}</p>
                  {item.party_name ? <p className="text-xs text-muted">{item.party_name}</p> : null}
                </td>
                <td className="px-4 py-3">{item.category_name}</td>
                <td className="px-4 py-3">{typeLabel(item.type)}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={item.status} />
                </td>
                <td className={`px-4 py-3 text-right tabular ${item.type === "income" ? "text-income" : "text-expense"}`}>
                  {formatBRL(item.amount)}
                </td>
                <td className="px-4 py-3 text-right">
                  <button className="text-sm text-brand" onClick={() => openEdit(item)}>
                    Editar
                  </button>
                  <button
                    className="ml-3 text-sm text-expense"
                    onClick={async () => {
                      if (confirm("Excluir este lançamento?")) {
                        await api(`/api/v1/transactions/${item.id}`, { method: "DELETE" });
                        await load();
                      }
                    }}
                  >
                    Excluir
                  </button>
                </td>
              </tr>
            ))}
            {items && items.items.length === 0 ? (
              <tr>
                <td className="px-4 py-8 text-center text-muted" colSpan={7}>
                  Nenhum lançamento encontrado.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </Card>

      {items && items.total > items.page_size ? (
        <div className="mt-4 flex justify-end gap-2">
          <GhostButton disabled={filters.page <= 1} onClick={() => setFilters({ ...filters, page: filters.page - 1 })}>
            Anterior
          </GhostButton>
          <GhostButton
            disabled={filters.page * items.page_size >= items.total}
            onClick={() => setFilters({ ...filters, page: filters.page + 1 })}
          >
            Próxima
          </GhostButton>
        </div>
      ) : null}

      {open ? (
        <Modal title={editing ? "Editar lançamento" : "Novo lançamento"} onClose={() => setOpen(false)}>
          <form className="space-y-3" onSubmit={save}>
            <Field label="Data">
              <input className={inputClass} type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} required />
            </Field>
            <Field label="Descrição">
              <input className={inputClass} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} required />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Tipo">
                <select className={inputClass} value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value as "income" | "expense", category_id: "" })}>
                  <option value="income">Receita</option>
                  <option value="expense">Despesa</option>
                </select>
              </Field>
              <Field label="Status">
                <select className={inputClass} value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value as typeof form.status })}>
                  <option value="paid">Pago</option>
                  <option value="pending">Pendente</option>
                  <option value="cancelled">Cancelado</option>
                </select>
              </Field>
            </div>
            <Field label="Categoria">
              <select className={inputClass} value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })} required>
                <option value="">Selecione</option>
                {filteredCategories.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Valor">
              <input className={inputClass} type="number" min="0.01" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
            </Field>
            {form.status === "pending" ? (
              <Field label="Vencimento">
                <input className={inputClass} type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
              </Field>
            ) : null}
            <Field label="Cliente / fornecedor">
              <input className={inputClass} value={form.party_name} onChange={(e) => setForm({ ...form, party_name: e.target.value })} />
            </Field>
            <Field label="Observação">
              <textarea className={inputClass} rows={3} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            </Field>
            {error ? <p className="text-sm text-red-700">{error}</p> : null}
            <div className="flex justify-end gap-2 pt-2">
              <GhostButton type="button" onClick={() => setOpen(false)}>
                Cancelar
              </GhostButton>
              <PrimaryButton type="submit">Salvar</PrimaryButton>
            </div>
          </form>
        </Modal>
      ) : null}
    </div>
  );
}
