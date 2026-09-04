const API_URL = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function parseDetail(body: unknown): string {
  if (typeof body === "object" && body && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => (typeof item === "object" && item && "msg" in item ? String(item.msg) : String(item)))
        .join(" ");
    }
  }
  return "Não foi possível concluir a operação.";
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("ff_token");
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const isForm = options.body instanceof FormData;
  if (!isForm && !headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (response.status === 401) {
    localStorage.removeItem("ff_token");
    if (!path.includes("/auth/login")) {
      window.location.href = "/login";
    }
    throw new ApiError("Autenticação obrigatória.", 401);
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(parseDetail(body), response.status);
  }
  if (response.status === 204) return undefined as T;
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("text/csv") || contentType.includes("text/plain")) {
    return (await response.text()) as T;
  }
  return (await response.json()) as T;
}

export function query(params: Record<string, string | number | boolean | undefined | null>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  });
  const encoded = search.toString();
  return encoded ? `?${encoded}` : "";
}
