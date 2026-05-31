import { createFileRoute } from "@tanstack/react-router";
import { motion } from "motion/react";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/settings")({
  head: () => ({ meta: [{ title: "Settings — Silicofeller" }] }),
  component: SettingsPage,
});

function SettingsPage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="mx-auto w-full max-w-4xl px-6 py-10"
    >
      <h1 className="text-3xl font-semibold tracking-tight text-foreground">Settings</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Workspace, notification, and security preferences.
      </p>
      <Card className="mt-8 rounded-2xl border-border p-6 shadow-none">
        <h2 className="text-base font-semibold text-foreground">Workspace</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="ws-name">Workspace name</Label>
            <Input id="ws-name" defaultValue="Silicofeller Lab" className="mt-1.5 h-10" />
          </div>
          <div>
            <Label htmlFor="ws-slug">Slug</Label>
            <Input id="ws-slug" defaultValue="silicofeller-lab" className="mt-1.5 h-10" />
          </div>
        </div>
        <Button className="mt-5 h-10 rounded-full px-5">Save changes</Button>
      </Card>
      <Card className="mt-6 rounded-2xl border-border p-6 shadow-none">
        <h2 className="text-base font-semibold text-foreground">Notifications</h2>
        <div className="mt-4 space-y-4">
          {[
            ["Product updates", true],
            ["Weekly usage digest", true],
            ["Security alerts", true],
          ].map(([label, on]) => (
            <div key={label as string} className="flex items-center justify-between">
              <span className="text-sm text-foreground">{label as string}</span>
              <Switch defaultChecked={on as boolean} />
            </div>
          ))}
        </div>
      </Card>
    </motion.div>
  );
}