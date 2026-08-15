"use client";

import Link from "next/link";
import { Shield, RefreshCw, Cpu, Activity, ArrowRight, CheckCircle, AlertTriangle } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-[#030303] text-zinc-100 overflow-hidden scanline">
      {/* Abstract Glowing Gradients */}
      <div className="absolute top-[-10%] left-[20%] w-[600px] height-[600px] rounded-full bg-blue-600/10 blur-[150px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[10%] w-[500px] height-[500px] rounded-full bg-emerald-600/5 blur-[120px] pointer-events-none" />

      {/* Header */}
      <header className="border-b border-zinc-900 bg-black/40 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-600/10 border border-blue-500/20 rounded-lg text-blue-500">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold tracking-tight text-white">WebGuardian</span>
              <span className="text-xs font-semibold text-blue-500 ml-1.5 px-1.5 py-0.5 bg-blue-500/10 rounded">AI</span>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <span className="text-xs text-zinc-500 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Sponsor Track: Bright Data
            </span>
            <Link
              href="/dashboard"
              className="px-4 py-2 text-sm bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-lg hover:bg-zinc-800 transition flex items-center gap-2"
            >
              Enter Console
              <ArrowRight className="w-4 h-4 text-zinc-400" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-6 pt-24 pb-32">
        <div className="text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-500/5 border border-blue-500/10 rounded-full text-xs font-medium text-blue-400 mb-8">
            <Activity className="w-3.5 h-3.5" />
            Autonomous Reliability Engineering for Web Data Pipelines
          </div>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-8">
            Your scraping pipelines break.<br />
            <span className="bg-gradient-to-r from-blue-400 via-indigo-400 to-emerald-400 bg-clip-text text-transparent">
              Your AI engineer fixes them.
            </span>
          </h1>
          <p className="text-lg md:text-xl text-zinc-400 max-w-2xl mx-auto mb-12 font-light leading-relaxed">
            Websites change. Selectors break. Data disappears. WebGuardian AI autonomously observes your pipelines, understands layout shifts, and repairs them instantly.
          </p>
          <div className="flex justify-center gap-4">
            <Link
              href="/dashboard"
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium rounded-xl transition flex items-center gap-2 shadow-lg shadow-blue-500/20"
            >
              Launch Command Center
              <ArrowRight className="w-4 h-4" />
            </Link>
            <a
              href="#workflow"
              className="px-6 py-3 bg-zinc-950 border border-zinc-900 hover:bg-zinc-900 text-zinc-300 font-medium rounded-xl transition"
            >
              Watch Healing Loop
            </a>
          </div>
        </div>

        {/* Cinematic Workflow Mockup */}
        <div id="workflow" className="mt-28 border border-zinc-900 bg-[#09090b]/80 rounded-2xl p-8 max-w-5xl mx-auto shadow-2xl relative">
          <div className="absolute top-3 left-4 flex gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-zinc-800" />
            <span className="w-2.5 h-2.5 rounded-full bg-zinc-800" />
            <span className="w-2.5 h-2.5 rounded-full bg-zinc-800" />
          </div>
          <div className="text-xs text-zinc-600 text-center mb-6 font-mono">webguardian_reliability_engine.log</div>

          <div className="grid md:grid-cols-4 gap-6 relative">
            {/* Step 1 */}
            <div className="border border-zinc-900/60 bg-[#0c0c0e]/60 rounded-xl p-5 text-center relative overflow-hidden">
              <div className="p-3 bg-amber-500/10 text-amber-500 border border-amber-500/20 rounded-xl w-fit mx-auto mb-4">
                <AlertTriangle className="w-5 h-5 animate-bounce" />
              </div>
              <h3 className="font-semibold text-white mb-2 text-sm">1. Failures Detected</h3>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Class `.price` missing on target DOM structure. Product extraction dropped to 0%.
              </p>
              <div className="absolute bottom-0 left-0 w-full h-[3px] bg-amber-500/30" />
            </div>

            {/* Step 2 */}
            <div className="border border-zinc-900/60 bg-[#0c0c0e]/60 rounded-xl p-5 text-center relative overflow-hidden">
              <div className="p-3 bg-blue-500/10 text-blue-500 border border-blue-500/20 rounded-xl w-fit mx-auto mb-4">
                <Cpu className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white mb-2 text-sm">2. AI Diagnosis</h3>
              <p className="text-xs text-zinc-500 leading-relaxed">
                LangGraph agent triggers DOM/Data analysis. Reconstructs semantic field extraction intent.
              </p>
              <div className="absolute bottom-0 left-0 w-full h-[3px] bg-blue-500/30" />
            </div>

            {/* Step 3 */}
            <div className="border border-zinc-900/60 bg-[#0c0c0e]/60 rounded-xl p-5 text-center relative overflow-hidden">
              <div className="p-3 bg-indigo-500/10 text-indigo-500 border border-indigo-500/20 rounded-xl w-fit mx-auto mb-4">
                <RefreshCw className="w-5 h-5 animate-spin" style={{ animationDuration: '3s' }} />
              </div>
              <h3 className="font-semibold text-white mb-2 text-sm">3. Sandbox Testing</h3>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Evaluates candidate selectors on new DOM. Computes final semantic & coverage validation score.
              </p>
              <div className="absolute bottom-0 left-0 w-full h-[3px] bg-indigo-500/30" />
            </div>

            {/* Step 4 */}
            <div className="border border-zinc-900/60 bg-[#0c0c0e]/60 rounded-xl p-5 text-center relative overflow-hidden">
              <div className="p-3 bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 rounded-xl w-fit mx-auto mb-4">
                <CheckCircle className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white mb-2 text-sm">4. Pipeline Restored</h3>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Repaired version v2 deployed to Bright Data Scraper Studio. Recovered 1,284 records.
              </p>
              <div className="absolute bottom-0 left-0 w-full h-[3px] bg-emerald-500/30" />
            </div>
          </div>
        </div>

        {/* Pitch / Positioning Section */}
        <div className="mt-32 text-center max-w-4xl mx-auto border-t border-zinc-900/80 pt-20">
          <h2 className="text-xs font-semibold text-blue-500 tracking-widest uppercase mb-4">The Reliability Category</h2>
          <p className="text-2xl md:text-3xl text-zinc-200 font-light mb-12 leading-relaxed">
            "PagerDuty detects pipeline failures. Datadog observes database metrics.<br />
            <span className="font-semibold text-white">WebGuardian AI repairs web data pipelines autonomously.</span>"
          </p>
          <div className="grid sm:grid-cols-3 gap-8 text-left">
            <div className="p-6 rounded-xl border border-zinc-900 bg-black/20">
              <h4 className="text-sm font-semibold text-white mb-2">Sponsor Integration</h4>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Built directly around Bright Data Scraper Studio as a control and deployment management plane.
              </p>
            </div>
            <div className="p-6 rounded-xl border border-zinc-900 bg-black/20">
              <h4 className="text-sm font-semibold text-white mb-2">Sandbox Scoring</h4>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Decides selector deployments by executing extractions inside an isolated schema validator.
              </p>
            </div>
            <div className="p-6 rounded-xl border border-zinc-900 bg-black/20">
              <h4 className="text-sm font-semibold text-white mb-2">Version Audits</h4>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Preserves complete version history records, deployment explanations, and one-click rollback triggers.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
