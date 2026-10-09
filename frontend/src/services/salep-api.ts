const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
).replace(/\/$/, "");

export class SalepApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "SalepApiError";
    this.status = status;
  }
}

export async function salepApi<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
      credentials: "include",
      cache: "no-store",
    });
  } catch {
    throw new SalepApiError(
      `Tidak dapat terhubung ke backend SALEP (${API_BASE_URL}). Pastikan backend sedang berjalan.`,
      0,
    );
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message =
      payload?.detail || payload?.message || `Request gagal (${response.status})`;
    throw new SalepApiError(message, response.status);
  }

  return payload as T;
}
