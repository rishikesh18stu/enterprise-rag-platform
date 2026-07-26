"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api";

export default function SettingsPage() {
  const [profile, setProfile] = useState<{ username: string; role: string } | null>(null);
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }

    fetch("http://localhost:8000/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then(setProfile)
      .catch(() => {});
  }, [router]);

  function handleLogout() {
    localStorage.removeItem("access_token");
    router.push("/login");
  }

  return (
    <div className="mx-auto max-w-md p-8">
      <h1 className="mb-6 text-2xl font-semibold text-gray-800">Settings</h1>

      {profile && (
        <div className="mb-6 rounded-lg bg-white p-6 shadow-sm">
          <p className="text-sm text-gray-500">Username</p>
          <p className="mb-3 text-lg text-gray-800">{profile.username}</p>
          <p className="text-sm text-gray-500">Role</p>
          <p className="text-lg capitalize text-gray-800">{profile.role}</p>
        </div>
      )}

      <button
        onClick={handleLogout}
        className="w-full rounded bg-red-600 py-2 font-medium text-white hover:bg-red-700"
      >
        Log out
      </button>
    </div>
  );
}
