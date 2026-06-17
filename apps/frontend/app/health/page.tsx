"use client";
import { useEffect, useState } from "react";
import { healthCheck } from "@/lib/api";

interface HealthStatus {
  status: string;
  version?: string;
  uptime_seconds?: number;
  llm_available: boolean;
  db: string;
  redis: string;
}

type ComponentStatus = "ok" | "error" | "checking";

interface Component {
  label: string;
  status: ComponentStatus;
  detail: string;
}

function StatusDot({ status }: { status: ComponentStatus }) {
  if (status === "checking") return <span className="w-2.5 h-2.5 rounded-full bg-slate-300 animate-pulse inline-block" />;
  if (status === "ok") return <span className="w-2.5 h-2.5 rounded-full bg-green-500 inline-block" />;
  return <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" />;
}

export default function HealthPage() {
  const [components, setComponents] = useState<Component[]>([
    { label: "Backend API", status: "checking", detail: "Connecting…" },
    { label: "Database (PostgreSQL)", status: "checking", detail: "Checking…" },
    { label: "Cache (Redis)", status: "checking", detail: "Checking…" },
    { label: "LLM (Gemini)", status: "checking", detail: "Checking…" },
  ]);
  const [uptime, setUptime] = useState<number | null>(null);
  const [lastChecked, setLastChecked] = useState<string | null>(null);
  const [overall, setOverall] = useState<"ok" | "degraded" | "down" | "checking">("checking");

  async function check() {
    setComponents((c) => c.map((x) => ({ ...x, status: "checking" as ComponentStatus })));
    setOverall("checking");
    try {
      const h: HealthStatus = await healthCheck();
      setUptime(h.uptime_seconds ?? null);
      setLastChecked(new Date().toLocaleTimeString());

      const dbOk = h.db === "ok";
      const redisOk = h.redis === "ok";
      const llmOk = h.llm_available;

      setComponents([
        { label: "Backend API", status: "ok", detail: h.version ? `v${h.version}` : "reachable" },
        { label: "Database (PostgreSQL)", status: dbOk ? "ok" : "error", detail: dbOk ? "connected" : h.db },
        { label: "Cache (Redis)", status: redisOk ? "ok" : "error", detail: redisOk ? "connected" : h.redis },
        {
          label: "LLM (Groq (LLaMA))",
          status: llmOk ? "ok" : "error",
          detail: llmOk ? "API key present — Groq (LLaMA) available" : "No API key — regex fallback active",
        },
      ]);

      if (dbOk && redisOk) setOverall("ok");
      else setOverall("degraded");
    } catch {
      setLastChecked(new Date().toLocaleTimeString());
      setComponents([
        { label: "Backend API", status: "error", detail: "unreachable — is it running?" },
        { label: "Database (PostgreSQL)", status: "checking", detail: "—" },
        { label: "Cache (Redis)", status: "checking", detail: "—" },
        { label: "LLM (Groq)", status: "checking", detail: "—" },
      ]);
      setOverall("down");
    }
  }

  useEffect(() => {
    check();
    const id = setInterval(check, 10000);
    return () => clearInterval(id);
  }, []);

  const overallLabel = { ok: "All systems operational", degraded: "Degraded", down: "Backend unreachable", checking: "Checking…" }[overall];
  const overallBg = { ok: "bg-green-50 border-green-200 text-green-700", degraded: "bg-amber-50 border-amber-200 text-amber-700", down: "bg-red-50 border-red-200 text-red-700", checking: "bg-slate-50 border-slate-200 text-slate-600" }[overall];

  return (
    <div className="max-w-xl mx-auto space-y-5">
      <div className="space-y-1">
        <h1 className="text-xl font-semibold text-slate-800">System Status</h1>
        {lastChecked && <p className="text-xs text-slate-400">Last checked: {lastChecked} · auto-refreshes every 10s</p>}
      </div>

      <div className={`border rounded-xl px-4 py-3 font-medium text-sm flex items-center gap-2 ${overallBg}`}>
        <StatusDot status={overall === "checking" ? "checking" : overall === "ok" ? "ok" : "error"} />
        {overallLabel}
        {uptime !== null && <span className="ml-auto text-xs font-normal opacity-70">uptime {Math.floor(uptime)}s</span>}
      </div>

      <div className="bg-white border border-slate-200 rounded-xl divide-y divide-slate-100">
        {components.map((c) => (
          <div key={c.label} className="flex items-center gap-3 px-4 py-3">
            <StatusDot status={c.status} />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-700">{c.label}</p>
              <p className="text-xs text-slate-400 truncate">{c.detail}</p>
            </div>
            <span className={`text-xs font-medium ${c.status === "ok" ? "text-green-600" : c.status === "error" ? "text-red-600" : "text-slate-400"}`}>
              {c.status === "checking" ? "…" : c.status}
            </span>
          </div>
        ))}
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs text-slate-500 space-y-1">
        <p className="font-medium text-slate-600">Demo quick-start</p>
        <p className="font-mono bg-white rounded px-2 py-1 border border-slate-200">make demo-infra</p>
        <p className="font-mono bg-white rounded px-2 py-1 border border-slate-200">make demo-backend  <span className="text-slate-400"># terminal 1</span></p>
        <p className="font-mono bg-white rounded px-2 py-1 border border-slate-200">make demo-frontend  <span className="text-slate-400"># terminal 2</span></p>
        <p className="mt-2">The <strong>LLM</strong> row shows orange if no Groq key is set. Statistical checks (GRIM + p-value) still run automatically via regex — the system is fully functional without a key.</p>
      </div>

      <button onClick={check} className="w-full py-2 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50">
        Refresh now
      </button>
    </div>
  );
}
