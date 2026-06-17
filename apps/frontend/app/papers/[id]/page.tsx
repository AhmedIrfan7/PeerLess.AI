"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getPaper, reparsePaper, PaperResponse, NetworkError, ApiError } from "@/lib/api";

const SEVERITY_COLOR: Record<string, string> = {
  info: "bg-slate-100 text-slate-600",
  low: "bg-amber-100 text-amber-700",
  medium: "bg-orange-100 text-orange-700",
  high: "bg-red-100 text-red-700",
};

export default function PaperPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [paper, setPaper] = useState<PaperResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    let stopped = false;
    async function poll() {
      while (!stopped) {
        try {
          const p = await getPaper(params.id);
          setPaper(p);
          if (p.status === "parsed" || p.status === "parse_failed") break;
        } catch (e) {
          if (e instanceof NetworkError) setError("Cannot reach backend.");
          else if (e instanceof ApiError) setError(e.message);
          break;
        }
        await new Promise((r) => setTimeout(r, 1000));
      }
    }
    poll();
    return () => { stopped = true; };
  }, [params.id]);

  async function handleAnalyze() {
    try {
      setAnalyzing(true);
      const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/v1/papers/${params.id}/analyze`, { method: "POST" });
      const data = await res.json();
      if (data.report_id) router.push(`/papers/${params.id}/report?rid=${data.report_id}`);
    } catch {
      setError("Failed to start analysis.");
      setAnalyzing(false);
    }
  }

  async function handleReparse() {
    try {
      await reparsePaper(params.id);
      setPaper(null);
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
    }
  }

  if (error) return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">{error}</div>
    </div>
  );

  if (!paper) return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div className="animate-pulse space-y-3">
        <div className="h-6 bg-slate-200 rounded w-3/4" />
        <div className="h-4 bg-slate-200 rounded w-1/2" />
        <div className="h-32 bg-slate-200 rounded" />
      </div>
      <p className="text-xs text-slate-400 text-center">Parsing paper…</p>
    </div>
  );

  const meta = paper.parsed_metadata;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <span className={`text-xs font-medium px-2 py-1 rounded ${
            paper.status === "parsed" ? "bg-green-100 text-green-700" :
            paper.status === "parse_failed" ? "bg-red-100 text-red-700" :
            "bg-amber-100 text-amber-700"
          }`}>{paper.status}</span>
          <span className="text-xs text-slate-400">{paper.original_filename}</span>
        </div>

        {meta?.title && <h1 className="text-xl font-semibold text-slate-800">{meta.title}</h1>}
        {meta?.authors && meta.authors.length > 0 && (
          <p className="text-sm text-slate-600">{meta.authors.join(", ")}</p>
        )}
        {meta?.abstract && (
          <p className="text-sm text-slate-600 leading-relaxed line-clamp-4">{meta.abstract}</p>
        )}
        <div className="flex gap-4 text-xs text-slate-400">
          {meta?.page_count && <span>{meta.page_count} pages</span>}
          {meta?.language && <span>Language: {meta.language}</span>}
          {meta?.doi && <span>DOI: {meta.doi}</span>}
        </div>

        {paper.status === "parse_failed" && (
          <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700 space-y-2">
            <p>{paper.error_message}</p>
            <button onClick={handleReparse} className="text-xs underline">Try Again</button>
          </div>
        )}

        {paper.status === "parsed" && (
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="w-full py-2.5 bg-blue-600 text-white rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {analyzing ? "Starting analysis…" : "Run Integrity Analysis"}
          </button>
        )}
      </div>
    </div>
  );
}
