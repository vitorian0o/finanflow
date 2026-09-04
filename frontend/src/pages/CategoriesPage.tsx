import { useEffect, useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { Category } from "../api/types";
import { Card, Field, GhostButton, Modal, PageHeader, PrimaryButton, inputClass } from "../components/ui";

export function CategoriesPage() {
  const [items, setItems] = useState<Category[]>([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Category | null>(null);
  const [name, setName] = useState("");
  const [type, setType] = useState<"income" | "expense">("expense");
  const [error, setError] = useState("");

  const load = async () => setItems(await api<Category[]>("/api/v1/categories"));

  useEffect(() => {
    void load();
  }, []);

  const save = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    try {
      if (editing) {
        await api(`/api/v1/categories/${editing.id}`, { method: "PUT", body: JSON.stringify({ name, type }) });
      } else {
        await api("/api/v1/categories", { method: "POST", body: JSON.stringify({ name, type }) });
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
        title="Categorias"
        subtitle="Organize receitas e despesas. Categorias em uso não podem ser excluídas."
        actions={
          <PrimaryButton
            onClick={() => {
              setEditing(null);
              setName("");
              setType("expense");
              setOpen(true);
            }}
          >
            Nova categoria
          </PrimaryButton>
        }
      />
      <div className="grid gap-4 md:grid-cols-2">
        {(["income", "expense"] as const).map((group) => (
          <Card key={group}>
            <h2 className="mb-4 text-sm font-medium">{group === "income" ? "Receitas" : "Despesas"}</h2>
            <ul className="space-y-2">
              {items
                .filter((item) => item.type === group)
                .map((item) => (
                  <li key={item.id} className="flex items-center justify-between rounded-lg border border-line px-3 py-2">
                    <span>
                      {item.name}
                      {item.is_default ? <span className="ml-2 text-xs text-muted">padrão</span> : null}
                    </span>
                    <span className="flex gap-3 text-sm">
                      <button
                        className="text-brand"
                        onClick={() => {
                          setEditing(item);
                          setName(item.name);
                          setType(item.type);
                          setOpen(true);
                        }}
                      >
                        Editar
                      </button>
                      <button
                        className="text-expense"
                        onClick={async () => {
                          try {
                            await api(`/api/v1/categories/${item.id}`, { method: "DELETE" });
                            await load();
                          } catch (err) {
                            setError(err instanceof Error ? err.message : "Erro ao excluir");
                          }
                        }}
                      >
                        Excluir
                      </button>
                    </span>
                  </li>
                ))}
            </ul>
          </Card>
        ))}
      </div>
      {error ? <p className="mt-4 text-sm text-red-700">{error}</p> : null}
      {open ? (
        <Modal title={editing ? "Editar categoria" : "Nova categoria"} onClose={() => setOpen(false)}>
          <form className="space-y-3" onSubmit={save}>
            <Field label="Nome">
              <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} required />
            </Field>
            <Field label="Tipo">
              <select className={inputClass} value={type} onChange={(e) => setType(e.target.value as typeof type)}>
                <option value="income">Receita</option>
                <option value="expense">Despesa</option>
              </select>
            </Field>
            {error ? <p className="text-sm text-red-700">{error}</p> : null}
            <div className="flex justify-end gap-2">
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
