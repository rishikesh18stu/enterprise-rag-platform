"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getToken } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) router.push("/login");
  }, [router]);

  const cards = [
    { title: "Chat", desc: "Ask questions about your documents", href: "/chat" },
    { title: "Upload", desc: "Add new documents to the knowledge base", href: "/upload" },
    { title: "Analytics", desc: "View usage and query statistics", href: "/analytics" },
    { title: "Settings", desc: "Manage your account", href: "/settings" },
  ];

  return (
    <div className="mx-auto max-w-4xl p-8">
      <h1 className="mb-8 text-2xl font-semibold text-gray-800">
        Enterprise RAG Dashboard
      </h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {cards.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm transition hover:shadow-md"
          >
            <h2 className="mb-1 text-lg font-medium text-gray-800">
              {card.title}
            </h2>
            <p className="text-sm text-gray-500">{card.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
