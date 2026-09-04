import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { AppLayout } from "./components/ui";
import { AccountsPage } from "./pages/AccountsPage";
import { LoginPage, RegisterPage } from "./pages/AuthPages";
import { CategoriesPage } from "./pages/CategoriesPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ImportPage } from "./pages/ImportPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { TransactionsPage } from "./pages/TransactionsPage";

function Protected() {
  const { token, loading } = useAuth();
  if (loading) {
    return <div className="flex min-h-screen items-center justify-center text-muted">Carregando...</div>;
  }
  if (!token) return <Navigate to="/login" replace />;
  return <Outlet />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/cadastro" element={<RegisterPage />} />
      <Route element={<Protected />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/lancamentos" element={<TransactionsPage />} />
          <Route path="/contas/pagar" element={<AccountsPage kind="payable" />} />
          <Route path="/contas/receber" element={<AccountsPage kind="receivable" />} />
          <Route path="/categorias" element={<CategoriesPage />} />
          <Route path="/importar" element={<ImportPage />} />
          <Route path="/relatorios" element={<ReportsPage />} />
          <Route path="/configuracoes" element={<SettingsPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
