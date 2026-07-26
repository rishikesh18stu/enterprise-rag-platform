const API_BASE = "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export async function sendChatMessage(question: string, sessionId: string | null) {
  const token = getToken();

  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question, session_id: sessionId }),
  });

  if (res.status === 401) {
    localStorage.removeItem("access_token");
    window.location.href = "/login";
    throw new Error("Session expired.");
  }

  if (!res.ok) {
    throw new Error("Chat request failed.");
  }

  return res.json() as Promise<{
    answer: string;
    citations: string[];
    session_id: string;
  }>;
}
export async function streamChatMessage(
  question: string,
  sessionId: string | null,
  onToken: (token: string) => void,
  onDone: (citations: string[], sessionId: string) => void
) {
  const token = getToken();

  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question, session_id: sessionId }),
  });

  if (!res.ok || !res.body) throw new Error("Stream failed.");

  // The browser doesn't have a built-in fetch+SSE combo (EventSource only
  // supports GET requests, and we need POST with an auth header) -- so we
  // read the raw byte stream manually and parse SSE 'data:' lines ourselves.
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || ""; // keep any incomplete trailing chunk for next read

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = JSON.parse(line.slice(6));

      if (data.done) {
        onDone(data.citations, data.session_id);
      } else if (data.token) {
        onToken(data.token);
      }
    }
  }
}
