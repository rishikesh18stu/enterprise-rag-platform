"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api";

export default function AnalyticsPage() {
  const [stats, setStats] = useState<{ total_sessions: number; total_messages: number } | null>(null);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }

    fetch("http://localhost:8000/chat/stats", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load stats.");
        return res.json();
      })
      .then(setStats)
      .catch(() => setError("Could not load analytics."));
  }, [router]);

  return (
    <div className="mx-auto max-w-2xl p-8">
      <h1 className="mb-6 text-2xl font-semibold text-gray-800">Analytics</h1>

      {error && <p className="text-red-600">{error}</p>}

      {stats && (
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-500">Active Sessions</p>
            <p className="text-3xl font-semibold text-gray-800">
              {stats.total_sessions}
            </p>
          </div>
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-500">Total Messages</p>
            <p className="text-3xl font-semibold text-gray-800">
              {stats.total_messages}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}