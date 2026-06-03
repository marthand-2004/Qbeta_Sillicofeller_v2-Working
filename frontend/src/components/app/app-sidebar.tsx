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
  Bot,
  ExternalLink,
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
    <Sidebar collapsible="icon" className="border-r border-slate-200 bg-[#FAFBFD]">
      <SidebarHeader className="border-b border-slate-200/80 px-4 py-4 bg-white flex justify-center h-14">
        <Link to="/" aria-label="Back to landing" className="flex items-center">
          {collapsed ? (
            <LogoMark className="mx-auto h-5 w-auto text-slate-800" />
          ) : (
            <SilicofellerLogo />
          )}
        </Link>
      </SidebarHeader>
      <SidebarContent className="py-2">
        <SidebarGroup>
          <SidebarGroupLabel className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400 px-3 mb-2">Workspace</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-1 px-1.5">
              {visible.map((item) => {
                const isActive = pathname === item.url;
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      isActive={isActive}
                      tooltip={item.title}
                      className={`h-9.5 rounded-xl transition-all duration-150 relative ${
                        isActive
                          ? "bg-white border border-slate-200/80 text-slate-900 shadow-[0_2px_8px_-3px_rgba(124,58,237,0.1)] font-bold pl-3"
                          : "text-slate-500 hover:bg-slate-100/60 hover:text-slate-800"
                      }`}
                    >
                      <Link to={item.url} className="flex items-center gap-2.5 w-full">
                        {isActive && (
                          <span className="absolute left-0 top-2 bottom-2 w-1 bg-accent rounded-r" />
                        )}
                        <item.icon
                          className={`h-4.5 w-4.5 transition-colors ${
                            isActive ? "text-accent" : "text-slate-400 group-hover:text-slate-600"
                          }`}
                        />
                        <span className="text-xs leading-none">{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* External Tools group */}
        <SidebarGroup className="mt-2 border-t border-slate-100 pt-3">
          <SidebarGroupLabel className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400 px-3 mb-2">External Engines</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-1 px-1.5">
              <SidebarMenuItem>
                <SidebarMenuButton 
                  asChild 
                  tooltip="QBETA Chatbot"
                  className="h-9.5 rounded-xl text-slate-500 hover:bg-slate-100/60 hover:text-slate-800 pl-3"
                >
                  <a
                    href="http://localhost:5173"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2.5 w-full"
                  >
                    <Bot className="h-4.5 w-4.5 text-accent" />
                    <span className="text-xs leading-none">QBETA Chatbot</span>
                    <ExternalLink className="ml-auto h-3 w-3 text-slate-400 group-hover:text-slate-500" />
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}