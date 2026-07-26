"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken, sendChatMessage, streamChatMessage } from "@/lib/api";
type Message = {
  role: "user" | "assistant";
  content: string;
  citations?: string[];
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  // Route guard: if there's no token, don't even render the chat --
  // send the user back to login immediately.
  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
    }
  }, [router]);

  async function handleSend() {
  if (!input.trim()) return;

  const userMessage: Message = { role: "user", content: input };
  setMessages((prev) => [...prev, userMessage, { role: "assistant", content: "" }]);
  setInput("");
  setLoading(true);

  try {
    await streamChatMessage(
      input,
      sessionId,
      (token) => {
  setMessages((prev) => {
    const last = prev[prev.length - 1];
    const updatedLast = { ...last, content: last.content + token };  // new object, not mutated
    return [...prev.slice(0, -1), updatedLast];
  });
},
      (citations, newSessionId) => {
        setSessionId(newSessionId);
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].citations = citations;
          return updated;
        });
        setLoading(false);
      }
    );
  } catch (err) {
    setLoading(false);
  }
}

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`mb-4 flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-lg rounded-lg p-3 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-800 shadow"
              }`}
            >
              <p>{msg.content}</p>
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-2 border-t border-gray-200 pt-2 text-xs text-gray-500">
                  Sources: {msg.citations.join(", ")}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && <p className="text-sm text-gray-400">Thinking...</p>}
      </div>

      <div className="border-t bg-white p-4">
        <div className="flex gap-2">
          <input
            className="flex-1 rounded border border-gray-300 p-3"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask a question..."
          />
          <button
            onClick={handleSend}
            disabled={loading}
            className="rounded bg-blue-600 px-6 py-3 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
