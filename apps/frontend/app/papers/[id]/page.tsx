"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getPaper, analyzePaper, reparsePaper, PaperResponse, NetworkError, ApiError } from "@/lib/api";

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
      const { report_id } = await analyzePaper(params.id);
      router.push(`/papers/${params.id}/report?rid=${report_id}`);
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
      else setError("Failed to start analysis.");
      setAnalyzing(false);
    }
  }

  async function handleReparse() {
    try {
      setPaper(null);
      await reparsePaper(params.id);
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
    }
  }

  if (error) return (
    <div className="max-w-2xl mx-auto space-y-4">
      <BackLink />
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">{error}</div>
    </div>
  );

  if (!paper) return (
    <div className="max-w-2xl mx-auto space-y-4">
      <BackLink />
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
      <BackLink />

      <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <span className={`text-xs font-medium px-2 py-1 rounded ${
            paper.status === "parsed" ? "bg-green-100 text-green-700" :
            paper.status === "parse_failed" ? "bg-red-100 text-red-700" :
            "bg-amber-100 text-amber-700"
          }`}>{paper.status}</span>
          <span className="text-xs text-slate-400 truncate max-w-xs">{paper.original_filename}</span>
        </div>

        {meta?.title && <h1 className="text-xl font-semibold text-slate-800">{meta.title}</h1>}
        {meta?.authors && meta.authors.length > 0 && (
          <p className="text-sm text-slate-600">{meta.authors.join(", ")}</p>
        )}
        {meta?.abstract && (
          <p className="text-sm text-slate-600 leading-relaxed line-clamp-4">{meta.abstract}</p>
        )}
        <div className="flex flex-wrap gap-4 text-xs text-slate-400">
          {meta?.page_count && <span>{meta.page_count} page{meta.page_count !== 1 ? "s" : ""}</span>}
          {meta?.language && <span>Language: {meta.language}</span>}
          {meta?.doi && <span>DOI: {meta.doi}</span>}
          <span>{(paper.byte_size / 1024).toFixed(1)} KB</span>
        </div>

        {paper.status === "parse_failed" && (
          <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700 space-y-2">
            <p>{paper.error_message || "Parsing failed."}</p>
            <button onClick={handleReparse} className="text-xs underline">Try again</button>
          </div>
        )}

        {(paper.status === "parsing" || paper.status === "uploaded") && (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            Parsing…
          </div>
        )}

        {paper.status === "parsed" && (
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="w-full py-2.5 bg-blue-600 text-white rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {analyzing ? "Starting analysis…" : "Run Integrity Analysis"}
          </button>
        )}
      </div>
    </div>
  );
}

function BackLink() {
  return (
    <Link href="/" className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800">
      <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd"/>
      </svg>
      Upload another paper
    </Link>
  );
}
