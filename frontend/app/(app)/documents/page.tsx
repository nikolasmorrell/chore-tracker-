"use client";
import { useRef, useState } from "react";
import { api } from "@/lib/api";
import { useApi, formatBytes, formatDate } from "@/lib/hooks";
import type {
  CursorPage,
  DocumentItem,
  DocumentUploadResponse,
} from "@/lib/types";

async function sha256Hex(file: File): Promise<string> {
  const buf = await file.arrayBuffer();
  const hash = await crypto.subtle.digest("SHA-256", buf);
  return Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export default function DocumentsPage() {
  const { data, isLoading, mutate } =
    useApi<CursorPage<DocumentItem>>("/api/v1/documents?limit=100");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function onUpload(file: File) {
    setBusy(true);
    setErr(null);
    try {
      const sha256 = await sha256Hex(file);
      const presign = await api.post<DocumentUploadResponse>(
        "/api/v1/documents",
        {
          filename: file.name,
          mime_type: file.type || "application/octet-stream",
          size_bytes: file.size,
          sha256,
          doc_type: "other",
        },
      );
      const form = new FormData();
      for (const [k, v] of Object.entries(presign.fields)) form.append(k, v);
      form.append("Content-Type", file.type || "application/octet-stream");
      form.append("file", file);
      const uploadRes = await fetch(presign.upload_url, {
        method: "POST",
        body: form,
      });
      if (!uploadRes.ok) throw new Error(`Upload failed (${uploadRes.status})`);
      await api.post(`/api/v1/documents/${presign.document_id}/confirm`);
      await mutate();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Documents</h1>
        <label className="inline-flex cursor-pointer items-center rounded-md bg-slate-900 px-4 py-2 text-sm text-white">
          {busy ? "Uploading…" : "Upload document"}
          <input
            ref={fileRef}
            type="file"
            className="hidden"
            disabled={busy}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onUpload(f);
            }}
          />
        </label>
      </div>
      {err ? <p className="mt-2 text-sm text-red-600">{err}</p> : null}
      <div className="mt-6 rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-2">Filename</th>
              <th className="px-4 py-2">Type</th>
              <th className="px-4 py-2">Size</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Uploaded</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td className="px-4 py-4 text-slate-500" colSpan={5}>
                  Loading…
                </td>
              </tr>
            ) : data && data.items.length ? (
              data.items.map((d) => (
                <tr key={d.id} className="border-t">
                  <td className="px-4 py-2">{d.original_filename}</td>
                  <td className="px-4 py-2">{d.doc_type}</td>
                  <td className="px-4 py-2">{formatBytes(d.size_bytes)}</td>
                  <td className="px-4 py-2">
                    <StatusBadge status={d.status} />
                  </td>
                  <td className="px-4 py-2 text-slate-500">
                    {formatDate(d.created_at)}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td className="px-4 py-4 text-slate-500" colSpan={5}>
                  No documents yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}

function StatusBadge({ status }: { status: DocumentItem["status"] }) {
  const tone =
    status === "ready"
      ? "bg-emerald-100 text-emerald-700"
      : status === "failed"
        ? "bg-red-100 text-red-700"
        : "bg-slate-100 text-slate-700";
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs ${tone}`}>{status}</span>
  );
}
