"use client";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { getReport, reviewFinding, ReportResponse, FindingResponse, NetworkError, ApiError } from "@/lib/api";
import { DISCLAIMER_SHORT, AI_SUMMARY_NOTICE } from "@/lib/legal";

const SEVERITY_STYLES: Record<string, { badge: string; border: string }> = {
  info: { badge: "bg-slate-100 text-slate-600", border: "border-slate-200" },
  low: { badge: "bg-amber-100 text-amber-700", border: "border-amber-200" },
  medium: { badge: "bg-orange-100 text-orange-700", border: "border-orange-200" },
  high: { badge: "bg-red-100 text-red-700", border: "border-red-200" },
};

const CONFIDENCE_STYLES: Record<string, string> = {
  low: "text-red-600",
  medium: "text-amber-600",
  high: "text-green-600",
};

function FindingCard({ finding, onReview }: { finding: FindingResponse; onReview: (id: string, action: "approve" | "reject", note?: string) => void }) {
  const [note, setNote] = useState("");
  const [expanded, setExpanded] = useState(false);
  const styles = SEVERITY_STYLES[finding.severity] || SEVERITY_STYLES.info;

  return (
    <div className={`bg-white border rounded-xl p-4 space-y-3 ${styles.border}`}>
      <div className="flex items-start gap-3">
        <div className="flex-1 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`text-xs font-medium px-2 py-0.5 rounded ${styles.badge}`}>
              {finding.severity}
            </span>
            <span className="text-xs text-slate-400 capitalize">{finding.agent.replace(/_/g, " ")}</span>
            {finding.status !== "draft" && (
              <span className={`text-xs font-medium px-2 py-0.5 rounded ${finding.status === "approved" ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"}`}>
                {finding.status}
              </span>
            )}
          </div>
          <p className="font-medium text-slate-800 text-sm">{finding.title}</p>
        </div>
        <span className="text-xs text-slate-400 shrink-0">{Math.round(finding.confidence * 100)}% conf.</span>
      </div>

      <p className="text-sm text-slate-600 leading-relaxed">{finding.summary}</p>

      {finding.evidence && finding.evidence.length > 0 && (
        <button onClick={() => setExpanded(!expanded)} className="text-xs text-blue-600 hover:underline">
          {expanded ? "Hide evidence" : `Show ${finding.evidence.length} evidence item(s)`}
        </button>
      )}

      {expanded && (
        <div className="bg-slate-50 rounded p-3 text-xs text-slate-600 font-mono space-y-1">
          {finding.evidence.map((e, i) => (
            <div key={i}><span className="text-slate-400">{e.kind}:</span> {JSON.stringify(e.content)}</div>
          ))}
        </div>
      )}

      {finding.requires_human_review && finding.status === "draft" && (
        <div className="border-t border-slate-100 pt-3 space-y-2">
          <p className="text-xs text-slate-500">This finding requires expert review before it can be shared.</p>
          <textarea
            className="w-full border border-slate-200 rounded p-2 text-xs resize-none focus:outline-none focus:ring-1 focus:ring-blue-400"
            placeholder="Optional reviewer note…"
            rows={2}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
          <div className="flex gap-2">
            <button
              onClick={() => onReview(finding.id, "approve", note || undefined)}
              className="px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded hover:bg-green-700"
            >
              Approve
            </button>
            <button
              onClick={() => onReview(finding.id, "reject", note || undefined)}
              className="px-3 py-1.5 bg-slate-200 text-slate-700 text-xs font-medium rounded hover:bg-slate-300"
            >
              Reject
            </button>
          </div>
        </div>
      )}

      {finding.reviewer_note && (
        <p className="text-xs text-slate-400 italic">Note: {finding.reviewer_note}</p>
      )}
    </div>
  );
}

export default function ReportPage({ params }: { params: { id: string } }) {
  const searchParams = useSearchParams();
  const reportId = searchParams.get("rid");
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!reportId) { setError("No report ID provided."); return; }
    let stopped = false;
    async function poll() {
      while (!stopped) {
        try {
          const r = await getReport(reportId!);
          setReport(r);
          if (r.status === "complete" || r.status === "failed") break;
        } catch (e) {
          if (e instanceof NetworkError) setError("Cannot reach backend.");
          else if (e instanceof ApiError) setError(e.message);
          break;
        }
        await new Promise((res) => setTimeout(res, 2000));
      }
    }
    poll();
    return () => { stopped = true; };
  }, [reportId]);

  async function handleReview(findingId: string, action: "approve" | "reject", note?: string) {
    try {
      await reviewFinding(findingId, action, note);
      if (reportId) {
        const r = await getReport(reportId);
        setReport(r);
      }
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
    }
  }

  if (error) return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">{error}</div>
    </div>
  );

  if (!report || report.status === "pending" || report.status === "partial") return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div className="bg-white border border-slate-200 rounded-xl p-6 text-center space-y-3">
        <div className="flex justify-center">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
        <p className="text-sm text-slate-600">Analysis in progress. Agents are running…</p>
        {report?.status === "partial" && (
          <p className="text-xs text-slate-400">Some agents have completed. Waiting for remaining results…</p>
        )}
      </div>
    </div>
  );

  if (report.status === "failed") return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 space-y-2">
        <p className="font-medium text-red-700">Analysis failed</p>
        <p className="text-sm text-red-600">{report.error || "All agents failed."}</p>
      </div>
    </div>
  );

  const bySeverity = (s: string) => report.findings.filter((f) => f.severity === s);
  const agentSummary = Array.from(new Set(report.findings.map((f) => f.agent)));

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <h1 className="text-lg font-semibold text-slate-800">Analysis Report</h1>
          <span className={`text-sm font-medium px-3 py-1 rounded-full ${
            report.overall_confidence === "high" ? "bg-green-100 text-green-700" :
            report.overall_confidence === "medium" ? "bg-amber-100 text-amber-700" :
            "bg-red-100 text-red-700"
          }`}>
            Overall confidence: {report.overall_confidence}
          </span>
        </div>
        <div className="flex flex-wrap gap-3 text-xs text-slate-400">
          <span>{report.findings.length} finding(s)</span>
          {agentSummary.map((a) => <span key={a} className="capitalize">{a.replace(/_/g, " ")}</span>)}
          {report.completed_at && (
            <span>Completed {new Date(report.completed_at).toLocaleString()}</span>
          )}
        </div>
        <div className="flex gap-4 text-xs">
          {(["high", "medium", "low", "info"] as const).map((s) => {
            const count = bySeverity(s).length;
            if (!count) return null;
            const styles = SEVERITY_STYLES[s];
            return (
              <span key={s} className={`px-2 py-0.5 rounded font-medium ${styles.badge}`}>
                {count} {s}
              </span>
            );
          })}
        </div>
        <p className="text-xs text-amber-700 bg-amber-50 rounded p-2">{DISCLAIMER_SHORT}</p>
      </div>

      {/* Plain language summary */}
      {report.plain_language_summary && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 space-y-3">
          <h2 className="font-semibold text-slate-800 text-sm">Plain-Language Summary</h2>
          <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
            {report.plain_language_summary}
          </div>
          <p className="text-xs text-slate-400 italic">{AI_SUMMARY_NOTICE}</p>
        </div>
      )}

      {/* Findings */}
      {report.findings.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-semibold text-slate-700 text-sm">Findings</h2>
          {(["high", "medium", "low", "info"] as const).flatMap((severity) =>
            report.findings
              .filter((f) => f.severity === severity)
              .map((f) => (
                <FindingCard key={f.id} finding={f} onReview={handleReview} />
              ))
          )}
        </div>
      )}

      {report.findings.length === 0 && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center text-sm text-green-700">
          No concerns flagged by any agent.
        </div>
      )}
    </div>
  );
}
