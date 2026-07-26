"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api";
export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const router = useRouter();
  useEffect(() => {
  if (!getToken()) {
    router.push("/login");
  }
}, [router]);
  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setStatus("");

    // multipart/form-data -- FormData handles the encoding automatically;
    // note we do NOT manually set Content-Type here, the browser sets the
    // correct multipart boundary header itself.
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/documents/upload", {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed.");
      }

      const data = await res.json();
      setStatus(`✅ ${data.filename} uploaded and indexed.`);
      setFile(null);
    } catch (err) {
      setStatus(`❌ ${(err as Error).message}`);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl p-8">
      <h1 className="mb-6 text-2xl font-semibold text-gray-800">
        Upload a Document
      </h1>

      <div className="rounded-lg border-2 border-dashed border-gray-300 p-8 text-center">
        <input
          type="file"
          accept=".pdf,.docx,.pptx,.xlsx,.txt,.md"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="mb-4"
        />
        {file && <p className="text-sm text-gray-600">{file.name}</p>}
      </div>

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="mt-4 w-full rounded bg-blue-600 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {uploading ? "Uploading..." : "Upload"}
      </button>

      {status && <p className="mt-4 text-sm">{status}</p>}

      <p className="mt-6 text-xs text-gray-400">
        Note: newly uploaded documents may require a backend restart before
        they appear in chat answers (known current limitation).
      </p>
    </div>
  );
}
