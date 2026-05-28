const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(error.error || `API error: ${res.status}`);
  }

  return res.json();
}

// ---------------------------------------------------------------------------
// Matches
// ---------------------------------------------------------------------------

export const matchesApi = {
  list: () => request<{ matches: any[]; total: number }>(\"/api/matches\"),
  get: (id: string) => request<any>(`/api/matches/${id}`),
  create: (data: any) => request<any>(\"/api/matches\", { method: \"POST\", body: JSON.stringify(data) }),
  getStatus: (id: string) => request<any>(`/api/matches/${id}/status`),
  makeMove: (matchId: string, move: { move_san: string }) =>
    request<any>(`/api/matches/${matchId}/moves`, {
      method: "POST",
      body: JSON.stringify(move),
    }),
};

// ---------------------------------------------------------------------------
// Models
// ---------------------------------------------------------------------------

export const modelsApi = {
  list: () => request<{ models: any[]; total: number }>(\"/api/models\"),
  get: (id: string) => request<any>(`/api/models/${id}`),
  create: (data: any) => request<any>(\"/api/models\", { method: \"POST\", body: JSON.stringify(data) }),
};

// ---------------------------------------------------------------------------
// Benchmarks
// ---------------------------------------------------------------------------

export const benchmarksApi = {
  get: (modelId: string) => request<any>(`/api/benchmarks/${modelId}`),
  rankings: () => request<any>(\"/api/benchmarks/rankings\"),
  history: (modelId: string) => request<any>(`/api/benchmarks/history?model_id=${modelId}`),
};

// ---------------------------------------------------------------------------
// SSE helper — subscribe to match updates
// ---------------------------------------------------------------------------

export function subscribeToMatch(
  matchId: string,
  onEvent: (event: { type: string; data: any }) => void,
  onDone?: () => void,
): () => void {
  const url = `${API_BASE}/api/matches/${matchId}/stream`;

  const controller = new AbortController();

  fetch(url, { signal: controller.signal })
    .then(async (res) => {
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              onEvent({ type: data.event || "unknown", data: data.data || data });
            } catch {
              // skip malformed events
            }
          }
        }
      }

      onDone?.();
    })
    .catch((err) => {
      if (err.name !== "AbortError") console.error("SSE connection failed:", err);
    });

  return () => controller.abort();
}
