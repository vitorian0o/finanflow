export type TransactionType = "income" | "expense";
export type TransactionStatus = "paid" | "pending" | "cancelled";

export type User = {
  id: string;
  name: string;
  email: string;
  company: { id: string; name: string };
};

export type Category = {
  id: string;
  name: string;
  type: TransactionType;
  is_default: boolean;
};

export type Transaction = {
  id: string;
  date: string;
  description: string;
  type: TransactionType;
  category_id: string;
  category_name: string;
  amount: number;
  status: TransactionStatus;
  due_date: string | null;
  paid_at: string | null;
  party_name: string | null;
  notes: string | null;
};

export type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type KpiPoint = {
  label: string;
  income: number;
  expense: number;
  net: number;
  balance?: number | null;
};

export type Insight = {
  type: string;
  title: string;
  message: string;
};

export type Dashboard = {
  period: string;
  date_from: string;
  date_to: string;
  total_income: number;
  total_expense: number;
  profit: number;
  margin: number;
  payable_total: number;
  receivable_total: number;
  current_balance: number;
  income_vs_expense: KpiPoint[];
  balance_evolution: KpiPoint[];
  income_by_category: { name: string; amount: number }[];
  expense_by_category: { name: string; amount: number }[];
  monthly_cash_flow: KpiPoint[];
  insights: Insight[];
};

export type AccountSummary = {
  overdue_count: number;
  overdue_amount: number;
  due_today_count: number;
  due_today_amount: number;
  due_soon_count: number;
  due_soon_amount: number;
  expected_inflow: number;
  expected_outflow: number;
};

export type ImportPreview = {
  filename: string;
  total_rows: number;
  valid_count: number;
  error_count: number;
  errors: { row: number; field: string | null; message: string; raw: string | null }[];
  valid_sample: Record<string, unknown>[];
};

export type ImportResult = ImportPreview & { id: string; imported_count: number };

export type Report = {
  company_name: string;
  date_from: string;
  date_to: string;
  total_income: number;
  total_expense: number;
  profit: number;
  margin: number;
  current_balance: number;
  overdue_payables: number;
  overdue_receivables: number;
  upcoming_payables: number;
  upcoming_receivables: number;
  categories: { name: string; type: string; amount: number }[];
  monthly_evolution: KpiPoint[];
};

export type NotificationItem = {
  id: string;
  type: string;
  title: string;
  message: string;
  channel: string;
  is_read: boolean;
  created_at: string;
};
