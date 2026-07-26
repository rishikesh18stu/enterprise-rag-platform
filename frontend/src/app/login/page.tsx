"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    // OAuth2PasswordRequestForm on the backend expects form-encoded data,
    // not JSON -- so we build a URLSearchParams body, matching what
    // Swagger's Authorize dialog sent when we tested this manually.
    const body = new URLSearchParams();
    body.append("username", username);
    body.append("password", password);

    try {
      const res = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });

      if (!res.ok) {
        throw new Error("Invalid username or password.");
      }

      const data = await res.json();

      // Storing the token in memory (React state) would be lost on refresh --
      // localStorage persists across page reloads, which is what we want
      // for "stay logged in" behavior. (Note: for production, httpOnly
      // cookies are more secure against XSS -- localStorage is the
      // pragmatic choice for this learning project.)
      localStorage.setItem("access_token", data.access_token);

      router.push("/chat");
    } catch (err) {
      setError("Login failed. Check your username and password.");
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm rounded-lg bg-white p-8 shadow-md"
      >
        <h1 className="mb-6 text-2xl font-semibold text-gray-800">Sign in</h1>

        {error && (
          <p className="mb-4 rounded bg-red-50 p-2 text-sm text-red-600">
            {error}
          </p>
        )}

        <label className="mb-1 block text-sm font-medium text-gray-700">
          Username
        </label>
        <input
          className="mb-4 w-full rounded border border-gray-300 p-2"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />

        <label className="mb-1 block text-sm font-medium text-gray-700">
          Password
        </label>
        <input
          type="password"
          className="mb-6 w-full rounded border border-gray-300 p-2"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button
          type="submit"
          className="w-full rounded bg-blue-600 py-2 font-medium text-white hover:bg-blue-700"
        >
          Sign in
        </button>
      </form>
    </div>
  );
}
