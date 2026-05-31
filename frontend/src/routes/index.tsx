import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth/auth-context";

export const Route = createFileRoute("/")({
  component: IndexRedirect,
});

function IndexRedirect() {
  const { user } = useAuth();
  const navigate = useNavigate();
  useEffect(() => {
    navigate({ to: user ? "/dashboard" : "/sign-in", replace: true });
  }, [user, navigate]);
  return null;
}
