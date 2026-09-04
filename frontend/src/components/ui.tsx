import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Bell,
  Building2,
  LayoutDashboard,
  LogOut,
  Menu,
  Receipt,
  Settings,
  Tags,
  Upload,
  Wallet,
  X,
} from "lucide-react";
import { api } from "../api/client";
import type { NotificationItem } from "../api/types";
import { useAuth } from "../auth/AuthContext";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/lancamentos", label: "Lançamentos", icon: Receipt },
  { to: "/contas/pagar", label: "Contas a pagar", icon: Wallet },
  { to: "/contas/receber", label: "Contas a receber", icon: Wallet },
  { to: "/categorias", label: "Categorias", icon: Tags },
  { to: "/importar", label: "Importar CSV", icon: Upload },
  { to: "/relatorios", label: "Relatórios", icon: Building2 },
  { to: "/configuracoes", label: "Empresa", icon: Settings },
];

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [bellOpen, setBellOpen] = useState(false);
  const [notes, setNotes] = useState<NotificationItem[]>([]);

  const loadNotes = async () => {
    try {
      setNotes(await api<NotificationItem[]>("/api/v1/notifications"));
    } catch {
      setNotes([]);
    }
  };

  useEffect(() => {
    void loadNotes();
  }, []);

  const unread = notes.filter((item) => !item.is_read).length;

  return (
    <div className="min-h-screen bg-canvas text-ink">
      {open ? (
        <button className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={() => setOpen(false)} aria-label="Fechar menu" />
      ) : null}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-sidebar text-slate-200 flex flex-col transition-transform lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}
      >
        <div className="flex items-center justify-between px-5 py-5 border-b border-white/10">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-teal-200/80">FinanFlow</p>
            <p className="mt-1 text-sm text-slate-400 truncate">{user?.company.name}</p>
          </div>
          <button className="lg:hidden text-slate-400" onClick={() => setOpen(false)}>
            <X size={18} />
          </button>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                  isActive ? "bg-white/10 text-white" : "text-slate-400 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              <item.icon size={16} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 py-4 border-t border-white/10">
          <p className="text-sm text-white truncate">{user?.name}</p>
          <p className="text-xs text-slate-500 truncate">{user?.email}</p>
          <button
            className="mt-3 flex items-center gap-2 text-xs text-slate-400 hover:text-white"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            <LogOut size={14} />
            Sair
          </button>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-line bg-white/90 px-4 py-3 backdrop-blur">
          <button className="lg:hidden text-ink" onClick={() => setOpen(true)} aria-label="Abrir menu">
            <Menu size={20} />
          </button>
          <p className="hidden sm:block text-sm text-muted">Gestão financeira para pequenas empresas</p>
          <div className="relative ml-auto">
            <button
              className="relative rounded-full border border-line p-2 text-muted hover:text-ink"
              onClick={() => {
                setBellOpen((value) => !value);
                void loadNotes();
              }}
              aria-label="Notificações"
            >
              <Bell size={16} />
              {unread ? (
                <span className="absolute -right-1 -top-1 h-4 min-w-4 rounded-full bg-brand px-1 text-[10px] text-white">
                  {unread}
                </span>
              ) : null}
            </button>
            {bellOpen ? (
              <div className="absolute right-0 mt-2 w-80 rounded-xl border border-line bg-white p-3 shadow-none">
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-sm font-medium">Alertas</p>
                  <button
                    className="text-xs text-brand"
                    onClick={async () => {
                      await api("/api/v1/notifications/read-all", { method: "POST" });
                      void loadNotes();
                    }}
                  >
                    Marcar lidas
                  </button>
                </div>
                <div className="max-h-72 space-y-2 overflow-y-auto">
                  {notes.length === 0 ? <p className="text-sm text-muted">Nenhum alerta no momento.</p> : null}
                  {notes.map((item) => (
                    <div key={item.id} className={`rounded-lg p-2 ${item.is_read ? "bg-canvas" : "bg-teal-50"}`}>
                      <p className="text-sm font-medium">{item.title}</p>
                      <p className="text-xs text-muted">{item.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </header>
        <main className="p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {subtitle ? <p className="mt-1 text-sm text-muted">{subtitle}</p> : null}
      </div>
      {actions}
    </div>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-2xl border border-line bg-white p-5 ${className}`}>{children}</section>;
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="mb-1.5 block text-muted">{label}</span>
      {children}
    </label>
  );
}

export const inputClass =
  "w-full rounded-lg border border-line bg-white px-3 py-2 text-sm outline-none focus:border-brand";

export function PrimaryButton({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-60 ${props.className ?? ""}`}
    >
      {children}
    </button>
  );
}

export function GhostButton({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center rounded-lg border border-line px-4 py-2 text-sm hover:bg-canvas ${props.className ?? ""}`}
    >
      {children}
    </button>
  );
}

export function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4">
      <div className="max-h-[92vh] w-full max-w-lg overflow-y-auto rounded-t-2xl bg-white p-5 sm:rounded-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button onClick={onClose} aria-label="Fechar">
            <X size={18} />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    paid: "bg-emerald-50 text-emerald-800",
    pending: "bg-amber-50 text-amber-800",
    cancelled: "bg-slate-100 text-slate-600",
  };
  const label = status === "paid" ? "Pago" : status === "pending" ? "Pendente" : "Cancelado";
  return <span className={`rounded-full px-2.5 py-0.5 text-xs ${map[status] ?? map.cancelled}`}>{label}</span>;
}

export function AuthShell({
  title,
  subtitle,
  children,
  onSubmit,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  onSubmit: (event: FormEvent) => void;
}) {
  return (
    <div className="min-h-screen bg-sidebar flex items-center justify-center p-4">
      <form onSubmit={onSubmit} className="w-full max-w-md rounded-2xl bg-white p-8">
        <p className="text-xs uppercase tracking-[0.2em] text-brand">FinanFlow</p>
        <h1 className="mt-2 text-2xl font-semibold">{title}</h1>
        <p className="mt-1 mb-6 text-sm text-muted">{subtitle}</p>
        {children}
      </form>
    </div>
  );
}
