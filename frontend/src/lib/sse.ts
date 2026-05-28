import { SSEEvent } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Subscribe to Server-Sent Events from the backend.
 * Returns a cleanup function to abort the connection.
 */
export function subscribe(
  url: string,
  onEvent: (event: SSEEvent) => void,
  onDone?: () => void,
  onRetry?: (delay: number) => void,
): () => void {
  const controller = new AbortController();

  // Try native EventSource first, fall back to manual ReadStream
  if (typeof EventSource !== "undefined") {
    const es = new EventSource(url);
    es.onmessage = (e) => {
      try {
        const parsed: SSEEvent = JSON.parse(e.data);
        onEvent(parsed);
      } catch {
        // ignore parse errors
      }
    };
    es.onerror = () => {
      // EventSource auto-reconnects; notify caller of retry
      onRetry?.(0);
    };
    return () => {
      es.close();
      controller.abort();
    };
  }

  // Fallback: manual streaming with ReadableStream
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
              const parsed: SSEEvent = JSON.parse(line.slice(6));
              onEvent(parsed);
            } catch {
              // skip malformed
            }
          }
        }
      }

      onDone?.();
    })
    .catch((err) => {
      if (err.name !== "AbortError") console.error("SSE error:", err);
    });

  return () => controller.abort();
}
