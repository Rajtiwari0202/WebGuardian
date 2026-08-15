"use client";

import Link from "next/link";
import { 
  Shield, ArrowLeft, Database, Globe, Activity, 
  Cpu, Code, RefreshCw, CheckCircle, Server, Eye, Layers
} from "lucide-react";

export default function ArchitectureVisualization() {
  const nodes = [
    {
      id: "website",
      icon: <Globe className="w-6 h-6 text-blue-500" />,
      title: "1. Target Website DOM",
      description: "Original DOM v1 shifts to redesigned layout v2.",
      details: "Price container class '.price' disappears; tag becomes '[data-testid=price]'"
    },
    {
      id: "collector",
      icon: <Server className="w-6 h-6 text-indigo-500" />,
      title: "2. Bright Data Collector",
      description: "Runs unblocking proxies and headless scraper scripts.",
      details: "Monitored via unique API triggers and snapshot IDs"
    },
    {
      id: "observatory",
      icon: <Activity className="w-6 h-6 text-red-500" />,
      title: "3. Scraper Observatory",
      description: "Audits data drops and structural validation mismatches.",
      details: "Translates 0-row extraction drops into pipeline failures"
    },
    {
      id: "drift",
      icon: <Shield className="w-6 h-6 text-amber-500" />,
      title: "4. Drift Engine",
      description: "Classifies anomalies: Schema Drift, DOM Drift, or Runtime drops.",
      details: "Blocks selector repair loops on runtime connection timeouts"
    },
    {
      id: "agent",
      icon: <Cpu className="w-6 h-6 text-blue-500" />,
      title: "5. LangGraph Repair Agent",
      description: "Runs state machine node loops (Triage, Analysis, intent, Plan).",
      details: "Recovers field extraction contract details to design solutions"
    },
    {
      id: "sandbox",
      icon: <Code className="w-6 h-6 text-purple-500" />,
      title: "6. Validation Sandbox",
      description: "Runs candidate selectors on new DOM and ranks outcomes.",
      details: "Formula: 30% Semantic + 30% Coverage + 20% Schema + 10% Layout + 10% Confidence"
    },
    {
      id: "deploy",
      icon: <RefreshCw className="w-6 h-6 text-emerald-500 animate-spin" style={{ animationDuration: '3s' }} />,
      title: "7. Studio Version Deploy",
      description: "Publishes configuration updates (vN) to Scraper Studio.",
      details: "Deprecates active v1 tags and triggers immediate pipeline recovery"
    },
    {
      id: "restored",
      icon: <CheckCircle className="w-6 h-6 text-emerald-400" />,
      title: "8. Recovered Pipeline",
      description: "Delivers complete dataset rows. Downtime: <35s.",
      details: "Logs version audit traces and preserves rollback triggers"
    }
  ];

  return (
    <div className="min-h-screen bg-[#030303] text-zinc-100 font-sans scanline">
      
      {/* Header */}
      <header className="border-b border-zinc-900 bg-zinc-950/40 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="p-2 bg-zinc-950 border border-zinc-900 hover:bg-zinc-900 rounded-lg text-zinc-400 hover:text-zinc-200 transition">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-sm font-bold text-white flex items-center gap-1.5">
              WebGuardian AI
              <span className="text-[10px] font-bold text-blue-500 px-1.5 py-0.5 bg-blue-500/10 rounded">DIAGRAM</span>
            </h1>
            <p className="text-[10px] text-zinc-500">Autonomous Reliability Pipeline Flow</p>
          </div>
        </div>
        <span className="text-xs text-zinc-500 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          Real-Time Architecture Map
        </span>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-12 space-y-16">
        
        {/* Six Word Pitch Banner */}
        <div className="text-center max-w-4xl mx-auto space-y-4">
          <h2 className="text-2xl font-bold tracking-tight text-white mb-2">WebGuardian Platform Architecture</h2>
          <div className="py-6 px-8 border border-blue-900/35 bg-blue-950/5 rounded-2xl max-w-3xl mx-auto shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 blur-[40px] pointer-events-none" />
            <span className="text-xs font-semibold text-blue-500 uppercase tracking-widest block mb-2 font-mono">Platform Thesis</span>
            <p className="text-lg md:text-2xl font-light text-zinc-100 leading-relaxed bg-gradient-to-r from-blue-400 via-indigo-200 to-emerald-400 bg-clip-text text-transparent">
              Observe → Understand → Repair → Validate → Deploy → Learn
            </p>
          </div>
        </div>

        {/* Three Layer Stack Design */}
        <div className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-2xl p-8 max-w-4xl mx-auto space-y-6 shadow-2xl">
          <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-2 mb-4 font-mono">
            <Layers className="w-4 h-4 text-blue-500" />
            WebGuardian AI Operational Layers
          </h3>
          
          <div className="space-y-4">
            {/* Layer 1: Experience */}
            <div className="p-5 border border-zinc-900 bg-zinc-950 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <span className="text-[10px] font-bold text-blue-500 uppercase tracking-widest block">EXPERIENCE LAYER</span>
                <span className="text-sm font-semibold text-zinc-200 mt-1 block">Control Center & Operator Cockpit</span>
              </div>
              <div className="flex gap-2">
                <span className="px-2.5 py-1 bg-zinc-900 border border-zinc-800 rounded text-xs text-zinc-400">Dashboard</span>
                <span className="px-2.5 py-1 bg-zinc-900 border border-zinc-800 rounded text-xs text-zinc-400">Incident War Room</span>
                <span className="px-2.5 py-1 bg-zinc-900 border border-zinc-800 rounded text-xs text-zinc-400">Data Explorer</span>
              </div>
            </div>

            {/* Layer 2: Intelligence */}
            <div className="p-5 border border-zinc-900 bg-zinc-950 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <span className="text-[10px] font-bold text-indigo-500 uppercase tracking-widest block">INTELLIGENCE LAYER</span>
                <span className="text-sm font-semibold text-zinc-200 mt-1 block">Decision Graph & Diagnostics Engine</span>
              </div>
              <div className="flex gap-2">
                <span className="px-2.5 py-1 bg-zinc-900 border border-zinc-800 rounded text-xs text-zinc-400">Drift Engine</span>
                <span className="px-2.5 py-1 bg-zinc-900 border border-zinc-800 rounded text-xs text-zinc-400">LangGraph Agent</span>
                <span className="px-2.5 py-1 bg-zinc-900 border border-zinc-800 rounded text-xs text-zinc-400">Agent Memory</span>
              </div>
            </div>

            {/* Layer 3: Execution */}
            <div className="p-5 border border-zinc-900 bg-zinc-950 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest block">EXECUTION LAYER</span>
                <span className="text-sm font-semibold text-zinc-200 mt-1 block">Managed Proxy Fabric & Sandbox Sandbox</span>
              </div>
              <div className="flex gap-2">
                <span className="px-2.5 py-1 bg-zinc-900 border border-zinc-800 rounded text-xs text-zinc-400">Bright Data Collectors</span>
                <span className="px-2.5 py-1 bg-zinc-900 border border-zinc-800 rounded text-xs text-zinc-400">Proxy Rotation</span>
                <span className="px-2.5 py-1 bg-zinc-900 border border-zinc-800 rounded text-xs text-zinc-400">Validation Sandbox</span>
              </div>
            </div>
          </div>
        </div>

        {/* Visual Node Grid */}
        <div className="border-t border-zinc-900/80 pt-16">
          <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest text-center mb-12 font-mono">
            Chronological Self-Healing Data Lifecycle
          </h3>
          <div className="grid md:grid-cols-2 gap-8 relative max-w-4xl mx-auto">
            {nodes.map((node) => (
              <div 
                key={node.id} 
                className="border border-zinc-900/80 bg-[#0c0c0e]/90 hover:bg-[#0c0c0e] rounded-2xl p-6 relative overflow-hidden transition shadow-xl group"
              >
                <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 blur-[40px] pointer-events-none group-hover:bg-blue-500/10 transition" />
                <div className="flex gap-4 items-start">
                  <div className="p-3 bg-zinc-950 border border-zinc-900 rounded-xl">
                    {node.icon}
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-sm font-bold text-white group-hover:text-blue-400 transition">
                      {node.title}
                    </h3>
                    <p className="text-xs text-zinc-400 leading-relaxed font-light">
                      {node.description}
                    </p>
                    <div className="pt-2">
                      <span className="text-[10px] font-mono text-zinc-600 block">
                        TELEMETRY: {node.details}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </main>
    </div>
  );
}
