import { Link, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard,
  Sparkles,
  Users,
  CreditCard,
  Settings,
  User,
  ShieldCheck,
  Info,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { SilicofellerLogo, LogoMark } from "@/components/silicofeller-logo";
import { useSidebar } from "@/components/ui/sidebar";
import { useAuth, type Role } from "@/lib/auth/auth-context";

type NavItem = {
  title: string;
  url: string;
  icon: typeof LayoutDashboard;
  roles: Role[];
};

const items: NavItem[] = [
  { title: "Dashboard", url: "/dashboard", icon: LayoutDashboard, roles: ["admin", "org_manager", "engineer"] },
  { title: "Designer", url: "/designer", icon: Sparkles, roles: ["admin", "org_manager", "engineer"] },
  { title: "Team Management", url: "/team", icon: Users, roles: ["admin", "org_manager"] },
  { title: "Billing", url: "/billing", icon: CreditCard, roles: ["admin", "org_manager"] },
  { title: "Admin Console", url: "/admin", icon: ShieldCheck, roles: ["admin"] },
  { title: "About", url: "/about", icon: Info, roles: ["admin", "org_manager", "engineer"] },
  { title: "Settings", url: "/settings", icon: Settings, roles: ["admin", "org_manager", "engineer"] },
  { title: "Profile", url: "/profile", icon: User, roles: ["admin", "org_manager", "engineer"] },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const pathname = useRouterState({ select: (r) => r.location.pathname });
  const { user } = useAuth();
  const visible = items.filter((i) => (user ? i.roles.includes(user.role) : false));

  return (
    <Sidebar collapsible="icon" className="border-r border-border">
      <SidebarHeader className="border-b border-border px-3 py-3">
        {collapsed ? (
          <LogoMark className="mx-auto h-7 w-7" />
        ) : (
          <SilicofellerLogo />
        )}
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Workspace</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {visible.map((item) => {
                const isActive = pathname === item.url;
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      isActive={isActive}
                      tooltip={item.title}
                      className={
                        isActive
                          ? "bg-[color:var(--accent-soft)] text-foreground hover:bg-[color:var(--accent-soft)]"
                          : ""
                      }
                    >
                      <Link to={item.url} className="flex items-center gap-2">
                        <item.icon
                          className={
                            isActive
                              ? "h-4 w-4 text-accent"
                              : "h-4 w-4 text-muted-foreground"
                          }
                        />
                        <span>{item.title}</span>
                        {isActive && (
                          <span className="ml-auto h-1.5 w-1.5 rounded-full bg-accent" />
                        )}
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}