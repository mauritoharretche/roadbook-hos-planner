const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "/api/v1").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function postJson<TResponse>(path: string, payload: unknown): Promise<TResponse> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError("Unable to reach the planning service. Check that the backend is running.", 0);
  }

  const body: unknown = await response.json().catch(() => null);
  if (!response.ok && response.status !== 422) {
    throw new ApiError(errorMessage(body), response.status, body);
  }
  return body as TResponse;
}

function errorMessage(body: unknown): string {
  if (isRecord(body)) {
    if (typeof body.detail === "string") return body.detail;
    const firstValue = Object.values(body)[0];
    if (Array.isArray(firstValue) && typeof firstValue[0] === "string") return firstValue[0];
  }
  return "The request could not be completed. Please review the trip details and try again.";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
