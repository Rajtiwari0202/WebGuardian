"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { 
  Shield, ArrowLeft, Building, MessageSquare, Webhook, 
  Key, Plus, Trash2, CheckCircle, RefreshCw, Send, Lock
} from "lucide-react";
import { API_BASE_URL } from "@/config/api";

export default function SettingsPage() {
  const [tenant, setTenant] = useState<any>(null);
  const [slack, setSlack] = useState<any>({ connected: false });
  const [webhooks, setWebhooks] = useState<any[]>([]);
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  
  // Forms & Modals
  const [slackChannel, setSlackChannel] = useState("alerts-data-ops");
  const [slackWebhookUrl, setSlackWebhookUrl] = useState("");
  const [isSavingSlack, setIsSavingSlack] = useState(false);
  const [slackStatusMsg, setSlackStatusMsg] = useState<string | null>(null);

  const [newWebhookUrl, setNewWebhookUrl] = useState("");
  const [newWebhookSecret, setNewWebhookSecret] = useState("");
  const [isCreatingWebhook, setIsCreatingWebhook] = useState(false);

  const [newKeyName, setNewKeyName] = useState("");
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const [tRes, sRes, wRes, kRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/integrations/tenants`),
        fetch(`${API_BASE_URL}/api/integrations/slack`),
        fetch(`${API_BASE_URL}/api/integrations/webhooks`),
        fetch(`${API_BASE_URL}/api/integrations/api-keys`),
      ]);

      if (tRes.ok) setTenant(await tRes.json());
      if (sRes.ok) setSlack(await sRes.json());
      if (wRes.ok) setWebhooks(await wRes.json());
      if (kRes.ok) setApiKeys(await kRes.json());
    } catch (err) {
      console.error("Error fetching settings:", err);
    }
  };

  const handleSaveSlack = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!slackWebhookUrl.trim()) return;
    setIsSavingSlack(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/integrations/slack`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          channel_name: slackChannel,
          webhook_url: slackWebhookUrl,
          test_dispatch: true
        })
      });
      const data = await res.json();
      setSlackStatusMsg(data.message);
      fetchSettings();
      setTimeout(() => setSlackStatusMsg(null), 4000);
    } catch (err) {
      setSlackStatusMsg("Error connecting Slack webhook.");
    } finally {
      setIsSavingSlack(false);
    }
  };

  const handleCreateWebhook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWebhookUrl.trim()) return;
    setIsCreatingWebhook(true);
    try {
      await fetch(`${API_BASE_URL}/api/integrations/webhooks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: newWebhookUrl,
          secret: newWebhookSecret || undefined,
          events: ["failure.detected", "repair.completed"]
        })
      });
      setNewWebhookUrl("");
      setNewWebhookSecret("");
      fetchSettings();
    } catch (err) {
      console.error(err);
    } finally {
      setIsCreatingWebhook(false);
    }
  };

  const handleDeleteWebhook = async (id: string) => {
    try {
      await fetch(`${API_BASE_URL}/api/integrations/webhooks/${id}`, { method: "DELETE" });
      fetchSettings();
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/integrations/api-keys`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newKeyName })
      });
      const data = await res.json();
      setGeneratedKey(data.api_key);
      setNewKeyName("");
      fetchSettings();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-[#030303] text-zinc-100 font-sans scanline">
      {/* Header */}
      <header className="border-b border-zinc-900 bg-zinc-950/40 backdrop-blur-md px-6 py-4 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="p-2 bg-zinc-950 border border-zinc-900 hover:bg-zinc-900 rounded-lg text-zinc-400 hover:text-zinc-200 transition">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-sm font-bold text-white flex items-center gap-1.5">
              WebGuardian AI
              <span className="text-[10px] font-bold text-indigo-500 px-1.5 py-0.5 bg-indigo-500/10 rounded">SETTINGS</span>
            </h1>
            <p className="text-[10px] text-zinc-500">Enterprise Integrations & Multi-Tenant Management</p>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10 space-y-12">
        
        {/* 1. Organization & Tenant Profile */}
        <section className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-2xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-zinc-900 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-blue-600/10 border border-blue-500/20 rounded-xl text-blue-500">
                <Building className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-white">Organization & Subscription</h2>
                <p className="text-xs text-zinc-500">Workspace data isolation & quota limits</p>
              </div>
            </div>
            <span className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold rounded-full uppercase tracking-wider">
              {tenant?.plan_tier || "Scale"} Plan
            </span>
          </div>

          <div className="grid sm:grid-cols-3 gap-4 text-xs font-mono">
            <div className="p-4 bg-zinc-950 border border-zinc-900 rounded-xl">
              <span className="text-[10px] text-zinc-600 block mb-1">TENANT NAME</span>
              <span className="font-bold text-zinc-300">{tenant?.name || "Acme Data Labs"}</span>
            </div>
            <div className="p-4 bg-zinc-950 border border-zinc-900 rounded-xl">
              <span className="text-[10px] text-zinc-600 block mb-1">TENANT SLUG</span>
              <span className="font-bold text-zinc-300">{tenant?.slug || "acme-data"}</span>
            </div>
            <div className="p-4 bg-zinc-950 border border-zinc-900 rounded-xl">
              <span className="text-[10px] text-zinc-600 block mb-1">MAX ACTIVE COLLECTORS</span>
              <span className="font-bold text-blue-400">{tenant?.max_collectors || 150} Collectors</span>
            </div>
          </div>
        </section>

        {/* 2. Slack Block Kit Integration */}
        <section className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-2xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-zinc-900 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-emerald-600/10 border border-emerald-500/20 rounded-xl text-emerald-500">
                <MessageSquare className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-white">Slack Incident Notifications</h2>
                <p className="text-xs text-zinc-500">Interactive alert cards with 1-click self-healing approvals</p>
              </div>
            </div>
            <span className={`px-2.5 py-1 rounded text-[10px] font-bold ${
              slack.connected ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-zinc-900 text-zinc-500"
            }`}>
              {slack.connected ? "● Connected" : "Not Configured"}
            </span>
          </div>

          <form onSubmit={handleSaveSlack} className="space-y-4 max-w-xl">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[10px] font-mono text-zinc-500 uppercase block mb-1.5">Target Slack Channel</label>
                <input
                  type="text"
                  value={slackChannel}
                  onChange={e => setSlackChannel(e.target.value)}
                  placeholder="e.g. alerts-data-ops"
                  className="w-full px-3.5 py-2.5 bg-zinc-950 border border-zinc-900 rounded-xl text-xs text-zinc-300 focus:border-emerald-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-[10px] font-mono text-zinc-500 uppercase block mb-1.5">Incoming Webhook URL</label>
                <input
                  type="url"
                  value={slackWebhookUrl}
                  onChange={e => setSlackWebhookUrl(e.target.value)}
                  placeholder="https://hooks.slack.com/services/..."
                  className="w-full px-3.5 py-2.5 bg-zinc-950 border border-zinc-900 rounded-xl text-xs text-zinc-300 focus:border-emerald-500 focus:outline-none"
                />
              </div>
            </div>

            {slackStatusMsg && (
              <div className="text-xs text-emerald-400 flex items-center gap-1.5 font-mono">
                <CheckCircle className="w-3.5 h-3.5" />
                {slackStatusMsg}
              </div>
            )}

            <button
              type="submit"
              disabled={isSavingSlack}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl transition flex items-center gap-2 disabled:opacity-50"
            >
              {isSavingSlack ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
              Save & Send Test Alert
            </button>
          </form>
        </section>

        {/* 3. Custom Webhook Streams */}
        <section className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-2xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-zinc-900 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-purple-600/10 border border-purple-500/20 rounded-xl text-purple-500">
                <Webhook className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-white">Outbound Webhooks</h2>
                <p className="text-xs text-zinc-500">Stream failure and recovery payloads to Datadog or custom services</p>
              </div>
            </div>
          </div>

          <form onSubmit={handleCreateWebhook} className="grid sm:grid-cols-3 gap-3">
            <input
              type="url"
              value={newWebhookUrl}
              onChange={e => setNewWebhookUrl(e.target.value)}
              placeholder="https://api.yourdomain.com/webhooks/webguardian"
              className="sm:col-span-2 px-3.5 py-2.5 bg-zinc-950 border border-zinc-900 rounded-xl text-xs text-zinc-300 focus:border-purple-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={isCreatingWebhook}
              className="px-4 py-2.5 bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs rounded-xl transition flex items-center justify-center gap-1.5 disabled:opacity-50"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Endpoint
            </button>
          </form>

          <div className="divide-y divide-zinc-900 text-xs">
            {webhooks.length > 0 ? (
              webhooks.map((w: any) => (
                <div key={w.id} className="py-3 flex items-center justify-between">
                  <div>
                    <span className="font-mono text-zinc-300 block">{w.url}</span>
                    <span className="text-[10px] text-zinc-600 font-mono">Events: {w.events.join(", ")}</span>
                  </div>
                  <button
                    onClick={() => handleDeleteWebhook(w.id)}
                    className="p-1.5 text-zinc-600 hover:text-red-400 transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            ) : (
              <p className="py-4 text-center text-xs text-zinc-600">No custom webhooks registered.</p>
            )}
          </div>
        </section>

        {/* 4. Developer API Keys */}
        <section className="border border-zinc-900 bg-[#0c0c0e]/80 rounded-2xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-zinc-900 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-amber-600/10 border border-amber-500/20 rounded-xl text-amber-500">
                <Key className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-white">Developer API Keys</h2>
                <p className="text-xs text-zinc-500">Authenticate external CI/CD pipelines & scraper schedulers</p>
              </div>
            </div>
          </div>

          {generatedKey && (
            <div className="p-4 bg-amber-950/20 border border-amber-900/50 rounded-xl text-xs space-y-1">
              <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider block">⚠️ SAVE YOUR API KEY (SHOWN ONCE)</span>
              <code className="p-2 bg-black/60 rounded block font-mono text-amber-200 select-all">{generatedKey}</code>
            </div>
          )}

          <form onSubmit={handleCreateApiKey} className="flex gap-3 max-w-md">
            <input
              type="text"
              value={newKeyName}
              onChange={e => setNewKeyName(e.target.value)}
              placeholder="Key description (e.g. Prod Pipeline Cron)"
              className="flex-1 px-3.5 py-2.5 bg-zinc-950 border border-zinc-900 rounded-xl text-xs text-zinc-300 focus:border-amber-500 focus:outline-none"
            />
            <button
              type="submit"
              className="px-4 py-2.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 font-bold text-xs rounded-xl border border-zinc-800 transition"
            >
              Generate Key
            </button>
          </form>

          <div className="divide-y divide-zinc-900 text-xs">
            {apiKeys.length > 0 ? (
              apiKeys.map((k: any) => (
                <div key={k.id} className="py-3 flex items-center justify-between">
                  <div>
                    <span className="font-bold text-zinc-300">{k.name}</span>
                    <span className="ml-3 font-mono text-[10px] text-zinc-500">{k.key_prefix}</span>
                  </div>
                  <span className="text-[10px] text-zinc-600">{new Date(k.created_at).toLocaleDateString()}</span>
                </div>
              ))
            ) : (
              <p className="py-4 text-center text-xs text-zinc-600">No active API keys.</p>
            )}
          </div>
        </section>

      </main>
    </div>
  );
}
