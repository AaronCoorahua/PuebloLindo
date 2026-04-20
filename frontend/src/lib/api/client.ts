const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function extractErrorDetail(payload: unknown): string | undefined {
  if (!payload || typeof payload !== "object") {
    return undefined;
  }

  const maybeDetail = (payload as { detail?: unknown }).detail;
  if (typeof maybeDetail === "string" && maybeDetail.trim()) {
    return maybeDetail;
  }

  if (Array.isArray(maybeDetail)) {
    const messages = maybeDetail
      .map((entry) => {
        if (!entry || typeof entry !== "object") {
          return undefined;
        }
        const msg = (entry as { msg?: unknown }).msg;
        if (typeof msg === "string" && msg.trim()) {
          return msg;
        }
        return undefined;
      })
      .filter((value): value is string => Boolean(value));

    if (messages.length > 0) {
      return messages.join("; ");
    }
  }

  return undefined;
}

export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = (await response.json()) as unknown;
      detail = extractErrorDetail(payload) ?? detail;
    } catch {
      // Keep status text when response is not JSON.
    }

    throw new Error(`API error ${response.status}: ${detail}`);
  }

  return (await response.json()) as T;
}

export async function postJson<TResponse, TBody = unknown>(path: string, body?: TBody): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = (await response.json()) as unknown;
      detail = extractErrorDetail(payload) ?? detail;
    } catch {
      // Keep status text when response is not JSON.
    }

    throw new Error(`API error ${response.status}: ${detail}`);
  }

  return (await response.json()) as TResponse;
}
