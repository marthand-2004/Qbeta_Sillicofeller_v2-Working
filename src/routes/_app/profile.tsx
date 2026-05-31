import { createFileRoute } from "@tanstack/react-router";
import { motion } from "motion/react";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/profile")({
  head: () => ({ meta: [{ title: "Profile — Silicofeller" }] }),
  component: ProfilePage,
});

function ProfilePage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="mx-auto w-full max-w-4xl px-6 py-10"
    >
      <h1 className="text-3xl font-semibold tracking-tight text-foreground">Profile</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Manage your personal information and preferences.
      </p>
      <Card className="mt-8 rounded-2xl border-border p-6 shadow-none">
        <div className="flex items-center gap-4">
          <Avatar className="h-16 w-16">
            <AvatarFallback className="bg-foreground text-base font-semibold text-background">
              AC
            </AvatarFallback>
          </Avatar>
          <div>
            <div className="text-base font-semibold text-foreground">Alex Chen</div>
            <div className="text-sm text-muted-foreground">Quantum Architect</div>
          </div>
          <Button variant="outline" className="ml-auto h-9 rounded-full">
            Change avatar
          </Button>
        </div>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="full-name">Full name</Label>
            <Input id="full-name" defaultValue="Alex Chen" className="mt-1.5 h-10" />
          </div>
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              defaultValue="alex@silicofeller.ai"
              className="mt-1.5 h-10"
            />
          </div>
          <div>
            <Label htmlFor="role">Role</Label>
            <Input id="role" defaultValue="Quantum Architect" className="mt-1.5 h-10" />
          </div>
          <div>
            <Label htmlFor="org">Organization</Label>
            <Input id="org" defaultValue="Silicofeller Lab" className="mt-1.5 h-10" />
          </div>
        </div>
        <Button className="mt-6 h-10 rounded-full px-5">Save profile</Button>
      </Card>
    </motion.div>
  );
}