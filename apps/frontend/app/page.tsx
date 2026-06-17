export default function Home() {
  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="text-center space-y-3 pt-4">
        <h1 className="text-3xl font-bold text-slate-800">Research Integrity Analysis</h1>
        <p className="text-slate-600 max-w-xl mx-auto">
          PEERLESS.AI flags possible concerns in a paper for expert review.
          It does not adjudicate misconduct.
        </p>
      </div>

      {/* Upload card — placeholder; wired in Step 11 */}
      <div className="max-w-xl mx-auto border-2 border-dashed border-slate-300 rounded-xl p-10 bg-white text-center space-y-4 hover:border-blue-400 transition-colors">
        <div className="text-4xl">📄</div>
        <p className="font-medium text-slate-700">Upload a research paper (PDF)</p>
        <p className="text-sm text-slate-500">
          Drag and drop here, or click to browse. Max 25 MB.
        </p>
        <button
          disabled
          className="mt-2 px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium opacity-50 cursor-not-allowed"
        >
          Select PDF
        </button>
        <p className="text-xs text-slate-400">Upload functionality coming in Step 11</p>
      </div>

      {/* What it does */}
      <div className="max-w-xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
        {[
          { icon: "🔢", label: "Statistical Integrity", desc: "GRIM + p-value recomputation" },
          { icon: "📚", label: "Citation Verification", desc: "Crossref · PubMed · arXiv" },
          { icon: "🗒️", label: "Plain-Language Summary", desc: "Accessible 4-paragraph overview" },
        ].map((f) => (
          <div key={f.label} className="bg-white rounded-lg border border-slate-200 p-4 space-y-1">
            <div className="text-2xl">{f.icon}</div>
            <p className="font-medium text-slate-700 text-sm">{f.label}</p>
            <p className="text-xs text-slate-500">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
