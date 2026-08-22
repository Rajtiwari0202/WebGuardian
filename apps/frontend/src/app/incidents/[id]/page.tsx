"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  Shield, RefreshCw, Cpu, Activity, AlertOctagon, 
  CheckCircle, ArrowLeft, Terminal, AlertTriangle, 
  ArrowRight, ShieldCheck, HelpCircle
} from "lucide-react";

import { API_BASE_URL } from "@/config/api";

export default function IncidentWarRoom({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = React.use(params);
  const incidentId = resolvedParams.id;
  
  const [incidentData, setIncidentData] = useState<any>(null);
  const [liveLog, setLiveLog] = useState<any[]>([]);
  const [status, setStatus] = useState<string>("INVESTIGATING");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Initial fetch
    fetchIncidentDetails();

    // 2. Continuous polling until resolved
    const pollTimer = setInterval(() => {
      fetchIncidentDetails();
    }, 1200);

    // 3. Open Server-Sent Events (SSE) stream for live updates
    const eventSource = new EventSource(`${API_BASE_URL}/api/demo/incident/${incidentId}/stream`);

    eventSource.onopen = () => {
      console.log("SSE: Connected to incident stream");
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "AGENT_STEP") {
          setLiveLog(prev => {
            if (prev.some(item => item.description === data.message)) return prev;
            return [...prev, {
              time: new Date().toLocaleTimeString(),
              event: data.node.replace("_", " "),
              description: data.message,
              status: "completed"
            }];
          });
          
          if (data.node === "RECOVERY_RUN" || data.node === "DEPLOYMENT" || data.node === "VERSION_AND_AUDIT") {
            setStatus("RECOVERED");
            setTimeout(fetchIncidentDetails, 500);
          }
        }
      } catch (err) {
        console.error("Error parsing SSE packet:", err);
      }
    };

    eventSource.onerror = (err) => {
      eventSource.close();
    };

    return () => {
      clearInterval(pollTimer);
      eventSource.close();
    };
  }, [incidentId]);

  const fetchIncidentDetails = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/demo/incident/${incidentId}`);
      if (!res.ok) throw new Error("Incident not found");
      const data = await res.json();
      setIncidentData(data);
      if (data.status === "SUCCESS" || (data.new_selector && data.new_selector !== "TBD (Generating...)")) {
        setStatus("RECOVERED");
      }
    } catch (err: any) {
      setError(err.message || "Failed to load incident details");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#030303] text-zinc-100 flex flex-col items-center justify-center font-sans">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mb-4" />
        <p className="text-xs text-zinc-400 font-mono">Initializing AI Reliability Engine...</p>
        <p className="text-[10px] text-zinc-600 mt-1">Connecting Bright Data telemetry streams...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#030303] text-zinc-100 flex flex-col items-center justify-center font-sans px-4">
        <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
        <h2 className="text-sm font-bold text-white mb-2">WebGuardian encountered an infrastructure issue</h2>
        <p className="text-xs text-zinc-500 max-w-md text-center mb-6">
          The requested Incident trace ID could not be retrieved from the active database tables.
        </p>
        <Link href="/dashboard" className="px-4 py-2 bg-zinc-900 border border-zinc-800 text-xs font-semibold rounded-lg text-zinc-300 hover:text-white transition flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>
      </div>
    );
  }

  const combinedTimeline = incidentData?.timeline || liveLog;

  return (
    <div className="min-h-screen bg-[#030303] text-zinc-100 font-sans scanline">
      {/* Header Indicator */}
      <div className="border-b border-zinc-900 bg-black/60 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="p-2 bg-zinc-950 border border-zinc-900 hover:bg-zinc-900 rounded-lg text-zinc-400 hover:text-zinc-200 transition">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold text-red-500 px-2 py-0.5 bg-red-500/10 rounded">🔥 CRITICAL INCIDENT</span>
              <span className="text-xs font-mono text-zinc-500">#{incidentId}</span>
            </div>
            <h1 className="text-sm font-bold text-white mt-1">Laptop Price Monitor Redesign Redirection</h1>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <span className="text-[10px] text-zinc-500 block">STATUS</span>
            <span className={`text-xs font-bold ${status === "RECOVERED" ? "text-emerald-500" : "text-amber-500 animate-pulse"}`}>
              {status}
            </span>
          </div>
          <div className="text-right border-l border-zinc-900 pl-4">
            <span className="text-[10px] text-zinc-500 block">IMPACT</span>
            <span className="text-xs font-bold text-white">12,431 rows affected</span>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-10 grid md:grid-cols-3 gap-8">
        
        {/* Left Column: Root Cause Analysis & Selector Repair */}
        <div className="md:col-span-2 space-y-8">
          
          {/* Root Cause Analysis block */}
          <div className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-xl p-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 blur-[50px] pointer-events-none" />
            <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-4">Root Cause Analysis</h3>
            
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4 font-mono text-xs">
                <div className="p-4 bg-red-950/20 border border-red-900/20 rounded-lg text-red-300">
                  <span className="text-[10px] text-red-500 font-bold block mb-1">OLD SELECTOR (FAILED)</span>
                  {incidentData?.old_selector || ".price"}
                </div>
                <div className="p-4 bg-emerald-950/20 border border-emerald-900/20 rounded-lg text-emerald-300">
                  <span className="text-[10px] text-emerald-500 font-bold block mb-1">REPAIRED SELECTOR (DEPLOYED)</span>
                  {incidentData?.new_selector || "TBD (Generating...)"}
                </div>
              </div>

              <div className="p-4 bg-zinc-950 border border-zinc-900 rounded-lg text-xs leading-relaxed">
                <span className="text-[10px] font-bold text-zinc-500 block mb-1.5">AI EXPLANATION</span>
                <p className="text-zinc-400 font-light">
                  {incidentData?.reasoning || 
                    "The selector failed because the target product card component was migrated from CSS class markers (.price) to semantic test identifiers (data-testid='price') during a website layout redesign."}
                </p>
              </div>
            </div>
          </div>

          {/* AI Repairs Table */}
          <div className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-xl p-6">
            <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-4">Sandbox Candidate Audits</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-zinc-900 text-zinc-500">
                    <th className="pb-3">Candidate Selector</th>
                    <th className="pb-3">Strategy</th>
                    <th className="pb-3 text-right">Semantic Score</th>
                    <th className="pb-3 text-right">Coverage</th>
                    <th className="pb-3 text-right">Final Score</th>
                    <th className="pb-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-900/50">
                  {incidentData?.candidates && incidentData.candidates.length > 0 ? (
                    incidentData.candidates.map((cand: any, idx: number) => (
                      <tr key={idx} className="text-zinc-300">
                        <td className="py-3.5 font-mono text-zinc-400">{cand.selector}</td>
                        <td className="py-3.5 capitalize">{cand.strategy.replace("_", " ")}</td>
                        <td className="py-3.5 text-right">{cand.semantic_score}%</td>
                        <td className="py-3.5 text-right">{cand.validation_score}%</td>
                        <td className="py-3.5 text-right font-bold">{cand.final_score}%</td>
                        <td className="py-3.5 text-right">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            cand.status === "SELECTED" 
                              ? "bg-emerald-500/10 text-emerald-500" 
                              : "bg-zinc-800/40 text-zinc-500"
                          }`}>
                            {cand.status === "SELECTED" ? "DEPLOYED" : "REJECTED"}
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-zinc-600">
                        Sandbox candidates generating...
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Deployment History Timeline block */}
          <div className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-xl p-6">
            <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-6">Deployment Trace</h3>
            <div className="flex items-center gap-6 justify-center max-w-lg mx-auto py-4">
              <div className="p-4 rounded-xl border border-zinc-900 bg-zinc-950 text-center w-36">
                <span className="text-[10px] text-zinc-500 block">Collector v1</span>
                <span className="text-xs font-mono text-zinc-400 mt-1 block">.price</span>
              </div>
              <ArrowRight className="w-5 h-5 text-zinc-700" />
              <div className="p-4 rounded-xl border border-red-950 bg-red-950/10 text-center w-36">
                <span className="text-[10px] text-red-500 block">🔥 Failure</span>
                <span className="text-xs font-mono text-red-400 mt-1 block">0 rows extracted</span>
              </div>
              <ArrowRight className="w-5 h-5 text-zinc-700 animate-pulse" />
              <div className="p-4 rounded-xl border border-emerald-900 bg-emerald-950/15 text-center w-36">
                <span className="text-[10px] text-emerald-500 block">Collector v2</span>
                <span className="text-xs font-mono text-emerald-400 mt-1 block">
                  {incidentData?.new_selector || "[data-testid='price']"}
                </span>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column: AI Engineer Live Log */}
        <div className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-xl p-6 h-fit">
          <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-6 flex items-center gap-2">
            <Terminal className="w-4 h-4 text-blue-500 animate-pulse" />
            AI Reliability Timeline
          </h3>

          <div className="relative border-l border-zinc-800 pl-5 ml-2.5 space-y-6">
            {combinedTimeline.map((step: any, idx: number) => (
              <div key={idx} className="relative">
                <div className={`absolute left-[-26px] top-1.5 w-3 h-3 rounded-full border border-zinc-950 ${
                  step.status === "completed" ? "bg-blue-500" : "bg-red-500 animate-ping"
                }`} />
                <span className="text-[9px] font-mono text-zinc-600 block">{step.time}</span>
                <h4 className="text-xs font-bold text-zinc-300 capitalize">{step.event}</h4>
                <p className="text-[10px] text-zinc-500 mt-1 leading-relaxed">{step.description}</p>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
