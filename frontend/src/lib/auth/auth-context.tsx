import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type Role = "admin" | "org_manager" | "engineer";

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: Role;
  organization: string;
  initials: string;
}

interface DemoAccount extends AuthUser {
  password: string;
}

export const DEMO_ACCOUNTS: DemoAccount[] = [
  {
    id: "u_admin",
    email: "admin@silicofeller.com",
    password: "admin123",
    name: "Sasha Park",
    role: "admin",
    organization: "Silicofeller",
    initials: "SP",
  },
  {
    id: "u_manager",
    email: "manager@quantumlabs.com",
    password: "manager123",
    name: "Mira Chen",
    role: "org_manager",
    organization: "Quantum Labs",
    initials: "MC",
  },
  {
    id: "u_engineer",
    email: "engineer@quantumlabs.com",
    password: "eng123",
    name: "Eli Novak",
    role: "engineer",
    organization: "Quantum Labs",
    initials: "EN",
  },
];

export const ROLE_LABEL: Record<Role, string> = {
  admin: "Admin",
  org_manager: "Organization Manager",
  engineer: "Engineer",
};

interface AuthContextValue {
  user: AuthUser | null;
  signIn: (email: string, password: string) => { ok: true } | { ok: false; error: string };
  signInAs: (role: Role) => void;
  signUp: (input: { name: string; email: string; organization: string }) => void;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const STORAGE_KEY = "silicofeller.auth.user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    try {
      const raw =
        typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : null;
      if (raw) setUser(JSON.parse(raw) as AuthUser);
    } catch {
      // ignore
    }
  }, []);

  const persist = useCallback((next: AuthUser | null) => {
    setUser(next);
    if (typeof window === "undefined") return;
    if (next) window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    else window.localStorage.removeItem(STORAGE_KEY);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      signIn: (email, password) => {
        const match = DEMO_ACCOUNTS.find(
          (a) => a.email.toLowerCase() === email.toLowerCase() && a.password === password,
        );
        if (!match) return { ok: false, error: "Invalid email or password" };
        const { password: _pw, ...safe } = match;
        persist(safe);
        return { ok: true };
      },
      signInAs: (role) => {
        const match = DEMO_ACCOUNTS.find((a) => a.role === role);
        if (!match) return;
        const { password: _pw, ...safe } = match;
        persist(safe);
      },
      signUp: ({ name, email, organization }) => {
        // First user from a new company becomes Organization Manager.
        const initials = name
          .split(/\s+/)
          .map((p) => p[0])
          .join("")
          .slice(0, 2)
          .toUpperCase();
        persist({
          id: `u_${Date.now()}`,
          email,
          name,
          role: "org_manager",
          organization,
          initials: initials || "ME",
        });
      },
      signOut: () => persist(null),
    }),
    [user, persist],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function canAccess(role: Role | undefined, page: "billing" | "team" | "admin" | "designer" | "about") {
  if (!role) return false;
  switch (page) {
    case "designer":
    case "about":
      return true;
    case "billing":
      return role === "admin" || role === "org_manager";
    case "team":
      return role === "admin" || role === "org_manager";
    case "admin":
      return role === "admin";
  }
}