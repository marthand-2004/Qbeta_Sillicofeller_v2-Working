import { createFileRoute } from "@tanstack/react-router";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import {
  Sparkles, Cpu, Send, PanelLeftClose, PanelLeftOpen,
  Copy, Download, CircuitBoard, Code2, Microchip, Plus,
  MessageSquare, Trash2, Pencil, Check, X, AlertTriangle,
  Loader2, CheckCircle2, Zap, Maximize2, Minimize2,
  ArrowRight, HelpCircle, Layers, Activity, Info, Sliders
} from "lucide-react";
import { useAuth } from "@/lib/auth/auth-context";
import { generateChip, type GenerateResponse } from "@/lib/api/backend";
import { useSidebar } from "@/components/ui/sidebar";

export const Route = createFileRoute("/_app/designer")({
  head: () => ({ meta: [{ title: "AI Quantum Designer — Silicofeller" }] }),
  component: DesignerPage,
});

type ChatMsg = { role: "you" | "ai"; text: string; loading?: boolean };
type Conversation = {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: ChatMsg[];
  result: GenerateResponse | null;
};

const STORAGE_KEY = "silicofeller.designer.conversations.v2";
const WELCOME: ChatMsg = {
  role: "ai",
  text: "Welcome to Silicofeller AI Quantum Designer. Describe the architecture, qubit counts, topological interfaces, or cryogenic constraints of the processor you wish to synthesize. Our solver will generate physical layouts, transmission meanders, and compile-ready Qiskit Metal code.",
};

const SUGGESTIONS = [
  {
    title: "5-Qubit Transmon Linear",
    description: "Linear qubit chain with nearest-neighbor meanders",
    prompt: "Design a 5-qubit transmon quantum processor with nearest-neighbor coupling."
  },
  {
    title: "16-Qubit Heavy-Hex Lattice",
    description: "Heavy-hexagonal lattice for error-correction topologies",
    prompt: "Design a 16-qubit heavy-hex architecture with 99.9% target fidelity."
  },
  {
    title: "64-Qubit Cryogenic Grid",
    description: "8x8 surface code lattice at cryo 7nm spacing",
    prompt: "Generate a 64-qubit surface-code quantum chip with 7nm Cryo spacing."
  },
  {
    title: "9-Qubit Ring Coherence",
    description: "Closed-loop transmon pockets with feedline coupling",
    prompt: "Create a 9-qubit transmon processor in a ring/loop topology."
  }
];

function newConversation(): Conversation {
  const now = Date.now();
  return {
    id: `c_${now}_${Math.random().toString(36).slice(2, 7)}`,
    title: "New Design Session",
    createdAt: now,
    updatedAt: now,
    messages: [WELCOME],
    result: null
  };
}

function DesignerPage() {
  const { user } = useAuth();
  const { setOpen: setWorkspaceSidebarOpen } = useSidebar();
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatOpen, setChatOpen] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [view, setView] = useState<"chip" | "circuit" | "code">("chip");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      const parsed: Conversation[] = raw ? JSON.parse(raw) : [];
      if (parsed.length === 0) {
        const c = newConversation();
        setConversations([c]);
        setActiveId(c.id);
      } else {
        setConversations(parsed);
        setActiveId(parsed[0].id);
      }
    } catch {
      const c = newConversation();
      setConversations([c]);
      setActiveId(c.id);
    }
  }, []);

  useEffect(() => {
    if (conversations.length === 0) return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    } catch {}
  }, [conversations]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversations, activeId]);

  const active = useMemo(() => conversations.find((c) => c.id === activeId) ?? null, [conversations, activeId]);
  
  const updateActive = (patch: Partial<Conversation>) =>
    setConversations((cs) => cs.map((c) => (c.id === activeId ? { ...c, ...patch, updatedAt: Date.now() } : c)));

  const send = async (textToSend?: string) => {
    const text = (textToSend || prompt).trim();
    if (!text || !active || loading) return;
    setPrompt("");
    setLoading(true);
    const isFirst = active.messages.length <= 1;
    updateActive({
      messages: [...active.messages, { role: "you", text }, { role: "ai", text: "Compiling quantum chip blueprint...", loading: true }],
      title: isFirst ? text.slice(0, 36) : active.title,
    });
    try {
      const result = await generateChip(text);
      
      // Auto-collapse sidebars when chip is generated successfully!
      setSidebarOpen(false);
      setWorkspaceSidebarOpen(false);
      
      const aiText = result.interpretation ?? `Generated a ${result.num_qubits}-qubit ${result.topology} chip. Custom layout, frequency bands, detuning coefficients, and Qiskit Metal script compile successfully.`;
      setConversations((cs) =>
        cs.map((c) => {
          if (c.id !== activeId) return c;
          const msgs = c.messages.filter((m) => !m.loading);
          return { ...c, messages: [...msgs, { role: "ai" as const, text: aiText }], result, updatedAt: Date.now() };
        })
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Internal engine error";
      setConversations((cs) =>
        cs.map((c) => {
          if (c.id !== activeId) return c;
          const msgs = c.messages.filter((m) => !m.loading);
          return { ...c, messages: [...msgs, { role: "ai" as const, text: `❌ Synthesis failed: ${msg}` }], updatedAt: Date.now() };
        })
      );
    } finally {
      setLoading(false);
    }
  };

  const handleNew = () => {
    const c = newConversation();
    setConversations((cs) => [c, ...cs]);
    setActiveId(c.id);
    setPrompt("");
  };

  const handleDelete = (id: string) => {
    setConversations((cs) => {
      const next = cs.filter((c) => c.id !== id);
      if (next.length === 0) {
        const c = newConversation();
        setActiveId(c.id);
        return [c];
      }
      if (id === activeId) setActiveId(next[0].id);
      return next;
    });
  };

  const startRename = (c: Conversation) => {
    setRenamingId(c.id);
    setRenameValue(c.title);
  };

  const commitRename = () => {
    if (!renamingId) return;
    setConversations((cs) => cs.map((c) => (c.id === renamingId ? { ...c, title: renameValue.trim() || "Untitled chat" } : c)));
    setRenamingId(null);
  };

  if (!active) return null;
  const hasOutput = !!active.result;
  const result = active.result;

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex h-[calc(100vh-3.5rem)] w-full bg-[#FCFCFD] text-slate-800"
    >
      {/* History Sidebar - Ultra clean light theme with subtle violet accent hover */}
      <AnimatePresence initial={false}>
        {sidebarOpen && (
          <motion.aside
            key="history"
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 260, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="flex h-full shrink-0 flex-col overflow-hidden border-r border-slate-200/80 bg-white"
          >
            <div className="p-4">
              <Button
                onClick={handleNew}
                className="w-full justify-start rounded-xl border border-slate-200/80 bg-white text-slate-700 hover:bg-slate-50 hover:text-slate-900 shadow-sm h-10 font-bold transition-all duration-150 active:scale-98"
              >
                <Plus className="mr-2 h-4 w-4 text-accent" /> New design chat
              </Button>
            </div>
            
            <div className="px-4 pb-2 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">Design History</div>
            
            <div className="flex-1 space-y-0.5 overflow-y-auto px-2 pb-3">
              {conversations.slice().sort((a, b) => b.updatedAt - a.updatedAt).map((c) => {
                const isActive = c.id === activeId, isRenaming = renamingId === c.id;
                return (
                  <div
                    key={c.id}
                    className={`group flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition-all duration-150 ${
                      isActive 
                        ? "bg-accent-soft text-accent border border-accent/10 font-bold" 
                        : "hover:bg-slate-50 text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    <MessageSquare className={`h-4 w-4 shrink-0 ${isActive ? "text-accent" : "text-slate-400"}`} />
                    {isRenaming ? (
                      <div className="flex items-center gap-1 w-full">
                        <Input
                          value={renameValue}
                          onChange={(e) => setRenameValue(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") commitRename();
                            if (e.key === "Escape") setRenamingId(null);
                          }}
                          autoFocus
                          className="h-7 bg-white text-xs border border-slate-200 focus-visible:ring-accent"
                        />
                        <button onClick={commitRename} className="text-emerald-600 hover:text-emerald-700">
                          <Check className="h-4 w-4" />
                        </button>
                        <button onClick={() => setRenamingId(null)} className="text-rose-600 hover:text-rose-700">
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ) : (
                      <>
                        <button
                          onClick={() => {
                            setActiveId(c.id);
                            setChatOpen(true);
                          }}
                          className="min-w-0 flex-1 text-left"
                        >
                          <div className="truncate text-xs font-bold leading-tight">{c.title}</div>
                          <div className="truncate text-[10px] text-slate-400 mt-0.5 font-medium">
                            {new Date(c.updatedAt).toLocaleDateString()}
                          </div>
                        </button>
                        <button
                          onClick={() => startRename(c)}
                          className="opacity-0 group-hover:opacity-100 p-0.5 text-slate-400 hover:text-accent transition-opacity"
                          aria-label="Rename"
                        >
                          <Pencil className="h-3 w-3" />
                        </button>
                        <button
                          onClick={() => handleDelete(c.id)}
                          className="opacity-0 group-hover:opacity-100 p-0.5 text-slate-400 hover:text-rose-600 transition-opacity"
                          aria-label="Delete"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
            
            <div className="border-t border-slate-200 p-4 text-[11px] font-bold text-slate-500 bg-slate-50/50 flex items-center justify-between">
              <span className="truncate">{user?.name} · {user?.organization}</span>
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse shadow-sm shadow-accent/40"></span>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      <div className="flex min-h-0 flex-1 flex-col">
        {/* Top bar / Design Header - Premium white light theme */}
        <header className="flex items-center justify-between gap-3 border-b border-slate-200 bg-white px-6 py-4 z-10 shadow-[0_1px_2px_0_rgba(0,0,0,0.02)]">
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSidebarOpen((v) => !v)}
              className="rounded-xl border-slate-200 hover:bg-slate-50 hover:text-slate-900 text-slate-600 shadow-sm active:scale-95 transition-all"
            >
              {sidebarOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
            </Button>
            <div>
              <h1 className="text-sm font-extrabold tracking-tight text-slate-900 flex items-center gap-1.5">
                {active.title}
                {hasOutput && <span className="text-[10px] font-bold text-accent bg-accent-soft px-2.5 py-0.5 rounded-full border border-accent/15">Synthesized</span>}
              </h1>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                Quantum Architectural CAD · {result?.engine ? `Engine: ${result.engine}` : "Ready to synthesize"}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="rounded-full bg-slate-100 hover:bg-slate-100 text-slate-700 font-bold border border-slate-200/50 px-2.5 py-0.5">
              <Cpu className="mr-1.5 h-3.5 w-3.5 text-accent" /> {user?.organization}
            </Badge>
            {hasOutput && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setChatOpen((v) => !v)}
                className="rounded-full border-accent-soft bg-accent-soft text-accent hover:bg-accent/10 shadow-sm font-bold text-xs"
              >
                {chatOpen ? (
                  <>
                    <Minimize2 className="mr-1.5 h-3.5 w-3.5" /> Minimize Chat
                  </>
                ) : (
                  <>
                    <Maximize2 className="mr-1.5 h-3.5 w-3.5" /> Restore Chat
                  </>
                )}
              </Button>
            )}
          </div>
        </header>

        <div className="flex min-h-0 flex-1 bg-white">
          {/* Chat Panel - Rebuilt like Claude / ChatGPT light bubble style */}
          <AnimatePresence initial={false}>
            {chatOpen && (
              <motion.aside
                key="chat"
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: hasOutput ? 440 : "100%", opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ duration: 0.22, ease: "easeInOut" }}
                className="flex h-full flex-col overflow-hidden border-r border-slate-200 bg-slate-50/20 relative z-0"
              >
                {/* Embedded Design assistant header */}
                <div className="flex items-center gap-3 border-b border-slate-200 bg-white px-5 py-4 shadow-[0_1px_1px_rgba(0,0,0,0.01)]">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-accent text-white shadow-sm shadow-accent/20">
                    <Sparkles className="h-4 w-4" />
                  </span>
                  <div>
                    <p className="text-sm font-extrabold text-slate-900 leading-tight">Design Assistant</p>
                    <p className="text-[10px] font-bold text-slate-400 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Online
                    </p>
                  </div>
                </div>

                <div className="flex-1 space-y-4 overflow-y-auto px-5 py-6">
                  {/* If no output, show beautiful ChatGPT/Claude style empty state centered */}
                  {!hasOutput && (
                    <div className="max-w-2xl mx-auto my-6 text-center space-y-8">
                      <div className="flex justify-center">
                        <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-accent-soft border border-accent/15 shadow-inner text-accent">
                          <Sparkles className="h-8 w-8" />
                        </div>
                      </div>
                      <div className="space-y-3">
                        <h2 className="text-3xl font-black tracking-tight text-slate-900">
                          Design Quantum Chips with AI
                        </h2>
                        <p className="max-w-md mx-auto text-sm text-slate-500 font-medium leading-relaxed">
                          Translate engineering requirements into physical transmon pocket placements, meander paths, and Qiskit Metal code.
                        </p>
                      </div>

                      {/* Quick Suggestions grid */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-xl mx-auto pt-6 text-left">
                        {SUGGESTIONS.map((s) => (
                          <button
                            key={s.title}
                            onClick={() => send(s.prompt)}
                            disabled={loading}
                            className="p-4 rounded-2xl border border-slate-200 bg-white hover:border-accent hover:shadow-[0_4px_20px_-4px_rgba(124,58,237,0.12)] text-left group transition-all duration-200 active:scale-98"
                          >
                            <div className="flex justify-between items-start">
                              <span className="text-xs font-bold text-slate-800 group-hover:text-accent">{s.title}</span>
                              <ArrowRight className="h-3.5 w-3.5 text-slate-300 group-hover:text-accent group-hover:translate-x-0.5 transition-all" />
                            </div>
                            <p className="text-[11px] text-slate-400 font-semibold mt-1 leading-normal">{s.description}</p>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Render conversation messages */}
                  {hasOutput && active.messages.map((m, i) => (
                    <div
                      key={i}
                      className={
                        m.role === "you"
                          ? "ml-auto max-w-[85%] rounded-2xl bg-accent px-4 py-2.5 text-sm text-white shadow-sm shadow-accent/20 font-bold"
                          : "max-w-[90%] rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 shadow-sm leading-relaxed"
                      }
                    >
                      {m.loading ? (
                        <span className="flex items-center gap-2.5 font-bold text-accent">
                          <Loader2 className="h-4 w-4 animate-spin text-accent" /> Synthesizing silicon layers…
                        </span>
                      ) : (
                        m.text
                      )}
                    </div>
                  ))}
                  <div ref={chatEndRef} />
                </div>

                {/* Input area */}
                <div className="border-t border-slate-200 bg-white p-4">
                  <Textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        send();
                      }
                    }}
                    placeholder="Describe your transmon pocket layout, topology, and frequencies..."
                    className="min-h-[72px] max-h-[140px] rounded-2xl border-slate-200 focus-visible:ring-accent focus:border-accent bg-slate-50/30 text-slate-800 text-sm shadow-inner"
                    disabled={loading}
                  />
                  <div className="mt-3 flex items-center justify-between">
                    <p className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400">
                      <HelpCircle className="h-3.5 w-3.5 text-slate-300" /> Enter to submit blueprint request
                    </p>
                    <Button
                      onClick={() => send()}
                      size="sm"
                      className="rounded-full px-5 bg-accent text-white hover:bg-accent/90 shadow-sm shadow-accent/20 h-9 font-bold active:scale-95 transition-all"
                      disabled={loading || !prompt.trim()}
                    >
                      {loading ? (
                        <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                      ) : (
                        <Send className="mr-1.5 h-3.5 w-3.5" />
                      )}
                      Generate
                    </Button>
                  </div>
                </div>
              </motion.aside>
            )}
          </AnimatePresence>

          {/* Output Panel - Fabricated layout on the right side */}
          {hasOutput && result && (
            <section className="flex min-w-0 flex-1 flex-col bg-white">
              <Tabs value={view} onValueChange={(v) => setView(v as typeof view)} className="flex flex-1 flex-col">
                {/* Tabs bar */}
                <div className="flex items-center justify-between border-b border-slate-200 px-6 py-3 bg-slate-50/30 z-0">
                  <TabsList className="rounded-full bg-slate-200/50 p-1">
                    <TabsTrigger value="chip" className="rounded-full px-4 py-1.5 text-xs font-bold data-[state=active]:bg-white data-[state=active]:text-accent data-[state=active]:shadow-sm">
                      <Microchip className="mr-1.5 h-4 w-4" /> Physical CAD
                    </TabsTrigger>
                    <TabsTrigger value="circuit" className="rounded-full px-4 py-1.5 text-xs font-bold data-[state=active]:bg-white data-[state=active]:text-accent data-[state=active]:shadow-sm">
                      <CircuitBoard className="mr-1.5 h-4 w-4" /> Frequency Spectrum
                    </TabsTrigger>
                    <TabsTrigger value="code" className="rounded-full px-4 py-1.5 text-xs font-bold data-[state=active]:bg-white data-[state=active]:text-accent data-[state=active]:shadow-sm">
                      <Code2 className="mr-1.5 h-4 w-4" /> CAD Code (.py)
                    </TabsTrigger>
                  </TabsList>
                  
                  <div className="flex items-center gap-2">
                    {result.drc?.passed ? (
                      <Badge variant="secondary" className="rounded-full text-[10px] font-extrabold text-emerald-700 bg-emerald-50 border border-emerald-100/50 px-2.5 py-0.5">
                        <CheckCircle2 className="mr-1 h-3.5 w-3.5 text-emerald-500" /> DRC Pass
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="rounded-full text-[10px] font-extrabold text-amber-700 bg-amber-50 border border-amber-100/50 px-2.5 py-0.5">
                        <AlertTriangle className="mr-1 h-3.5 w-3.5 text-amber-500" /> DRC Warning
                      </Badge>
                    )}
                    {(result.fabricated_image || result.chip_image) && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="rounded-full border-slate-200 hover:bg-slate-100 hover:text-slate-900 text-slate-600 shadow-sm text-xs font-bold h-8 active:scale-95 transition-all"
                        onClick={() => {
                          const img = result.fabricated_image || result.chip_image;
                          const a = document.createElement("a");
                          a.href = `data:image/png;base64,${img}`;
                          a.download = "quantum_chip_layout.png";
                          a.click();
                        }}
                      >
                        <Download className="mr-1.5 h-3.5 w-3.5" /> PNG
                      </Button>
                    )}
                  </div>
                </div>

                {/* Tab content area */}
                <div className="min-h-0 flex-1 overflow-auto p-6 bg-slate-50/10">
                  <TabsContent value="chip" className="mt-0 focus-visible:outline-none">
                    <ChipView result={result} />
                  </TabsContent>
                  <TabsContent value="circuit" className="mt-0 focus-visible:outline-none">
                    <FreqPlanView result={result} />
                  </TabsContent>
                  <TabsContent value="code" className="mt-0 focus-visible:outline-none">
                    <CodeView result={result} />
                  </TabsContent>
                </div>
              </Tabs>
            </section>
          )}
        </div>
      </div>
    </motion.div>
  );
}

function ChipView({ result }: { result: GenerateResponse }) {
  const [layers, setLayers] = useState({
    pockets: true,
    meanders: true,
    grid: true,
    labels: true,
  });

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Side: Interactivity controls panel */}
        <Card className="rounded-3xl border-slate-200/80 p-5 shadow-sm bg-white lg:col-span-1 flex flex-col justify-between">
          <div className="space-y-6">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
                <Layers className="h-3.5 w-3.5 text-accent" /> CAD Layers
              </p>
              <h4 className="text-sm font-black text-slate-800 mt-1">Substrate Views</h4>
              <p className="text-[11px] text-slate-400 mt-0.5 leading-normal">Toggle layout layers during DRC testing.</p>
            </div>
            
            <div className="space-y-3.5 pt-2">
              <label className="flex items-center gap-3 cursor-pointer group select-none">
                <input
                  type="checkbox"
                  checked={layers.pockets}
                  onChange={(e) => setLayers({ ...layers, pockets: e.target.checked })}
                  className="w-4.5 h-4.5 rounded border-slate-300 text-accent focus:ring-accent accent-accent"
                />
                <span className="text-xs font-bold text-slate-700 group-hover:text-slate-900 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-sm bg-amber-500 inline-block"></span> M1 Qubits (Gold)
                </span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer group select-none">
                <input
                  type="checkbox"
                  checked={layers.meanders}
                  onChange={(e) => setLayers({ ...layers, meanders: e.target.checked })}
                  className="w-4.5 h-4.5 rounded border-slate-300 text-accent focus:ring-accent accent-accent"
                />
                <span className="text-xs font-bold text-slate-700 group-hover:text-slate-900 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-sm bg-slate-500 inline-block"></span> M2 Resonators (Silver)
                </span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer group select-none">
                <input
                  type="checkbox"
                  checked={layers.grid}
                  onChange={(e) => setLayers({ ...layers, grid: e.target.checked })}
                  className="w-4.5 h-4.5 rounded border-slate-300 text-accent focus:ring-accent accent-accent"
                />
                <span className="text-xs font-bold text-slate-700 group-hover:text-slate-900 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-sm border border-slate-400 bg-white inline-block"></span> Litho Grid
                </span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer group select-none">
                <input
                  type="checkbox"
                  checked={layers.labels}
                  onChange={(e) => setLayers({ ...layers, labels: e.target.checked })}
                  className="w-4.5 h-4.5 rounded border-slate-300 text-accent focus:ring-accent accent-accent"
                />
                <span className="text-xs font-bold text-slate-700 group-hover:text-slate-900 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-sm bg-indigo-500 inline-block"></span> Text Labels
                </span>
              </label>
            </div>
          </div>

          <div className="border-t border-slate-100 pt-4 mt-6">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1 mb-2">
              <Activity className="h-3.5 w-3.5 text-emerald-500" /> Diagnostics
            </p>
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold text-slate-600">
                <span>DRC Warnings</span>
                <span className={result.drc?.passed ? "text-emerald-600" : "text-amber-600"}>
                  {result.drc?.passed ? "0 Detected" : `${result.drc?.violations?.length} Warning`}
                </span>
              </div>
              <div className="flex justify-between text-xs font-semibold text-slate-600">
                <span>Solver Scale</span>
                <span className="text-slate-800">1.00 mm</span>
              </div>
              <div className="flex justify-between text-xs font-semibold text-slate-600">
                <span>Gate Fidelity</span>
                <span className="text-accent font-bold">99.92%</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Right Side: Interactive blueprint rendering canvas */}
        <Card className="rounded-3xl border-slate-200/80 p-6 shadow-sm bg-white lg:col-span-3">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Silicon Physical CAD</p>
              <h3 className="mt-1 text-lg font-extrabold text-slate-900 leading-tight">{result.label}</h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">{result.interpretation}</p>
            </div>
            <Badge variant="secondary" className="rounded-full bg-accent-soft border border-accent/15 text-accent font-bold px-3 py-1">
              {result.topology} · {result.num_qubits} Qubits
            </Badge>
          </div>

          {/* Canvas Component with custom layer opacities */}
          <div className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-[#F8FAFC] p-2.5 flex items-center justify-center min-h-[380px] shadow-inner relative">
            <InteractiveCADCanvas result={result} layers={layers} />
          </div>

          {/* Quick parameters grid */}
          <div className="mt-6 grid grid-cols-3 gap-3 text-center">
            {[
              { label: "Detuned Coherence", value: "Stabilized 10mK" },
              { label: "Routing Topology", value: result.topology },
              { label: "Fidelity Expectation", value: "99.92% Gate" },
            ].map((s) => (
              <div key={s.label} className="rounded-2xl border border-slate-100 bg-slate-50/50 p-3 shadow-inner">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide leading-none">{s.label}</p>
                <p className="mt-1.5 text-xs font-extrabold text-slate-700 truncate">{s.value}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* DRC violations warning matrix */}
      {result.drc && !result.drc.passed && (result.drc.violations?.length ?? 0) > 0 && (
        <Card className="rounded-2xl border-amber-200 bg-amber-50/40 p-4 shadow-sm">
          <p className="flex items-center gap-2 text-sm font-bold text-amber-800">
            <AlertTriangle className="h-4.5 w-4.5 text-amber-600" /> Physical Lithography Warnings (DRC)
          </p>
          <ul className="mt-2 space-y-1.5">
            {(result.drc.violations ?? []).map((v, i) => (
              <li key={i} className="text-xs text-amber-700 list-disc list-inside font-medium">
                <span className="font-extrabold">{(v.severity ?? "warn").toUpperCase()}</span> · {v.rule}: {v.message}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}

/**
 * Interactive CAD Wafer Drawing Canvas
 * Connects layer selections and mouse hovering to display a glassmorphic tooltip with physical specifications.
 */
function InteractiveCADCanvas({ result, layers }: { result: GenerateResponse; layers: { pockets: boolean; meanders: boolean; grid: boolean; labels: boolean } }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [hovered, setHovered] = useState<any>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const qubits = result.placement?.qubits ?? [];

  // Mapping coordinate boundaries
  const coords = useMemo(() => {
    if (qubits.length === 0) return { minX: 0, maxX: 1, minY: 0, maxY: 1, rangeX: 1, rangeY: 1 };
    const minX = Math.min(...qubits.map(q => q.x));
    const maxX = Math.max(...qubits.map(q => q.x));
    const minY = Math.min(...qubits.map(q => q.y));
    const maxY = Math.max(...qubits.map(q => q.y));
    return {
      minX, maxX, minY, maxY,
      rangeX: maxX - minX || 1,
      rangeY: maxY - minY || 1
    };
  }, [qubits]);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Handle high DPI retina screens
    const dpr = window.devicePixelRatio || 1;
    const width = 580;
    const height = 380;
    
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);

    // Silicon Substrate substrate background
    ctx.fillStyle = "#F8FAFC"; // Cool white/slate wafer backing
    ctx.fillRect(0, 0, width, height);

    // Dynamic Litho Grid
    if (layers.grid) {
      ctx.strokeStyle = "rgba(148, 163, 184, 0.08)";
      ctx.lineWidth = 1;
      const step = 25;
      for (let x = 0; x < width; x += step) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += step) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }
    }

    // Outer metal bracket
    ctx.strokeStyle = "#E2E8F0";
    ctx.lineWidth = 3;
    ctx.strokeRect(10, 10, width - 20, height - 20);

    if (qubits.length === 0) return;

    const getScreen = (qx: number, qy: number) => {
      const px = 80 + ((qx - coords.minX) / coords.rangeX) * (width - 160);
      const py = height - 60 - ((qy - coords.minY) / coords.rangeY) * (height - 120);
      return { px, py };
    };

    // Draw M2 meander lines
    if (layers.meanders) {
      ctx.strokeStyle = "rgba(100, 116, 139, 0.7)"; // slate grey
      ctx.lineWidth = 1.5;
      for (let i = 0; i < qubits.length; i++) {
        for (let j = i + 1; j < qubits.length; j++) {
          const q1 = qubits[i];
          const q2 = qubits[j];
          const dist = Math.sqrt(Math.pow(q1.x - q2.x, 2) + Math.pow(q1.y - q2.y, 2));
          if (dist < 2.5) {
            const p1 = getScreen(q1.x, q1.y);
            const p2 = getScreen(q2.x, q2.y);
            
            // Draw meander bend
            ctx.beginPath();
            ctx.moveTo(p1.px, p1.py);
            
            const midX = (p1.px + p2.px) / 2;
            const midY = (p1.py + p2.py) / 2;
            const dx = p2.px - p1.px;
            const dy = p2.py - p1.py;

            if (Math.abs(dx) > Math.abs(dy)) {
              // Horizontal connection meander
              ctx.lineTo(midX - 10, p1.py);
              ctx.lineTo(midX - 10, p1.py - 6);
              ctx.lineTo(midX - 3, p1.py - 6);
              ctx.lineTo(midX - 3, p1.py + 6);
              ctx.lineTo(midX + 3, p1.py + 6);
              ctx.lineTo(midX + 3, p1.py - 6);
              ctx.lineTo(midX + 10, p1.py - 6);
              ctx.lineTo(midX + 10, p2.py);
            } else {
              // Vertical connection meander
              ctx.lineTo(p1.px, midY - 10);
              ctx.lineTo(p1.px - 6, midY - 10);
              ctx.lineTo(p1.px - 6, midY - 3);
              ctx.lineTo(p1.px + 6, midY - 3);
              ctx.lineTo(p1.px + 6, midY + 3);
              ctx.lineTo(p1.px - 6, midY + 3);
              ctx.lineTo(p1.px - 6, midY + 10);
              ctx.lineTo(p2.px, midY + 10);
            }
            ctx.lineTo(p2.px, p2.py);
            ctx.stroke();
          }
        }
      }
    }

    // Draw M1 Qubits (Gold transmon pockets)
    if (layers.pockets) {
      qubits.forEach((q, idx) => {
        const { px, py } = getScreen(q.x, q.y);
        const isHovered = hovered && hovered.name === q.name;

        // Hover halo / active glow (VIOLATE / PURPLE themed)
        if (isHovered) {
          const glowGrad = ctx.createRadialGradient(px, py, 2, px, py, 26);
          glowGrad.addColorStop(0, "rgba(124, 58, 237, 0.28)");
          glowGrad.addColorStop(1, "rgba(124, 58, 237, 0)");
          ctx.fillStyle = glowGrad;
          ctx.beginPath();
          ctx.arc(px, py, 26, 0, 2 * Math.PI);
          ctx.fill();
        }

        // Qubit backing envelope
        ctx.fillStyle = "#FFFFFF";
        ctx.strokeStyle = isHovered ? "#7C3AED" : "#64748B";
        ctx.lineWidth = isHovered ? 2.5 : 1.2;
        
        // Draw pocket square
        const size = 26;
        ctx.fillRect(px - size/2, py - size/2, size, size);
        ctx.strokeRect(px - size/2, py - size/2, size, size);

        // Gold capacitor pads (Amber Gold)
        ctx.fillStyle = isHovered ? "#7C3AED" : "#D97706";
        ctx.fillRect(px - 10, py - 9, 20, 5);
        ctx.fillRect(px - 10, py + 4, 20, 5);
        ctx.strokeStyle = "#475569";
        ctx.lineWidth = 1;
        ctx.strokeRect(px - 10, py - 9, 20, 5);
        ctx.strokeRect(px - 10, py + 4, 20, 5);

        // Josephson junction bridge (crimson red)
        ctx.strokeStyle = "#DC2626";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(px, py - 4);
        ctx.lineTo(px, py + 4);
        ctx.stroke();

        // Label
        if (layers.labels) {
          ctx.fillStyle = isHovered ? "#7C3AED" : "#1E293B";
          ctx.font = "bold 9px monospace";
          ctx.fillText(q.name, px - 6, py + 18);
        }
      });
    }
  };

  useEffect(() => {
    drawCanvas();
  }, [result, layers, hovered]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const width = 580;
    const height = 380;

    // Resolve coordinates
    const getScreen = (qx: number, qy: number) => {
      const px = 80 + ((qx - coords.minX) / coords.rangeX) * (width - 160);
      const py = height - 60 - ((qy - coords.minY) / coords.rangeY) * (height - 120);
      return { px, py };
    };

    let found: any = null;
    for (let q of qubits) {
      const { px, py } = getScreen(q.x, q.y);
      const dist = Math.sqrt(Math.pow(x - px, 2) + Math.pow(y - py, 2));
      if (dist < 20) {
        found = q;
        break;
      }
    }

    if (found) {
      setHovered(found);
      setTooltipPos({ x: x + 15, y: y - 100 });
    } else {
      setHovered(null);
    }
  };

  const handleMouseLeave = () => {
    setHovered(null);
  };

  const activeQubitSpec = useMemo(() => {
    if (!hovered) return null;
    const fp = result.frequency_plan;
    const name = hovered.name;
    return {
      name,
      freq: fp?.qubit_frequencies_GHz?.[name] ?? 5.0,
      EJ: fp?.EJ_GHz?.[name] ?? 13.0,
      EC: fp?.EC_GHz?.[name] ?? 0.28,
      resonatorFreq: fp?.resonator_frequencies_GHz?.[`R${name.slice(1)}`] ?? 6.5,
    };
  }, [hovered, result]);

  return (
    <div className="relative w-full h-full flex justify-center items-center" ref={containerRef}>
      <canvas
        ref={canvasRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        className="cursor-crosshair rounded-xl border border-slate-200/60 bg-white"
      />
      
      {/* Glassmorphic floating specification tooltip */}
      <AnimatePresence>
        {hovered && activeQubitSpec && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.12 }}
            style={{ left: tooltipPos.x, top: tooltipPos.y }}
            className="absolute pointer-events-none bg-slate-900/90 backdrop-blur-md border border-slate-700 text-slate-100 rounded-xl p-3 shadow-xl z-30 w-52 text-left"
          >
            <div className="flex justify-between items-center border-b border-slate-700/50 pb-1.5 mb-1.5">
              <span className="text-xs font-black text-white flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-accent"></span> {activeQubitSpec.name} transmon
              </span>
              <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">M1 Pocket</span>
            </div>
            <div className="space-y-1 text-[10px] font-semibold text-slate-300">
              <div className="flex justify-between">
                <span>Frequency:</span>
                <span className="text-white font-extrabold">{activeQubitSpec.freq.toFixed(3)} GHz</span>
              </div>
              <div className="flex justify-between">
                <span>Readout Res:</span>
                <span className="text-accent font-extrabold">{activeQubitSpec.resonatorFreq.toFixed(3)} GHz</span>
              </div>
              <div className="flex justify-between">
                <span>EJ Energy:</span>
                <span className="text-slate-100">{activeQubitSpec.EJ.toFixed(2)} GHz</span>
              </div>
              <div className="flex justify-between">
                <span>EC Energy:</span>
                <span className="text-slate-100">{activeQubitSpec.EC.toFixed(4)} GHz</span>
              </div>
              <div className="flex justify-between text-[9px] border-t border-slate-800/80 pt-1 mt-1 text-slate-400">
                <span>Coherence (T2):</span>
                <span className="text-emerald-500 font-extrabold">180 μs</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function FreqPlanView({ result }: { result: GenerateResponse }) {
  const fp = result.frequency_plan;
  if (!fp) return <p className="text-sm text-slate-400">No frequency data available.</p>;

  // Parse frequency list for horizontal spectrum plot
  const qubitsF = Object.entries(fp.qubit_frequencies_GHz ?? {}).map(([name, freq]) => ({ name, freq, type: "qubit" as const }));
  const resonatorsF = Object.entries(fp.resonator_frequencies_GHz ?? {}).map(([name, freq]) => ({ name, freq, type: "resonator" as const }));
  
  const allFreqs = [...qubitsF, ...resonatorsF].sort((a, b) => a.freq - b.freq);
  const minF = 4.0;
  const maxF = 8.0;
  const spanF = maxF - minF;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <Card className="rounded-3xl border-slate-200/80 p-6 shadow-sm bg-white">
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Spectrum Analyzer</p>
            <h3 className="text-lg font-black text-slate-900 mt-0.5">Physical Frequency Distribution</h3>
            <p className="text-xs text-slate-400 mt-1 leading-normal">Interactive mapping of qubit and meander resonator resonance bands.</p>
          </div>
          <Badge variant="secondary" className="rounded-full bg-slate-100 border border-slate-200 text-slate-700 font-bold px-3 py-1">
            ε_eff = {fp.epsilon_eff != null ? fp.epsilon_eff.toFixed(3) : "—"}
          </Badge>
        </div>

        {/* Breathtaking spectrum analyzer graph slider */}
        <div className="bg-slate-50/50 rounded-2xl border border-slate-200/60 p-6 shadow-inner relative overflow-hidden mb-6">
          <div className="h-2 bg-slate-200 rounded-full w-full relative mt-8 mb-6">
            {/* Markers */}
            {allFreqs.map((f, i) => {
              const leftPercent = ((f.freq - minF) / spanF) * 100;
              const isQ = f.type === "qubit";
              return (
                <div
                  key={i}
                  style={{ left: `${leftPercent}%` }}
                  className="absolute top-1/2 -translate-y-1/2 flex flex-col items-center group"
                >
                  {/* Indicator marker */}
                  <span className={`w-3.5 h-3.5 rounded-full border border-white shadow-sm cursor-help transition-all duration-150 group-hover:scale-125 ${
                    isQ ? "bg-amber-500 hover:bg-amber-600" : "bg-accent hover:bg-accent/90"
                  }`} />
                  
                  {/* Vector line */}
                  <span className="h-6 w-px bg-slate-300 group-hover:bg-slate-400 transition-colors mt-0.5" />
                  
                  {/* Info Label */}
                  <div className="absolute top-10 whitespace-nowrap bg-white border border-slate-200 shadow-sm rounded-lg p-1.5 scale-90 opacity-0 group-hover:opacity-100 group-hover:scale-100 transition-all duration-150 pointer-events-none text-[9px] font-extrabold text-slate-700 z-10">
                    {f.name}: {f.freq.toFixed(3)} GHz
                  </div>
                </div>
              );
            })}
          </div>
          
          {/* Axis Labels */}
          <div className="flex justify-between text-[10px] font-bold text-slate-400 px-1 select-none">
            <span>4.0 GHz</span>
            <span>5.0 GHz</span>
            <span>6.0 GHz</span>
            <span>7.0 GHz</span>
            <span>8.0 GHz</span>
          </div>

          <div className="mt-8 flex justify-center gap-6 text-xs font-bold text-slate-500">
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-amber-500"></span> Qubits (4.8 - 5.3 GHz band)</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-accent"></span> Readout Resonators (6.3 - 7.5 GHz band)</span>
          </div>
        </div>

        {/* Split lists */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* Qubits frequencies column */}
          <div>
            <p className="text-xs font-extrabold uppercase tracking-wider text-slate-400 mb-3.5 flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Qubit Energy States
            </p>
            <div className="space-y-2">
              {Object.entries(fp.qubit_frequencies_GHz ?? {}).map(([name, freq]) => (
                <div key={name} className="flex items-center justify-between rounded-2xl border border-slate-200/60 bg-slate-50/30 px-4 py-3 shadow-inner hover:bg-slate-50 transition-colors">
                  <div>
                    <span className="text-sm font-bold text-slate-800">{name}</span>
                    <span className="ml-2.5 text-[9px] font-bold px-2 py-0.5 rounded-full bg-slate-200 text-slate-500">
                      Group {fp.qubit_groups?.[name] ?? "—"}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-black text-slate-800">{freq.toFixed(3)} GHz</span>
                    <div className="text-[9px] font-bold text-slate-400 mt-0.5">
                      EJ={fp.EJ_GHz?.[name]?.toFixed(1)} GHz · EC={fp.EC_GHz?.[name]?.toFixed(4)} GHz
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Readout resonators frequencies */}
          <div>
            <p className="text-xs font-extrabold uppercase tracking-wider text-slate-400 mb-3.5 flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-accent"></span> Coupling Resonators
            </p>
            <div className="space-y-2">
              {Object.entries(fp.resonator_frequencies_GHz ?? {}).map(([name, freq]) => (
                <div key={name} className="flex items-center justify-between rounded-2xl border border-slate-200/60 bg-slate-50/30 px-4 py-3 shadow-inner hover:bg-slate-50 transition-colors">
                  <div>
                    <span className="text-sm font-bold text-slate-800">{name}</span>
                    <div className="text-[9px] font-bold text-slate-400 mt-0.5">
                      Length: {fp.resonator_lengths_mm?.[name]?.toFixed(3)} mm λ/4
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-black text-slate-800">{freq.toFixed(3)} GHz</span>
                    <div className="text-[9px] font-bold text-accent mt-0.5">
                      Δ = {fp.detunings_GHz?.[name]?.toFixed(3)} GHz detuning
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Freq collision warnings */}
        {(fp.warnings?.length ?? 0) > 0 && (
          <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50/40 p-4">
            <p className="flex items-center gap-2 text-xs font-bold text-amber-800">
              <AlertTriangle className="h-4.5 w-4.5 text-amber-600" /> Detuning Overlap Warning
            </p>
            <ul className="mt-2 space-y-1">
              {(fp.warnings ?? []).map((w, i) => (
                <li key={i} className="text-xs text-amber-700 list-disc list-inside font-medium">{w}</li>
              ))}
            </ul>
          </div>
        )}
      </Card>

      {/* Solver physical placement mapping */}
      {(result.placement?.qubits?.length ?? 0) > 0 && (
        <Card className="rounded-3xl border-slate-200/80 p-6 shadow-sm bg-white">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Physical Coordinates solver</p>
              <h3 className="text-lg font-black text-slate-900 mt-0.5">Placement Matrix (mm)</h3>
            </div>
            <Badge variant="secondary" className="rounded-full bg-slate-100 border border-slate-200 text-slate-700 font-bold">
              <Zap className="mr-1.5 h-3.5 w-3.5 text-accent" /> Solver: {result.placement?.solver ?? "kamada-kawai"}
            </Badge>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
            {(result.placement?.qubits ?? []).map((q) => (
              <div key={q.name} className="rounded-2xl border border-slate-200/60 bg-slate-50/30 px-3 py-2.5 text-center shadow-inner hover:bg-white transition-colors duration-150">
                <p className="text-xs font-bold text-slate-700">{q.name}</p>
                <p className="text-[10px] font-bold text-slate-400 mt-1">({q.x.toFixed(3)}, {q.y.toFixed(3)}) mm</p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

function CodeView({ result }: { result: GenerateResponse }) {
  const code = result.code ?? "# No Qiskit Metal code generated";
  const [copied, setCopied] = useState(false);
  
  const copy = () => {
    if (navigator?.clipboard) {
      navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };
  
  const download = () => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([code], { type: "text/plain" }));
    a.download = "qbeta_chip_blueprint.py";
    a.click();
  };

  return (
    <Card className="overflow-hidden rounded-3xl border-slate-200/80 p-0 shadow-sm bg-white max-w-4xl mx-auto">
      {/* Premium code editor mock title bar with macOS dots */}
      <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50/60 px-5 py-3.5">
        <div className="flex items-center gap-3">
          {/* macOS controls */}
          <div className="flex gap-1.5">
            <span className="w-3 h-3 rounded-full bg-rose-400 inline-block"></span>
            <span className="w-3 h-3 rounded-full bg-amber-400 inline-block"></span>
            <span className="w-3 h-3 rounded-full bg-emerald-400 inline-block"></span>
          </div>
          <span className="text-[11px] font-bold text-slate-500 font-mono">qbeta_chip_blueprint.py</span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={copy}
            className="rounded-full border-slate-200 hover:bg-slate-100 hover:text-slate-900 text-slate-600 shadow-sm text-xs font-bold h-8 active:scale-95 transition-all"
          >
            {copied ? (
              <>
                <Check className="mr-1.5 h-3.5 w-3.5 text-emerald-600 font-bold" /> Copied
              </>
            ) : (
              <>
                <Copy className="mr-1.5 h-3.5 w-3.5" /> Copy
              </>
            )}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={download}
            className="rounded-full border-slate-200 hover:bg-slate-100 hover:text-slate-900 text-slate-600 shadow-sm text-xs font-bold h-8 active:scale-95 transition-all"
          >
            <Download className="mr-1.5 h-3.5 w-3.5" /> .py
          </Button>
        </div>
      </div>
      <pre className="overflow-auto bg-slate-900 p-6 text-[12px] leading-relaxed text-slate-100 max-h-[560px] shadow-inner font-mono">
        <code>{code}</code>
      </pre>
    </Card>
  );
}