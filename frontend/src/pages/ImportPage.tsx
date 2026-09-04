import { useState } from "react";
import { api } from "../api/client";
import type { ImportPreview, ImportResult } from "../api/types";
import { Card, PageHeader, PrimaryButton } from "../components/ui";

export function ImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const send = async (path: "/api/v1/imports/preview" | "/api/v1/imports/confirm") => {
    if (!file) return;
    setError("");
    setLoading(true);
    try {
      const body = new FormData();
      body.append("file", file);
      const data = await api<ImportPreview | ImportResult>(path, { method: "POST", body });
      if (path.endsWith("preview")) {
        setPreview(data as ImportPreview);
        setResult(null);
      } else {
        setResult(data as ImportResult);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na importação");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Importar CSV"
        subtitle="Valide o arquivo antes de gravar. Linhas inválidas são ignoradas e listadas no resumo."
        actions={
          <a className="text-sm text-brand" href="/api/v1/imports/sample">
            Baixar CSV de exemplo
          </a>
        }
      />
      <Card className="max-w-3xl">
        <p className="mb-4 text-sm text-muted">
          Colunas obrigatórias: data, descricao, categoria, tipo, valor, status. Opcionais: vencimento, observacao, cliente.
        </p>
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={(event) => {
            setFile(event.target.files?.[0] ?? null);
            setPreview(null);
            setResult(null);
          }}
        />
        <div className="mt-4 flex flex-wrap gap-2">
          <PrimaryButton disabled={!file || loading} onClick={() => void send("/api/v1/imports/preview")}>
            Validar arquivo
          </PrimaryButton>
          <PrimaryButton disabled={!file || loading} onClick={() => void send("/api/v1/imports/confirm")}>
            Importar válidos
          </PrimaryButton>
        </div>
        {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      </Card>

      {preview ? (
        <Card className="mt-4 max-w-3xl">
          <h2 className="text-sm font-medium">Pré-visualização</h2>
          <p className="mt-2 text-sm text-muted">
            {preview.total_rows} registros encontrados · {preview.valid_count} válidos · {preview.error_count} com erro
          </p>
          {preview.errors.length ? (
            <ul className="mt-3 space-y-1 text-sm text-expense">
              {preview.errors.map((item) => (
                <li key={`${item.row}-${item.message}`}>
                  Linha {item.row}: {item.message}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-income">Nenhum erro encontrado.</p>
          )}
        </Card>
      ) : null}

      {result ? (
        <Card className="mt-4 max-w-3xl border-teal-200 bg-teal-50">
          <h2 className="text-sm font-medium">Importação concluída</h2>
          <ul className="mt-2 text-sm text-ink">
            <li>{result.total_rows} registros encontrados</li>
            <li>{result.imported_count} importados</li>
            <li>{result.error_count} registros com erro</li>
          </ul>
        </Card>
      ) : null}
    </div>
  );
}
