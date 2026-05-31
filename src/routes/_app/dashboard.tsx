import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "motion/react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowUpRight, Cpu, Layers, Sparkles, Zap } from "lucide-react";

export const Route = createFileRoute("/_app/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard — Silicofeller" }] }),
  component: DashboardPage,
});

const stats = [
  { label: "Active Designs", value: "24", icon: Cpu, hint: "+3 this week" },
  { label: "Credits Used", value: "8,210", icon: Zap, hint: "82% of quota" },
  { label: "Architectures", value: "324", icon: Layers, hint: "+18 this month" },
  { label: "AI Sessions", value: "1,204", icon: Sparkles, hint: "+12% MoM" },
];

function DashboardPage() {
  return (
    <div className="mx-auto w-full max-w-7xl px-6 py-10">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mb-8 flex flex-wrap items-end justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">Dashboard</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Welcome back. Here's a snapshot of your quantum design workspace.
          </p>
        </div>
        <Button asChild className="h-10 rounded-full px-5">
          <Link to="/billing">
            View Billing <ArrowUpRight className="ml-1 h-4 w-4" />
          </Link>
        </Button>
      </motion.div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: i * 0.05 }}
            whileHover={{ y: -2 }}
          >
            <Card className="rounded-2xl border-border p-5 shadow-none">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  {s.label}
                </span>
                <s.icon className="h-4 w-4 text-accent" />
              </div>
              <div className="mt-3 text-2xl font-semibold text-foreground">{s.value}</div>
              <div className="mt-1 text-xs text-muted-foreground">{s.hint}</div>
            </Card>
          </motion.div>
        ))}
      </div>
      <Card className="mt-8 rounded-2xl border-border p-8 shadow-none">
        <h2 className="text-lg font-semibold text-foreground">Get started</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Generate your first quantum architecture from a natural-language prompt.
        </p>
        <Button className="mt-5 h-10 rounded-full px-5">New design</Button>
      </Card>
    </div>
  );
}