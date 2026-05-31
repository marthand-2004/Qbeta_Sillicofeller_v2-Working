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
import { LogOut, Settings as SettingsIcon, User as UserIcon, CreditCard } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ROLE_LABEL, useAuth } from "@/lib/auth/auth-context";
import { useEffect } from "react";

export const Route = createFileRoute("/_app")({
  component: AppLayout,
});

function AppLayout() {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();

  useEffect(() => {
    if (!user) navigate({ to: "/sign-in", replace: true });
  }, [user, navigate]);

  if (!user) return null;

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-background">
        <AppSidebar />
        <SidebarInset className="flex flex-1 flex-col">
          <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-background/80 px-4 backdrop-blur md:px-6">
            <div className="flex items-center gap-2">
              <SidebarTrigger />
              <span className="hidden text-sm text-muted-foreground md:inline">
                Silicofeller Console
              </span>
              <Badge
                variant="secondary"
                className="ml-2 rounded-full border border-border bg-[color:var(--accent-soft)] px-2.5 py-0.5 text-[11px] font-medium text-foreground"
              >
                {ROLE_LABEL[user.role]}
              </Badge>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger className="flex items-center gap-2 rounded-full border border-border bg-card px-1.5 py-1 pr-3 text-sm transition-colors hover:bg-secondary">
                <Avatar className="h-7 w-7">
                  <AvatarFallback className="bg-foreground text-[11px] font-semibold text-background">
                    {user.initials}
                  </AvatarFallback>
                </Avatar>
                <span className="hidden font-medium text-foreground sm:inline">{user.name}</span>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="flex flex-col">
                    <span className="font-medium text-foreground">{user.name}</span>
                    <span className="text-xs text-muted-foreground">{user.email}</span>
                    <span className="mt-1 text-[11px] text-muted-foreground">
                      {user.organization} · {ROLE_LABEL[user.role]}
                    </span>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link to="/profile" className="cursor-pointer">
                    <UserIcon className="mr-2 h-4 w-4" /> Profile
                  </Link>
                </DropdownMenuItem>
                {(user.role === "admin" || user.role === "org_manager") && (
                  <DropdownMenuItem asChild>
                    <Link to="/billing" className="cursor-pointer">
                      <CreditCard className="mr-2 h-4 w-4" /> Billing
                    </Link>
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem asChild>
                  <Link to="/settings" className="cursor-pointer">
                    <SettingsIcon className="mr-2 h-4 w-4" /> Settings
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="cursor-pointer text-foreground"
                  onClick={() => {
                    signOut();
                    navigate({ to: "/sign-in" });
                  }}
                >
                  <LogOut className="mr-2 h-4 w-4" /> Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </header>
          <main className="flex-1">
            <Outlet />
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}