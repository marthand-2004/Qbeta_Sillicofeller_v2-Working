import { cn } from "@/lib/utils";

interface LogoProps {
  variant?: "horizontal" | "icon";
  className?: string;
  /** Tailwind size class for the icon mark. Defaults to h-8. */
  iconClassName?: string;
}

/**
 * Silicofeller logo — two-tone badge + divider + NVIDIA lockup.
 * Matches the brand reference: [ SILICO ][ FELLER ] | 🟢 NVIDIA.
 */
export function SilicofellerLogo({
  variant = "horizontal",
  className,
  iconClassName,
}: LogoProps) {
  if (variant === "icon") {
    return <LogoMark className={cn("h-8 w-auto", iconClassName, className)} />;
  }

  return (
    <div className={cn("flex items-center gap-3", className)}>
      {/* ── Two-tone badge ── */}
      <div className="flex items-center gap-0">
        {/* SILICO — outlined box */}
        <span
          className="inline-flex items-center border border-foreground px-[7px] py-[3px] text-[0.7rem] font-bold tracking-[0.12em] text-foreground"
          style={{ fontFamily: "var(--font-display, ui-sans-serif)", lineHeight: 1 }}
        >
          SILICO
        </span>
        {/* FELLER — filled box */}
        <span
          className="inline-flex items-center bg-foreground px-[7px] py-[3px] text-[0.7rem] font-bold tracking-[0.12em] text-background"
          style={{ fontFamily: "var(--font-display, ui-sans-serif)", lineHeight: 1 }}
        >
          FELLER
        </span>
      </div>

      {/* ── Divider ── */}
      <span className="h-5 w-px bg-foreground/30" aria-hidden="true" />

      {/* ── NVIDIA lockup ── */}
      <NvidiaLogo className="h-5 w-auto" />
    </div>
  );
}

/**
 * Compact icon-only mark for collapsed sidebar / favicon contexts.
 * Just the two-tone badge as an SVG — no NVIDIA in collapsed state.
 */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 64 22"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("h-6 w-auto", className)}
      aria-hidden="true"
    >
      {/* Outlined half — SILICO */}
      <rect x="0.5" y="0.5" width="31" height="21" rx="1" stroke="currentColor" strokeWidth="1" fill="none" />
      <text
        x="16"
        y="15"
        textAnchor="middle"
        fontSize="8"
        fontWeight="700"
        letterSpacing="1.2"
        fill="currentColor"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
      >
        SILICO
      </text>

      {/* Filled half — FELLER */}
      <rect x="32" y="0" width="32" height="22" rx="1" fill="currentColor" />
      <text
        x="48"
        y="15"
        textAnchor="middle"
        fontSize="8"
        fontWeight="700"
        letterSpacing="1.2"
        fill="white"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
      >
        FELLER
      </text>
    </svg>
  );
}

/**
 * NVIDIA logo — green eye mark + wordmark, faithful to the official brand.
 */
export function NvidiaLogo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 120 36"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("h-5 w-auto", className)}
      aria-label="NVIDIA"
      role="img"
    >
      {/* ── Eye / leaf mark ── */}
      {/* Outer green shape */}
      <path
        d="M13.5 4C8.2 4 4 8.8 4 14.5c0 3.6 1.7 6.8 4.4 8.8V10.2c0-.4.3-.7.7-.7h1.2v14.9c1 .4 2 .6 3.2.6 5.3 0 9.5-4.3 9.5-9.5S18.8 4 13.5 4z"
        fill="#76B900"
      />
      {/* Inner dark cutout giving the "eye" shape */}
      <path
        d="M9.1 10.2v12.8c1.3.8 2.8 1.3 4.4 1.3 4.4 0 8-3.6 8-8s-3.6-8-8-8c-1.6 0-3.1.5-4.4 1.3v.6z"
        fill="#1a1a1a"
      />
      {/* Bright green inner leaf */}
      <path
        d="M13.5 8.5c3 0 5.5 2.5 5.5 5.5s-2.5 5.5-5.5 5.5c-.8 0-1.5-.2-2.2-.5V9c.7-.3 1.4-.5 2.2-.5z"
        fill="#76B900"
      />

      {/* ── NVIDIA wordmark ── */}
      {/* N */}
      <path
        d="M30 10h2.2l4.2 9.5V10h2v14h-2.2L32 14.5V24h-2V10z"
        fill="#1a1a1a"
      />
      {/* V */}
      <path
        d="M40 10h2.3l3 10.5L48.3 10h2.2L46 24h-2.5L40 10z"
        fill="#1a1a1a"
      />
      {/* I */}
      <path d="M52 10h2v14h-2V10z" fill="#1a1a1a" />
      {/* D */}
      <path
        d="M56 10h4c3.3 0 6 2.7 6 7s-2.7 7-6 7h-4V10zm2 2v10h2c2.2 0 4-1.8 4-5s-1.8-5-4-5h-2z"
        fill="#1a1a1a"
      />
      {/* I */}
      <path d="M68 10h2v14h-2V10z" fill="#1a1a1a" />
      {/* A */}
      <path
        d="M74 10h2.5l5 14h-2.2l-1.1-3.2h-5.9L71.2 24H69L74 10zm1.2 3.2l-2.2 6h4.4l-2.2-6z"
        fill="#1a1a1a"
      />
    </svg>
  );
}
