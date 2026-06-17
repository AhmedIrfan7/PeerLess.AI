"use client";
import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { uploadPaper, NetworkError, ApiError } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const MAX_MB = 25;

  function validate(file: File): string | null {
    if (!file.name.toLowerCase().endsWith(".pdf") && file.type !== "application/pdf")
      return "Only PDF files are accepted.";
    if (file.size > MAX_MB * 1024 * 1024)
      return `File exceeds ${MAX_MB} MB limit.`;
    if (file.size === 0)
      return "File is empty.";
    return null;
  }

  async function handleFile(file: File) {
    const err = validate(file);
    if (err) { setError(err); return; }
    setError(null);
    setUploading(true);
    setProgress(30);
    try {
      setProgress(60);
      const res = await uploadPaper(file);
      setProgress(100);
      router.push(`/papers/${res.paper_id}`);
    } catch (e) {
      if (e instanceof NetworkError) setError("Cannot reach the backend. Is it running?");
      else if (e instanceof ApiError) setError(e.message);
      else setError("Upload failed. Please try again.");
      setUploading(false);
      setProgress(0);
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault(); setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  return (
    <div className="space-y-8">
      <div className="text-center space-y-2 pt-4">
        <h1 className="text-3xl font-bold text-slate-800">Research Integrity Analysis</h1>
        <p className="text-slate-500 max-w-lg mx-auto text-sm">
          Upload a paper to flag possible statistical, citation, or methodology concerns for expert review.
        </p>
      </div>

      {error && (
        <div className="max-w-xl mx-auto bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div
        className={`max-w-xl mx-auto border-2 border-dashed rounded-xl p-10 bg-white text-center space-y-4 transition-colors cursor-pointer
          ${dragging ? "border-blue-500 bg-blue-50" : "border-slate-300 hover:border-blue-400"}
          ${uploading ? "opacity-60 pointer-events-none" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <div className="text-4xl">{uploading ? "⏳" : "📄"}</div>
        <p className="font-medium text-slate-700">
          {uploading ? "Uploading…" : "Drop a PDF here, or click to browse"}
        </p>
        <p className="text-xs text-slate-400">PDF only · max {MAX_MB} MB</p>
        {uploading && (
          <div className="w-full bg-slate-200 rounded-full h-1.5">
            <div className="bg-blue-500 h-1.5 rounded-full transition-all" style={{ width: `${progress}%` }} />
          </div>
        )}
        <input ref={inputRef} type="file" accept=".pdf,application/pdf" className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
      </div>

      <div className="max-w-xl mx-auto grid grid-cols-3 gap-3 text-center">
        {[
          { icon: "🔢", label: "Statistical Integrity", desc: "GRIM + p-value checks" },
          { icon: "📚", label: "Citation Verification", desc: "Crossref · PubMed · arXiv" },
          { icon: "🗒️", label: "Plain-Language Summary", desc: "Accessible overview" },
        ].map((f) => (
          <div key={f.label} className="bg-white rounded-lg border border-slate-200 p-3 space-y-1">
            <div className="text-xl">{f.icon}</div>
            <p className="font-medium text-slate-700 text-xs">{f.label}</p>
            <p className="text-xs text-slate-400">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
