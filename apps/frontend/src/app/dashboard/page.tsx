"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { 
  Shield, RefreshCw, Cpu, Activity, Play, AlertOctagon, 
  CheckCircle, ArrowRight, MessageSquare, Terminal, Clock, 
  History, Eye, AlertTriangle, Layers, ArrowLeftRight, Trash2
} from "lucide-react";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, BarChart, Bar
} from "recharts";

import { API_BASE_URL } from "@/config/api";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<"observatory" | "visualizer" | "chat" | "versions">("observatory");
  const [mounted, setMounted] = useState(false);
  const [judgeMode, setJudgeMode] = useState(false);
  const [autonomousMode, setAutonomousMode] = useState(false);
  const [hasApiKey, setHasApiKey] = useState(false);
  
  // Scraper & Telemetry States
  const [scrapers, setScrapers] = useState<any[]>([]);
  const [selectedScraper, setSelectedScraper] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [incidentTrace, setIncidentTrace] = useState<any>(null);
  
  // Loading & Running Indicators
  const [isRunning, setIsRunning] = useState(false);
  const [isChaosRunning, setIsChaosRunning] = useState(false);
  const [activeIncidentId, setActiveIncidentId] = useState<string | null>(null);
  const [resetMessage, setResetMessage] = useState<string | null>(null);

  // Chat State
  const [chatMessage, setChatMessage] = useState("");
  const [chatLog, setChatLog] = useState<Array<{ sender: "user" | "ai"; text: string; actions?: string[] }>>([
    {
      sender: "ai",
      text: "Hello! I am WebGuardian AI, your autonomous web reliability engineer. I am actively monitoring your scraper pipelines. Ask me anything."
    }
  ]);
  const [chatLoading, setChatLoading] = useState(false);

  useEffect(() => {
    setMounted(true);
    fetchData();
  }, []);

  // Poll incident status during live runs
  useEffect(() => {
    if (!activeIncidentId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/demo/incident/${activeIncidentId}`);
        const data = await res.json();
        setIncidentTrace(data);

        if (data.status === "SUCCESS" || data.status === "FAILED") {
          setIsChaosRunning(false);
          setActiveIncidentId(null);
          fetchData();
        }
      } catch (err) {
        console.error("Error polling incident:", err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [activeIncidentId]);

  const fetchData = async () => {
    try {
      const scrapersRes = await fetch(`${API_BASE_URL}/api/scrapers`);
      const scrapersData = await scrapersRes.json();
      setScrapers(scrapersData);
      
      const laptopScraper = scrapersData.find((s: any) => s.name.includes("Laptop")) || scrapersData[0];
      if (laptopScraper) {
        const detailsRes = await fetch(`${API_BASE_URL}/api/scrapers/${laptopScraper.id}`);
        const detailsData = await detailsRes.json();
        setSelectedScraper(detailsData);
      }

      const analyticsRes = await fetch(`${API_BASE_URL}/api/analytics/dashboard`);
      const analyticsData = await analyticsRes.json();
      setAnalytics(analyticsData);
    } catch (err) {
      console.error("Error fetching dashboard telemetry:", err);
    }
  };

  const handleRunScraper = async () => {
    if (!selectedScraper) return;
    setIsRunning(true);
    try {
      await fetch(`${API_BASE_URL}/api/scrapers/${selectedScraper.id}/run`, {
        method: "POST"
      });
      setTimeout(() => {
        setIsRunning(false);
        fetchData();
      }, 1500);
    } catch (err) {
      setIsRunning(false);
    }
  };

  // Scenario 1: DOM Redesign
  const handleTriggerChaos = async () => {
    if (!selectedScraper) return;
    setIsChaosRunning(true);
    setActiveTab("visualizer");
    setIncidentTrace({
      status: "INCIDENT_DETECTED",
      timeline: [
        { time: "10:02:01", event: "Failure detected: Price extraction dropped to 0%", status: "active" },
        { time: "10:02:03", event: "Failure triage: DOM_DRIFT confirmed", status: "active" }
      ],
      candidates: []
    });

    try {
      const res = await fetch(`${API_BASE_URL}/api/demo/trigger-chaos?scraper_id=${selectedScraper.id}`, {
        method: "POST"
      });
      const data = await res.json();
      setActiveIncidentId(data.run_id);
    } catch (err) {
      setIsChaosRunning(false);
    }
  };

  // Scenario 2: Bright Data Timeout Outage
  const handleTriggerTimeoutDrift = async () => {
    if (!selectedScraper) return;
    setIsChaosRunning(true);
    setActiveTab("visualizer");
    setIncidentTrace({
      status: "INCIDENT_DETECTED",
      timeline: [
        { time: "10:05:01", event: "Failure detected: Timeout connecting to collector", status: "active" }
      ],
      candidates: []
    });

    try {
      const res = await fetch(`${API_BASE_URL}/api/demo/trigger-timeout-drift?scraper_id=${selectedScraper.id}`, {
        method: "POST"
      });
      const data = await res.json();
      setActiveIncidentId(data.run_id);
    } catch (err) {
      setIsChaosRunning(false);
    }
  };

  // Scenario 3: Unsafe Strategy Rejections
  const handleTriggerUnsafeDrift = async () => {
    if (!selectedScraper) return;
    setIsChaosRunning(true);
    setActiveTab("visualizer");
    setIncidentTrace({
      status: "INCIDENT_DETECTED",
      timeline: [
        { time: "10:08:01", event: "Failure detected: DOM drift on required elements", status: "active" }
      ],
      candidates: []
    });

    try {
      const res = await fetch(`${API_BASE_URL}/api/demo/trigger-unsafe-drift?scraper_id=${selectedScraper.id}`, {
        method: "POST"
      });
      const data = await res.json();
      setActiveIncidentId(data.run_id);
    } catch (err) {
      setIsChaosRunning(false);
    }
  };

  const handleResetDemo = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/demo/reset`, {
        method: "POST"
      });
      const data = await res.json();
      setResetMessage(data.message);
      setActiveIncidentId(null);
      setIncidentTrace(null);
      setIsChaosRunning(false);
      setAutonomousMode(false);
      fetchData();
      setTimeout(() => setResetMessage(null), 3000);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRollback = async (version: number) => {
    if (!selectedScraper) return;
    try {
      await fetch(`${API_BASE_URL}/api/scrapers/${selectedScraper.id}/rollback?version_number=${version}`, {
        method: "POST"
      });
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleChatSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatMessage.trim()) return;

    const userMsg = chatMessage;
    setChatMessage("");
    setChatLog(prev => [...prev, { sender: "user", text: userMsg }]);
    setChatLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg })
      });
      const data = await res.json();
      setChatLog(prev => [...prev, { sender: "ai", text: data.response, actions: data.suggested_actions }]);
    } catch (err) {
      setChatLog(prev => [...prev, { sender: "ai", text: "Error connecting to AI Reliability Chat engine." }]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030303] text-zinc-100 font-sans scanline">
      
      {/* Top Banner Mode Indicator */}
      <div className="border-b border-zinc-900 bg-black/80 px-6 py-2.5 flex items-center justify-between text-xs text-zinc-400">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-semibold text-zinc-300">
            {hasApiKey ? "DATA SOURCE ● Bright Data Connected" : "DEMO SIMULATION ● Mock Collector Mode"}
          </span>
          <span className="text-zinc-700">|</span>
          <span className="italic text-zinc-500">"AI proposes. Sandbox proves. WebGuardian deploys."</span>
        </div>
        <div className="flex items-center gap-3">
          {resetMessage && (
            <span className="text-[10px] text-emerald-400 font-mono animate-bounce">{resetMessage}</span>
          )}
          <button
            onClick={handleResetDemo}
            className="px-2 py-1 bg-zinc-950 hover:bg-zinc-900 border border-zinc-900 hover:border-zinc-800 rounded text-[10px] font-bold text-zinc-400 hover:text-white transition flex items-center gap-1"
          >
            <Trash2 className="w-3 h-3 text-red-500" />
            Reset Demo Environment
          </button>
        </div>
      </div>

      {/* Main Command Header */}
      <header className="border-b border-zinc-900 bg-zinc-950/40 backdrop-blur-md sticky top-0 z-40 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-600/10 border border-blue-500/20 rounded-lg text-blue-500">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold tracking-tight text-white flex items-center gap-1.5 text-sm md:text-base">
              WebGuardian AI
              <span className="text-[10px] font-bold text-blue-500 px-1.5 py-0.5 bg-blue-500/10 rounded">CONSOLE</span>
            </h1>
            <div className="flex items-center gap-2">
              <p className="text-[10px] text-zinc-500">Autonomous Web Reliability Engineering</p>
              <span className="text-zinc-700 text-[10px]">•</span>
              <Link href="/architecture" className="text-[10px] text-zinc-400 hover:text-white transition flex items-center gap-0.5">
                View System Map <ArrowRight className="w-2.5 h-2.5" />
              </Link>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          
          {/* Judge Mode Switch */}
          <div className="flex items-center gap-1.5 border border-zinc-900 bg-zinc-950 px-3 py-1.5 rounded-lg text-xs">
            <span className={`w-1.5 h-1.5 rounded-full ${judgeMode ? "bg-amber-500" : "bg-zinc-700"}`} />
            <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Judge Mode</span>
            <button
              onClick={() => setJudgeMode(!judgeMode)}
              className={`ml-1.5 px-2 py-0.5 rounded text-[10px] font-bold transition ${
                judgeMode ? "bg-amber-500/10 text-amber-500 border border-amber-500/30" : "bg-zinc-850 text-zinc-500 border border-zinc-800"
              }`}
            >
              {judgeMode ? "ON" : "OFF"}
            </button>
          </div>

          {/* Autonomous Mode Toggle */}
          <div className="flex items-center gap-1.5 border border-zinc-900 bg-zinc-950 px-3 py-1.5 rounded-lg text-xs">
            <span className={`w-1.5 h-1.5 rounded-full ${autonomousMode ? "bg-emerald-500 animate-pulse" : "bg-zinc-700"}`} />
            <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Autonomous</span>
            <button
              onClick={() => {
                setAutonomousMode(!autonomousMode);
                if (!autonomousMode) {
                  handleTriggerChaos();
                }
              }}
              className={`ml-1.5 px-2 py-0.5 rounded text-[10px] font-bold transition ${
                autonomousMode ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/30" : "bg-zinc-850 text-zinc-500 border border-zinc-800"
              }`}
            >
              {autonomousMode ? "ON" : "OFF"}
            </button>
          </div>

          {/* Scenarios triggers */}
          <button
            onClick={handleRunScraper}
            disabled={isRunning || isChaosRunning}
            className="px-3.5 py-1.5 bg-zinc-900 hover:bg-zinc-850 text-zinc-200 border border-zinc-800 hover:border-zinc-750 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 disabled:opacity-50"
          >
            {isRunning ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5 text-zinc-400" />
            )}
            Run Collector
          </button>
          
          <button
            onClick={handleTriggerChaos}
            disabled={isChaosRunning || isRunning}
            className="px-3.5 py-1.5 bg-gradient-to-r from-red-950/60 to-red-900/60 hover:from-red-900/80 hover:to-red-800/80 text-red-200 border border-red-900/50 hover:border-red-700/60 text-xs font-bold rounded-lg transition flex items-center gap-1.5 disabled:opacity-50"
          >
            DOM Drift
          </button>

          <button
            onClick={handleTriggerTimeoutDrift}
            disabled={isChaosRunning || isRunning}
            className="px-3.5 py-1.5 bg-gradient-to-r from-amber-950/40 to-amber-900/40 hover:from-amber-900/60 hover:to-amber-800/60 text-amber-200 border border-amber-900/50 hover:border-amber-700/60 text-xs font-bold rounded-lg transition flex items-center gap-1.5 disabled:opacity-50"
          >
            Outage Timeout
          </button>

          <button
            onClick={handleTriggerUnsafeDrift}
            disabled={isChaosRunning || isRunning}
            className="px-3.5 py-1.5 bg-gradient-to-r from-purple-950/40 to-purple-900/40 hover:from-purple-900/60 hover:to-purple-800/60 text-purple-200 border border-purple-900/50 hover:border-purple-700/60 text-xs font-bold rounded-lg transition flex items-center gap-1.5 disabled:opacity-50"
          >
            Unsafe Rejections
          </button>
        </div>
      </header>

      {/* Dashboard container */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        
        {/* Global Incident Alert Banner */}
        {activeIncidentId && (
          <div className="border border-red-950 bg-red-950/10 px-6 py-4 rounded-xl flex items-center justify-between text-xs text-red-200 mb-6">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-500 animate-pulse" />
              <div>
                <span className="font-bold uppercase block tracking-wider">🔥 CRITICAL RELIABILITY INCIDENT</span>
                <span className="text-[10px] text-zinc-400">Collector Laptop Prices Monitor failed schema extraction constraints.</span>
              </div>
            </div>
            <Link
              href={`/incidents/${activeIncidentId}`}
              className="px-3 py-1.5 bg-red-900 hover:bg-red-800 border border-red-700/60 rounded text-[11px] font-bold text-red-200 transition flex items-center gap-1.5 animate-bounce"
            >
              Enter Incident War Room
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        )}

        {/* JUDGE MODE PANEL (Displays when ON to simplify metrics) */}
        {judgeMode ? (
          <div className="border border-amber-900 bg-amber-950/5 rounded-xl p-8 mb-8 space-y-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-48 h-48 bg-amber-500/5 blur-[80px]" />
            <h2 className="text-xs font-bold text-amber-500 uppercase tracking-widest flex items-center gap-2">
              <Eye className="w-4 h-4" />
              Autonomous Reliability Engine Pitch Summary
            </h2>
            <div className="grid sm:grid-cols-5 gap-6 text-center">
              <div className="p-5 border border-zinc-900 bg-black/40 rounded-xl">
                <span className="text-[10px] font-bold text-red-500 block mb-1">PROBLEM</span>
                <span className="text-sm font-bold text-white block">SCRAPER FAILURE</span>
                <span className="text-[10px] text-zinc-500 block mt-1">87% Data Loss</span>
              </div>
              <div className="p-5 border border-zinc-900 bg-black/40 rounded-xl">
                <span className="text-[10px] font-bold text-amber-500 block mb-1">INTELLIGENCE</span>
                <span className="text-sm font-bold text-white block">AI ROOT CAUSE</span>
                <span className="text-[10px] text-zinc-500 block mt-1">DOM Drift Detected</span>
              </div>
              <div className="p-5 border border-zinc-900 bg-black/40 rounded-xl">
                <span className="text-[10px] font-bold text-blue-500 block mb-1">REPAIR</span>
                <span className="text-sm font-bold text-white block">3 CANDIDATES</span>
                <span className="text-[10px] text-zinc-500 block mt-1">Strategies planned</span>
              </div>
              <div className="p-5 border border-zinc-900 bg-black/40 rounded-xl">
                <span className="text-[10px] font-bold text-purple-500 block mb-1">SAFETY</span>
                <span className="text-sm font-bold text-white block">SANDBOX TESTED</span>
                <span className="text-[10px] text-zinc-500 block mt-1">100% Schema Pass</span>
              </div>
              <div className="p-5 border border-emerald-900 bg-emerald-950/10 rounded-xl">
                <span className="text-[10px] font-bold text-emerald-400 block mb-1">RESULT</span>
                <span className="text-sm font-bold text-emerald-400 block">AUTO DEPLOYED</span>
                <span className="text-[10px] text-emerald-500 block mt-1">Pipeline Restored</span>
              </div>
            </div>
          </div>
        ) : null}

        {/* Navigation Tabs */}
        <div className="flex border-b border-zinc-900 mb-8 gap-1">
          <button
            onClick={() => setActiveTab("observatory")}
            className={`px-4 py-3 text-xs font-bold tracking-tight border-b-2 flex items-center gap-2 transition ${
              activeTab === "observatory" 
                ? "border-blue-500 text-white bg-blue-500/5" 
                : "border-transparent text-zinc-500 hover:text-zinc-300"
            }`}
          >
            <Activity className="w-4 h-4" />
            Observatory Dashboard
          </button>
          <button
            onClick={() => setActiveTab("visualizer")}
            className={`px-4 py-3 text-xs font-bold tracking-tight border-b-2 flex items-center gap-2 transition ${
              activeTab === "visualizer" 
                ? "border-blue-500 text-white bg-blue-500/5" 
                : "border-transparent text-zinc-500 hover:text-zinc-300"
            }`}
          >
            <Cpu className="w-4 h-4" />
            AI Incident Visualizer
            {isChaosRunning && (
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-ping" />
            )}
          </button>
          <button
            onClick={() => setActiveTab("chat")}
            className={`px-4 py-3 text-xs font-bold tracking-tight border-b-2 flex items-center gap-2 transition ${
              activeTab === "chat" 
                ? "border-blue-500 text-white bg-blue-500/5" 
                : "border-transparent text-zinc-500 hover:text-zinc-300"
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            Ask AI Engineer
          </button>
          <button
            onClick={() => setActiveTab("versions")}
            className={`px-4 py-3 text-xs font-bold tracking-tight border-b-2 flex items-center gap-2 transition ${
              activeTab === "versions" 
                ? "border-blue-500 text-white bg-blue-500/5" 
                : "border-transparent text-zinc-500 hover:text-zinc-300"
            }`}
          >
            <History className="w-4 h-4" />
            Version & Audits
          </button>
        </div>

        {/* Tab Contents */}
        {activeTab === "observatory" && (
          <div className="space-y-8">
            {/* Top Cards Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="p-5 rounded-xl border border-zinc-900 bg-[#0c0c0e]/80 flex flex-col justify-between h-32">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Active Collectors</span>
                <span className="text-3xl font-bold text-white tracking-tight">
                  {analytics?.metrics?.active_scrapers || 24}
                </span>
                <span className="text-[10px] text-zinc-600">All published in Scraper Studio</span>
              </div>
              <div className="p-5 rounded-xl border border-zinc-900 bg-[#0c0c0e]/80 flex flex-col justify-between h-32">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Pipeline Health</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold text-white tracking-tight">
                    {analytics?.metrics?.pipeline_health || 99.8}%
                  </span>
                  <span className="text-[10px] text-emerald-500">Stable</span>
                </div>
                <span className="text-[10px] text-zinc-600">Dynamic extraction score</span>
              </div>
              <div className="p-5 rounded-xl border border-zinc-900 bg-[#0c0c0e]/80 flex flex-col justify-between h-32">
                <span className="text-[10px] font-bold text-red-500 uppercase tracking-widest">Active Incidents</span>
                <span className="text-3xl font-bold text-white tracking-tight">
                  {analytics?.metrics?.failed_today || 0}
                </span>
                <span className="text-[10px] text-zinc-600">Awaiting selector audits</span>
              </div>
              <div className="p-5 rounded-xl border border-zinc-900 bg-[#0c0c0e]/80 flex flex-col justify-between h-32">
                <span className="text-[10px] font-bold text-blue-500 uppercase tracking-widest">Auto Healed</span>
                <span className="text-3xl font-bold text-white tracking-tight">
                  {analytics?.metrics?.auto_repairs || 18}
                </span>
                <span className="text-[10px] text-zinc-600">Repaired without downtime</span>
              </div>
            </div>

            {/* Enterprise Impact section */}
            <div className="border border-zinc-900 bg-[#09090b]/40 rounded-xl p-6">
              <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-6 font-mono">Prevented Business Downtime</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <span className="text-xs text-zinc-600 block mb-1">Downtime Prevented</span>
                  <span className="text-lg font-bold text-emerald-500">
                    {analytics?.business_impact?.downtime_prevented_hours || 18.4} hours
                  </span>
                </div>
                <div>
                  <span className="text-xs text-zinc-600 block mb-1">Manual Fixes Avoided</span>
                  <span className="text-lg font-bold text-zinc-300">
                    {analytics?.business_impact?.manual_fixes_avoided || 142}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-zinc-600 block mb-1">Avg Recovery Time</span>
                  <span className="text-lg font-bold text-blue-500">
                    {analytics?.business_impact?.average_recovery_time_seconds || 28} seconds
                  </span>
                </div>
                <div>
                  <span className="text-xs text-zinc-600 block mb-1">Engineering Hours Saved</span>
                  <span className="text-lg font-bold text-zinc-300">
                    {analytics?.business_impact?.engineering_hours_saved || 76} hrs/mo
                  </span>
                </div>
              </div>
            </div>

            {/* Charts Section */}
            <div className="grid md:grid-cols-2 gap-8">
              <div className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-xl p-6">
                <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-4">Pipeline Health History</h3>
                <div className="h-64">
                  {mounted && analytics?.health_history && (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={analytics.health_history}>
                        <defs>
                          <linearGradient id="colorHealth" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <XAxis dataKey="day" stroke="#52525b" fontSize={10} />
                        <YAxis domain={[90, 100]} stroke="#52525b" fontSize={10} />
                        <Tooltip contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a" }} />
                        <Area type="monotone" dataKey="score" stroke="#3b82f6" fillOpacity={1} fill="url(#colorHealth)" strokeWidth={2} />
                      </AreaChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>

              <div className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-xl p-6">
                <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-4">Latency Drift Monitor (ms)</h3>
                <div className="h-64">
                  {mounted && analytics?.latency_drift && (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={analytics.latency_drift}>
                        <XAxis dataKey="run" stroke="#52525b" fontSize={10} />
                        <YAxis stroke="#52525b" fontSize={10} />
                        <Tooltip contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a" }} />
                        <Bar dataKey="latency" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "visualizer" && (
          <div className="space-y-8">
            
            {/* Active Incident Warning */}
            {isChaosRunning && (
              <div className="border border-red-950 bg-red-950/10 px-6 py-4 rounded-xl flex items-center justify-between text-xs text-red-200 animate-pulse">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-500 animate-bounce" />
                  <div>
                    <span className="font-bold uppercase block tracking-wider">🔥 STATEFUL REPAIR IN PROGRESS</span>
                    <span className="text-[10px] text-red-400">LangGraph Agent is executing DOM validation checks in Sandbox.</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-red-500 rounded-full animate-ping" />
                  <span>AI Agent Executing...</span>
                </div>
              </div>
            )}

            {/* Twin Panels Layout */}
            <div className="grid md:grid-cols-3 gap-8">
              {/* Panel 1: Agent Step Logs */}
              <div className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-xl p-6 md:col-span-1">
                <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-6">AI Agent Log</h3>
                
                {incidentTrace?.timeline ? (
                  <div className="relative border-l border-zinc-800 pl-5 ml-2.5 space-y-6">
                    {incidentTrace.timeline.map((step: any, idx: number) => (
                      <div key={idx} className="relative">
                        <div className={`absolute left-[-26px] top-1.5 w-3 h-3 rounded-full border border-zinc-950 ${
                          step.status === "completed" ? "bg-blue-500 animate-pulse" : "bg-red-500 animate-ping"
                        }`} />
                        <span className="text-[9px] font-mono text-zinc-600 block">{step.time}</span>
                        <h4 className="text-xs font-bold text-zinc-300">{step.event}</h4>
                        <p className="text-[10px] text-zinc-500 mt-1 leading-relaxed">{step.description}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="h-64 flex flex-col items-center justify-center text-center text-xs text-zinc-600">
                    <Terminal className="w-8 h-8 mb-2 opacity-50" />
                    <span>No active incident trace. Select a scenario in the header to trigger a self-healing demo.</span>
                  </div>
                )}
              </div>

              {/* Panel 2 & 3: Code Diff & Sandboxed Candidates */}
              <div className="md:col-span-2 space-y-8">
                {/* Code Diff Panel */}
                <div className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-xl p-6">
                  <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-4">Selector Code Audit Diff</h3>
                  {incidentTrace ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                        <div className="p-4 bg-red-950/20 border border-red-900/20 rounded-lg text-red-300">
                          <span className="text-[10px] text-red-500 block mb-1">OLD SELECTOR (FAILED)</span>
                          {incidentTrace.old_selector || ".price"}
                        </div>
                        <div className="p-4 bg-emerald-950/20 border border-emerald-900/20 rounded-lg text-emerald-300">
                          <span className="text-[10px] text-emerald-500 block mb-1">REPAIRED SELECTOR (DEPLOYED)</span>
                          {incidentTrace.new_selector || "TBD (Generating...)"}
                        </div>
                      </div>
                      <div className="p-4 bg-zinc-950 border border-zinc-900 rounded-lg text-xs">
                        <span className="text-[10px] font-bold text-zinc-500 block mb-1">AI AGENT REASONING SUMMARY</span>
                        <p className="text-zinc-400 font-light leading-relaxed">
                          {incidentTrace.reasoning || "Analyzing DOM tree structural elements..."}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="h-32 flex items-center justify-center text-xs text-zinc-600">
                      Waiting for incident trigger...
                    </div>
                  )}
                </div>

                {/* Candidate Sandbox Results */}
                <div className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-xl p-6">
                  <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-4">Validation Sandbox Candidates</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left">
                      <thead>
                        <tr className="border-b border-zinc-900 text-zinc-500">
                          <th className="pb-3">Candidate Selector</th>
                          <th className="pb-3">Strategy</th>
                          <th className="pb-3 text-right">Semantic Match</th>
                          <th className="pb-3 text-right">Coverage</th>
                          <th className="pb-3 text-right">Final Score</th>
                          <th className="pb-3 text-right">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-900/50">
                        {incidentTrace?.candidates && incidentTrace.candidates.length > 0 ? (
                          incidentTrace.candidates.map((cand: any, idx: number) => (
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
                                    : cand.status === "VALIDATED" 
                                    ? "bg-blue-500/10 text-blue-500" 
                                    : "bg-red-500/10 text-red-500"
                                }`}>
                                  {cand.status}
                                </span>
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan={6} className="py-8 text-center text-zinc-600">
                              No candidates evaluated yet. evaluation starts once selector changes occur.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "chat" && (
          <div className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-xl p-6 max-w-4xl mx-auto flex flex-col h-[500px]">
            <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-4 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-blue-500 animate-pulse" />
              Ask Your AI Reliability Engineer
            </h3>

            <div className="flex-1 overflow-y-auto space-y-4 mb-6 pr-2">
              {chatLog.map((log, idx) => (
                <div key={idx} className={`flex ${log.sender === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`p-4 rounded-xl max-w-[85%] text-xs leading-relaxed ${
                    log.sender === "user" 
                      ? "bg-blue-600 text-white font-medium" 
                      : "bg-zinc-950 border border-zinc-900 text-zinc-300 font-light"
                  }`}>
                    <div className="whitespace-pre-line">{log.text}</div>
                    
                    {log.actions && (
                      <div className="flex gap-2 mt-3 pt-3 border-t border-zinc-900">
                        {log.actions.map((act, idx) => (
                          <button
                            key={idx}
                            onClick={() => {
                              if (act.includes("Redesign") || act.includes("Drift")) handleTriggerChaos();
                              else if (act.includes("Run")) handleRunScraper();
                              else setActiveTab("versions");
                            }}
                            className="px-2.5 py-1 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 rounded text-[10px] text-zinc-400 hover:text-white transition"
                          >
                            {act}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {chatLoading && (
                <div className="flex justify-start">
                  <div className="p-4 bg-zinc-950 border border-zinc-900 text-zinc-500 rounded-xl text-xs flex items-center gap-2">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    Awaiting Reliability Triage...
                  </div>
                </div>
              )}
            </div>

            <form onSubmit={handleChatSend} className="flex gap-2">
              <input
                type="text"
                value={chatMessage}
                onChange={e => setChatMessage(e.target.value)}
                placeholder="Ask: 'What happened to my Nvidia scraper?' or 'Is my Amazon collector healthy?'..."
                className="flex-1 px-4 py-3 bg-zinc-950 border border-zinc-900 hover:border-zinc-805 focus:border-blue-500 focus:outline-none rounded-xl text-xs transition placeholder:text-zinc-650 text-zinc-200"
              />
              <button
                type="submit"
                className="px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl transition"
              >
                Query Agent
              </button>
            </form>
          </div>
        )}

        {activeTab === "versions" && (
          <div className="space-y-8">
            {/* Version History Table */}
            <div className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-xl p-6">
              <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-6">Published Collector Versions</h3>
              
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-zinc-900 text-zinc-500">
                      <th className="pb-3">Version</th>
                      <th className="pb-3">Deploy Reason</th>
                      <th className="pb-3">Active Selector</th>
                      <th className="pb-3">Status</th>
                      <th className="pb-3 text-right">Published At</th>
                      <th className="pb-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-900/50">
                    {selectedScraper?.versions ? (
                      selectedScraper.versions.map((ver: any, idx: number) => (
                        <tr key={idx} className="text-zinc-300">
                          <td className="py-3.5 font-bold">v{ver.version}</td>
                          <td className="py-3.5 font-light text-zinc-400">{ver.reason || "N/A"}</td>
                          <td className="py-3.5 font-mono text-zinc-400">{ver.selectors?.price || ".price"}</td>
                          <td className="py-3.5">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                              ver.status === "ACTIVE" 
                                ? "bg-emerald-500/10 text-emerald-500" 
                                : "bg-zinc-800/40 text-zinc-500"
                            }`}>
                              {ver.status}
                            </span>
                          </td>
                          <td className="py-3.5 text-right text-zinc-500">
                            {new Date(ver.created_at).toLocaleTimeString()}
                          </td>
                          <td className="py-3.5 text-right">
                            {ver.status !== "ACTIVE" && (
                              <button
                                onClick={() => handleRollback(ver.version)}
                                className="px-2 py-1 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-400 hover:text-white rounded transition text-[10px]"
                              >
                                Rollback to v{ver.version}
                              </button>
                            )}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="py-4 text-center text-zinc-600">
                          No version history loaded.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Audit Logs */}
            <div className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-xl p-6 max-w-3xl">
              <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-4 font-mono">Audited Event logs</h3>
              <div className="space-y-4 font-mono text-xs">
                {selectedScraper?.audit_logs ? (
                  selectedScraper.audit_logs.map((log: any, idx: number) => (
                    <div key={idx} className="p-3 bg-zinc-950 border border-zinc-900 rounded-lg flex items-center justify-between text-zinc-400">
                      <div>
                        <span className="text-blue-500 font-bold">[{log.event_type}]</span>
                        <span className="ml-2 font-light text-zinc-500 text-[11px]">
                          {JSON.stringify(log.details)}
                        </span>
                      </div>
                      <span className="text-[10px] text-zinc-600">
                        {new Date(log.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-4 text-zinc-600">No events audited.</div>
                )}
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
