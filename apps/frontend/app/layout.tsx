import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { DISCLAIMER_FULL, DISCLAIMER_SHORT } from "@/lib/legal";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "PEERLESS.AI — Research Integrity Tool",
  description:
    "Multi-agent scientific peer-review tool. Surfaces flagged concerns for human review.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-slate-50 min-h-screen flex flex-col`}>
        {/* Header */}
        <header className="bg-white border-b border-slate-200 shadow-sm">
          <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link href="/" className="text-xl font-bold text-slate-800 tracking-tight hover:text-blue-700">
                PEERLESS.AI
              </Link>
              <span className="hidden sm:inline text-xs text-slate-500 border border-slate-300 rounded px-2 py-0.5">
                Research Integrity
              </span>
            </div>
            <nav className="flex items-center gap-4">
              <Link href="/" className="text-xs text-slate-500 hover:text-slate-800">Upload</Link>
              <Link href="/health" className="text-xs text-slate-500 hover:text-slate-800">Status</Link>
            </nav>
          </div>
          {/* Persistent disclaimer banner */}
          <div className="bg-amber-50 border-t border-amber-200 px-4 py-1.5">
            <p className="max-w-5xl mx-auto text-xs text-amber-800 text-center">
              {DISCLAIMER_FULL}
            </p>
          </div>
        </header>

        {/* Main */}
        <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-8">{children}</main>

        {/* Footer */}
        <footer className="bg-white border-t border-slate-200 mt-auto">
          <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between text-xs text-slate-400">
            <span>PEERLESS.AI v0.1.0</span>
            <span>{DISCLAIMER_SHORT}</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
