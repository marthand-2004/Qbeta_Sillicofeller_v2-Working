import { createFileRoute } from "@tanstack/react-router";
import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Sparkles,
  Cpu,
  Send,
  PanelLeftClose,
  PanelLeftOpen,
  Copy,
  Download,
  CircuitBoard,
  Code2,
  Microchip,
} from "lucide-react";
import { useAuth } from "@/lib/auth/auth-context";

export const Route = createFileRoute("/_app/designer")({
  head: () => ({ meta: [{ title: "Designer — Silicofeller" }] }),
  component: DesignerPage,
});

type ChatMsg = { role: "you" | "ai"; text: string };

const SAMPLE_VERILOG = `// Silicofeller generated — 64-qubit surface code controller
module qpu_controller #(
  parameter QUBITS = 64,
  parameter FIDELITY_BPS = 9990
) (
  input  wire        clk_cryo,
  input  wire        rst_n,
  input  wire [7:0]  gate_op,
  input  wire [5:0]  target_q,
  output reg  [63:0] readout,
  output reg         ready
);
  // nearest-neighbour coupling map
  reg [5:0] coupling [0:QUBITS-1][0:3];
  always @(posedge clk_cryo or negedge rst_n) begin
    if (!rst_n) begin
      readout <= 64'b0;
      ready   <= 1'b0;
    end else begin
      // dispatch microwave pulse to target qubit
      readout <= readout ^ (64'b1 << target_q);
      ready   <= (gate_op != 8'h00);
    end
  end
endmodule`;

function DesignerPage() {
  const { user } = useAuth();
  const [prompt, setPrompt] = useState("");
  const [chatOpen, setChatOpen] = useState(true);
  const [view, setView] = useState<"chip" | "circuit" | "code">("chip");
  const [hasOutput, setHasOutput] = useState(false);
  const [messages, setMessages] = useState<ChatMsg[]>([
    {
      role: "ai",
      text: "Describe the quantum architecture you want to design — qubit count, topology, target gate fidelity.",
    },
  ]);

  const send = () => {
    if (!prompt.trim()) return;
    setMessages((m) => [
      ...m,
      { role: "you", text: prompt },
      {
        role: "ai",
        text: "Generated a 64-qubit surface-code layout with nearest-neighbour coupling. Estimated logical error rate 2.3e-6. Open the Chip, Circuit or Code tab on the right to inspect the design.",
      },
    ]);
    setPrompt("");
    setHasOutput(true);
  };

  const copyCode = () => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(SAMPLE_VERILOG);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="flex h-[calc(100vh-3.5rem)] w-full flex-col"
    >
      <div className="flex items-center justify-between gap-3 border-b border-border bg-background/60 px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">AI Designer</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Chat to generate quantum chip architectures. Inspect chip, circuit and HDL on the right.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="rounded-full">
            <Cpu className="mr-1.5 h-3 w-3" /> {user?.organization}
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setChatOpen((v) => !v)}
            className="rounded-full"
          >
            {chatOpen ? (
              <>
                <PanelLeftClose className="mr-1.5 h-4 w-4" /> Minimize chat
              </>
            ) : (
              <>
                <PanelLeftOpen className="mr-1.5 h-4 w-4" /> Show chat
              </>
            )}
          </Button>
        </div>
      </div>

      <div className="flex min-h-0 flex-1">
        <AnimatePresence initial={false}>
          {chatOpen && (
            <motion.aside
              key="chat"
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 420, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.25, ease: "easeInOut" }}
              className="flex h-full flex-col overflow-hidden border-r border-border bg-card/40"
            >
              <div className="flex items-center justify-between border-b border-border px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-foreground text-background">
                    <Sparkles className="h-3.5 w-3.5" />
                  </span>
                  <div>
                    <p className="text-sm font-medium text-foreground">Design Assistant</p>
                    <p className="text-[11px] text-muted-foreground">Quantum architect · online</p>
                  </div>
                </div>
              </div>
              <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
                {messages.map((m, i) => (
                  <div
                    key={i}
                    className={
                      m.role === "you"
                        ? "ml-auto max-w-[85%] rounded-2xl bg-foreground px-3.5 py-2 text-sm text-background"
                        : "max-w-[90%] rounded-2xl border border-border bg-card px-3.5 py-2 text-sm text-foreground"
                    }
                  >
                    {m.text}
                  </div>
                ))}
              </div>
              <div className="border-t border-border p-3">
                <Textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      send();
                    }
                  }}
                  placeholder="e.g. 128-qubit transmon array, 99.9% fidelity"
                  className="min-h-[64px] rounded-2xl"
                />
                <div className="mt-2 flex items-center justify-between">
                  <p className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                    <Sparkles className="h-3 w-3 text-accent" /> Enter to send
                  </p>
                  <Button onClick={send} size="sm" className="rounded-full px-4">
                    <Send className="mr-1.5 h-3.5 w-3.5" /> Send
                  </Button>
                </div>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        <section className="flex min-w-0 flex-1 flex-col bg-background">
          <Tabs value={view} onValueChange={(v) => setView(v as typeof view)} className="flex flex-1 flex-col">
            <div className="flex items-center justify-between border-b border-border px-6 py-3">
              <TabsList className="rounded-full bg-secondary p-1">
                <TabsTrigger value="chip" className="rounded-full px-4 text-xs">
                  <Microchip className="mr-1.5 h-3.5 w-3.5" /> Fabricated Chip
                </TabsTrigger>
                <TabsTrigger value="circuit" className="rounded-full px-4 text-xs">
                  <CircuitBoard className="mr-1.5 h-3.5 w-3.5" /> Circuit
                </TabsTrigger>
                <TabsTrigger value="code" className="rounded-full px-4 text-xs">
                  <Code2 className="mr-1.5 h-3.5 w-3.5" /> Code
                </TabsTrigger>
              </TabsList>
              {view === "code" && hasOutput && (
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={copyCode} className="rounded-full">
                    <Copy className="mr-1.5 h-3.5 w-3.5" /> Copy
                  </Button>
                  <Button variant="outline" size="sm" className="rounded-full">
                    <Download className="mr-1.5 h-3.5 w-3.5" /> .v
                  </Button>
                </div>
              )}
            </div>

            <div className="min-h-0 flex-1 overflow-auto p-6">
              {!hasOutput ? (
                <EmptyState />
              ) : (
                <>
                  <TabsContent value="chip" className="mt-0">
                    <ChipView />
                  </TabsContent>
                  <TabsContent value="circuit" className="mt-0">
                    <CircuitView />
                  </TabsContent>
                  <TabsContent value="code" className="mt-0">
                    <CodeView />
                  </TabsContent>
                </>
              )}
            </div>
          </Tabs>
        </section>
      </div>
    </motion.div>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full min-h-[400px] flex-col items-center justify-center text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-border bg-card">
        <Sparkles className="h-6 w-6 text-accent" />
      </div>
      <h2 className="mt-4 text-lg font-semibold text-foreground">No design yet</h2>
      <p className="mt-1 max-w-sm text-sm text-muted-foreground">
        Describe your quantum architecture in the chat. The fabricated chip, circuit and HDL will appear here.
      </p>
    </div>
  );
}

function ChipView() {
  return (
    <Card className="rounded-3xl border-border p-6 shadow-none">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Fabricated Layout
          </p>
          <h3 className="mt-1 text-lg font-semibold text-foreground">QPU-64 · Surface Code</h3>
        </div>
        <Badge variant="secondary" className="rounded-full">7nm · Cryo</Badge>
      </div>
      <div className="mt-6 overflow-hidden rounded-2xl border border-border bg-[#0A0A0A] p-6">
        <svg viewBox="0 0 360 360" className="mx-auto h-[360px] w-full max-w-[420px]">
          <defs>
            <linearGradient id="die" x1="0" x2="1" y1="0" y2="1">
              <stop offset="0%" stopColor="#1a1a2e" />
              <stop offset="100%" stopColor="#0a0a0a" />
            </linearGradient>
          </defs>
          <rect x="20" y="20" width="320" height="320" rx="18" fill="url(#die)" stroke="#6D5AF0" strokeOpacity="0.4" />
          {Array.from({ length: 8 }).map((_, r) =>
            Array.from({ length: 8 }).map((_, c) => {
              const x = 50 + c * 35;
              const y = 50 + r * 35;
              return (
                <g key={`${r}-${c}`}>
                  <rect x={x - 8} y={y - 8} width="16" height="16" rx="3" fill="#6D5AF0" fillOpacity="0.18" stroke="#8B7AF7" strokeOpacity="0.6" />
                  <circle cx={x} cy={y} r="2.5" fill="#8B7AF7" />
                  {c < 7 && <line x1={x + 8} y1={y} x2={x + 27} y2={y} stroke="#6D5AF0" strokeOpacity="0.45" strokeWidth="1" />}
                  {r < 7 && <line x1={x} y1={y + 8} x2={x} y2={y + 27} stroke="#6D5AF0" strokeOpacity="0.45" strokeWidth="1" />}
                </g>
              );
            }),
          )}
          {[0, 1, 2, 3].map((i) => (
            <rect key={i} x={30 + i * 80} y={330} width="20" height="6" rx="1" fill="#8B7AF7" fillOpacity="0.7" />
          ))}
        </svg>
      </div>
      <div className="mt-5 grid grid-cols-3 gap-3 text-center">
        {[
          { label: "Qubits", value: "64" },
          { label: "Fidelity", value: "99.9%" },
          { label: "Coherence", value: "180μs" },
        ].map((s) => (
          <div key={s.label} className="rounded-2xl border border-border bg-card p-3">
            <p className="text-[11px] text-muted-foreground">{s.label}</p>
            <p className="mt-0.5 text-lg font-semibold text-foreground">{s.value}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function CircuitView() {
  return (
    <Card className="rounded-3xl border-border p-6 shadow-none">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Logical Circuit
          </p>
          <h3 className="mt-1 text-lg font-semibold text-foreground">Entanglement Routing</h3>
        </div>
        <Badge variant="secondary" className="rounded-full">4 qubits · 6 gates</Badge>
      </div>
      <div className="mt-6 overflow-x-auto rounded-2xl border border-border bg-card p-6">
        <svg viewBox="0 0 520 220" className="h-[220px] w-full min-w-[480px]">
          {[0, 1, 2, 3].map((q) => {
            const y = 35 + q * 50;
            return (
              <g key={q}>
                <text x="10" y={y + 4} fontSize="11" fill="#6b7280" fontFamily="ui-monospace">
                  q{q}
                </text>
                <line x1="40" y1={y} x2="500" y2={y} stroke="#0A0A0A" strokeWidth="1" />
              </g>
            );
          })}
          {[
            { x: 90, q: 0, label: "H" },
            { x: 90, q: 2, label: "H" },
            { x: 170, q: 1, label: "X" },
            { x: 330, q: 3, label: "T" },
            { x: 410, q: 0, label: "M" },
          ].map((g, i) => {
            const y = 35 + g.q * 50;
            return (
              <g key={i}>
                <rect x={g.x - 14} y={y - 14} width="28" height="28" rx="6" fill="#FFFFFF" stroke="#0A0A0A" />
                <text x={g.x} y={y + 4} fontSize="12" textAnchor="middle" fill="#0A0A0A" fontWeight="600">
                  {g.label}
                </text>
              </g>
            );
          })}
          {/* CNOT control/target */}
          <g>
            <circle cx={250} cy={35} r="5" fill="#0A0A0A" />
            <line x1={250} y1={35} x2={250} y2={135} stroke="#0A0A0A" strokeWidth="1" />
            <circle cx={250} cy={135} r="11" fill="#FFFFFF" stroke="#0A0A0A" />
            <line x1={241} y1={135} x2={259} y2={135} stroke="#0A0A0A" />
            <line x1={250} y1={126} x2={250} y2={144} stroke="#0A0A0A" />
          </g>
          <g>
            <circle cx={370} cy={85} r="5" fill="#6D5AF0" />
            <line x1={370} y1={85} x2={370} y2={185} stroke="#6D5AF0" strokeWidth="1" />
            <circle cx={370} cy={185} r="11" fill="#FFFFFF" stroke="#6D5AF0" />
            <line x1={361} y1={185} x2={379} y2={185} stroke="#6D5AF0" />
            <line x1={370} y1={176} x2={370} y2={194} stroke="#6D5AF0" />
          </g>
        </svg>
      </div>
    </Card>
  );
}

function CodeView() {
  return (
    <Card className="overflow-hidden rounded-3xl border-border p-0 shadow-none">
      <div className="flex items-center justify-between border-b border-border bg-card px-5 py-3">
        <div className="flex items-center gap-2">
          <Code2 className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium text-foreground">qpu_controller.v</span>
        </div>
        <Badge variant="secondary" className="rounded-full text-[10px]">Verilog</Badge>
      </div>
      <pre className="overflow-auto bg-[#0A0A0A] p-5 text-[12.5px] leading-relaxed text-[#E6E6F0]">
        <code className="font-mono">{SAMPLE_VERILOG}</code>
      </pre>
    </Card>
  );
}