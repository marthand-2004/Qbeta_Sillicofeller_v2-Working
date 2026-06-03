import { createFileRoute, Outlet, useNavigate, Link } from "@tanstack/react-router";
import { SidebarProvider, SidebarTrigger, SidebarInset } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app/app-sidebar";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LogOut, Settings as SettingsIcon, User as UserIcon, CreditCard, Home, ChevronRight, Activity } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ROLE_LABEL, useAuth } from "@/lib/auth/auth-context";
import { useEffect } from "react";

export const Route = createFileRoute("/_app")({
  component: AppLayout,
});

function AppLayout() {
  const navigate = useNavigate();
  const { user, hydrated, signOut } = useAuth();

  useEffect(() => {
    if (hydrated && !user) navigate({ to: "/sign-in", replace: true });
  }, [hydrated, user, navigate]);

  if (!hydrated || !user) return null;

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-slate-50/20 text-slate-800">
        <AppSidebar />
        <SidebarInset className="flex flex-1 flex-col overflow-hidden">
          {/* Re-styled next-generation header/navbar */}
          <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-slate-200/80 bg-white/80 px-6 backdrop-blur-md shadow-[0_1px_2px_0_rgba(0,0,0,0.015)]">
            <div className="flex items-center gap-3">
              <SidebarTrigger className="h-9 w-9 rounded-xl border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 transition-all cursor-pointer shadow-sm active:scale-95" />
              
              {/* Elegant breadcrumb indicator */}
              <div className="hidden sm:flex items-center gap-1.5 text-xs font-bold text-slate-500">
                <Link to="/dashboard" className="hover:text-slate-800 transition-colors">Workspace</Link>
                <ChevronRight className="h-3.5 w-3.5 text-slate-300" />
                <span className="text-slate-800 font-extrabold">Console</span>
                <ChevronRight className="h-3.5 w-3.5 text-slate-300" />
                <Badge
                  variant="secondary"
                  className="rounded-full bg-accent-soft text-accent border border-accent/10 px-2.5 py-0.5 text-[10px] font-bold"
                >
                  {ROLE_LABEL[user.role]}
                </Badge>
              </div>
            </div>

            {/* Profile Dropdown lockup with clean design */}
            <div className="flex items-center gap-3">
              <DropdownMenu>
                <DropdownMenuTrigger className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white p-1 pr-3 text-xs font-bold text-slate-700 shadow-sm transition-all hover:bg-slate-50/80 hover:border-accent/30 focus:outline-none cursor-pointer">
                  <Avatar className="h-7 w-7 border border-slate-100">
                    <AvatarFallback className="bg-accent text-[10px] font-black text-white shadow-sm shadow-accent/20">
                      {user.initials}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden sm:inline-block truncate max-w-[120px]">{user.name}</span>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56 mt-2 rounded-2xl border-slate-200 shadow-xl p-1 bg-white">
                  <DropdownMenuLabel className="px-3 py-2.5">
                    <div className="flex flex-col">
                      <span className="font-extrabold text-slate-900 leading-tight">{user.name}</span>
                      <span className="text-[10px] text-slate-400 font-semibold mt-0.5">{user.email}</span>
                      <span className="mt-2 text-[10px] font-bold text-accent bg-accent-soft border border-accent/15 px-2 py-0.5 rounded-full w-max">
                        {user.organization}
                      </span>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator className="bg-slate-100" />
                  <DropdownMenuItem asChild className="rounded-xl px-3 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 cursor-pointer focus:bg-slate-50">
                    <Link to="/profile">
                      <UserIcon className="mr-2 h-4 w-4 text-slate-400" /> User Profile
                    </Link>
                  </DropdownMenuItem>
                  {(user.role === "admin" || user.role === "org_manager") && (
                    <DropdownMenuItem asChild className="rounded-xl px-3 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 cursor-pointer focus:bg-slate-50">
                      <Link to="/billing">
                        <CreditCard className="mr-2 h-4 w-4 text-slate-400" /> Billing & Usage
                      </Link>
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem asChild className="rounded-xl px-3 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 cursor-pointer focus:bg-slate-50">
                    <Link to="/settings">
                      <SettingsIcon className="mr-2 h-4 w-4 text-slate-400" /> Console Settings
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator className="bg-slate-100" />
                  <DropdownMenuItem
                    className="rounded-xl px-3 py-2 text-xs font-bold text-rose-600 hover:text-rose-700 cursor-pointer focus:bg-rose-50"
                    onClick={() => {
                      signOut();
                      navigate({ to: "/" });
                    }}
                  >
                    <LogOut className="mr-2 h-4 w-4 text-rose-400" /> Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </header>
          
          <main className="flex-1 overflow-hidden relative">
            <Outlet />
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}