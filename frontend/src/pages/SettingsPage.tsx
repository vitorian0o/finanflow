import { useState, type FormEvent } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Card, Field, PageHeader, PrimaryButton, inputClass } from "../components/ui";

export function SettingsPage() {
  const { user, refresh } = useAuth();
  const [name, setName] = useState(user?.company.name ?? "");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const save = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await api("/api/v1/company", { method: "PUT", body: JSON.stringify({ name }) });
      await refresh();
      setMessage("Nome da empresa atualizado.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar");
    }
  };

  return (
    <div>
      <PageHeader title="Empresa" subtitle="O nome aparece nos relatórios exportados." />
      <Card className="max-w-lg">
        <form className="space-y-4" onSubmit={save}>
          <Field label="Nome da empresa">
            <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} required />
          </Field>
          {message ? <p className="text-sm text-income">{message}</p> : null}
          {error ? <p className="text-sm text-red-700">{error}</p> : null}
          <PrimaryButton type="submit">Salvar</PrimaryButton>
        </form>
      </Card>
    </div>
  );
}
