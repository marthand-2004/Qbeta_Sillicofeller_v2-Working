import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "motion/react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowUpRight, Cpu, Layers, Sparkles, Zap, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchHealth, type HealthResponse } from "@/lib/api/backend";

export const Route = createFileRoute("/_app/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard — Silicofeller" }] }),
  component: DashboardPage,
});

function DashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [healthError, setHealthError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((e: Error) => setHealthError(e.message))
      .finally(() => setHealthLoading(false));
  }, []);

  const stats = [
    { label: "Max Qubits", value: health ? String(health.max_qubits) : "—", icon: Cpu, hint: "per design" },
    { label: "Backend", value: health ? health.version : "—", icon: Zap, hint: health?.status ?? "checking…" },
    { label: "Qiskit Metal", value: health ? health.qiskit_metal : "—", icon: Layers, hint: health?.metal_version ?? "—" },
    { label: "ML Intent", value: health ? health.ml_intent : "—", icon: Sparkles, hint: "intent classifier" },
  ];

  return (
    <div className="mx-auto w-full max-w-7xl px-6 py-10">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">Dashboard</h1>
          <p className="mt-1 text-sm text-muted-foreground">Welcome back. Here's a snapshot of your quantum design workspace.</p>
        </div>
        <Button asChild className="h-10 rounded-full px-5">
          <Link to="/designer">Open Designer <ArrowUpRight className="ml-1 h-4 w-4" /></Link>
        </Button>
      </motion.div>

      {/* Backend status cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s, i) => (
          <motion.div key={s.label} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: i * 0.05 }} whileHover={{ y: -2 }}>
            <Card className="rounded-2xl border-border p-5 shadow-none">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{s.label}</span>
                {healthLoading ? <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" /> : <s.icon className="h-4 w-4 text-accent" />}
              </div>
              <div className="mt-3 text-2xl font-semibold text-foreground truncate">{healthLoading ? "…" : s.value}</div>
              <div className="mt-1 text-xs text-muted-foreground">{s.hint}</div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Backend health detail */}
      <Card className="mt-6 rounded-2xl border-border p-6 shadow-none">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-foreground">Backend Pipeline</h2>
          {healthLoading ? (
            <Badge variant="secondary" className="rounded-full"><Loader2 className="mr-1 h-3 w-3 animate-spin" />Connecting…</Badge>
          ) : healthError ? (
            <Badge variant="secondary" className="rounded-full text-red-500"><XCircle className="mr-1 h-3 w-3" />Offline</Badge>
          ) : (
            <Badge variant="secondary" className="rounded-full text-green-600"><CheckCircle2 className="mr-1 h-3 w-3" />Online</Badge>
          )}
        </div>
        {healthError && (
          <p className="text-sm text-red-500 mb-3">⚠ Cannot reach backend: {healthError}. Make sure <code className="text-xs">python app.py</code> is running in the <code className="text-xs">backend/</code> directory.</p>
        )}
        {health && (
          <div className="flex flex-wrap gap-2">
            {health.pipeline.map((step) => (
              <span key={step} className="rounded-full border border-border bg-secondary px-3 py-1 text-xs font-medium text-foreground">{step}</span>
            ))}
          </div>
        )}
      </Card>

      <Card className="mt-6 rounded-2xl border-border p-8 shadow-none">
        <h2 className="text-lg font-semibold text-foreground">Get started</h2>
        <p className="mt-1 text-sm text-muted-foreground">Generate your first quantum chip architecture from a natural-language prompt.</p>
        <Button asChild className="mt-5 h-10 rounded-full px-5"><Link to="/designer">New design</Link></Button>
      </Card>
    </div>
  );
}