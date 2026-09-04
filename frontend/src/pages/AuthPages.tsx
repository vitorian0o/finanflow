import { useState, type FormEvent } from "react";
import { Link, Navigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { AuthShell, Field, PrimaryButton, inputClass } from "../components/ui";

export function LoginPage() {
  const { token, setToken } = useAuth();
  const [email, setEmail] = useState("demo@finanflow.app");
  const [password, setPassword] = useState("demo12345");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (token) return <Navigate to="/" replace />;

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await api<{ access_token: string }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(result.access_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title="Entrar" subtitle="Acesse o painel financeiro da sua empresa." onSubmit={onSubmit}>
      <div className="space-y-4">
        <Field label="E-mail">
          <input className={inputClass} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </Field>
        <Field label="Senha">
          <input className={inputClass} type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </Field>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <PrimaryButton type="submit" disabled={loading} className="w-full">
          {loading ? "Entrando..." : "Entrar"}
        </PrimaryButton>
        <p className="text-center text-sm text-muted">
          Não tem conta?{" "}
          <Link to="/cadastro" className="text-brand">
            Criar conta
          </Link>
        </p>
        <p className="text-center text-xs text-muted">Demo: demo@finanflow.app / demo12345</p>
      </div>
    </AuthShell>
  );
}

export function RegisterPage() {
  const { token, setToken } = useAuth();
  const [name, setName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (token) return <Navigate to="/" replace />;

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await api<{ access_token: string }>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({ name, email, password, company_name: companyName }),
      });
      setToken(result.access_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no cadastro");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title="Criar conta" subtitle="Comece a organizar o caixa da sua empresa." onSubmit={onSubmit}>
      <div className="space-y-4">
        <Field label="Seu nome">
          <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} required />
        </Field>
        <Field label="Nome da empresa">
          <input className={inputClass} value={companyName} onChange={(e) => setCompanyName(e.target.value)} required />
        </Field>
        <Field label="E-mail">
          <input className={inputClass} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </Field>
        <Field label="Senha">
          <input className={inputClass} type="password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} required />
        </Field>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <PrimaryButton type="submit" disabled={loading} className="w-full">
          {loading ? "Criando..." : "Criar conta"}
        </PrimaryButton>
        <p className="text-center text-sm text-muted">
          Já tem acesso?{" "}
          <Link to="/login" className="text-brand">
            Entrar
          </Link>
        </p>
      </div>
    </AuthShell>
  );
}
