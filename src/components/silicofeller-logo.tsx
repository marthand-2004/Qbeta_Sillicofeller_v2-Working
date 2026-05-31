import { cn } from "@/lib/utils";

interface LogoProps {
  variant?: "horizontal" | "icon";
  className?: string;
  /** Tailwind size for the icon mark (height). Defaults to h-8. */
  iconClassName?: string;
}

/**
 * Silicofeller logo. The "S" mark is composed of semiconductor traces with
 * quantum node terminations and a neural connection across the chip.
 */
export function SilicofellerLogo({
  variant = "horizontal",
  className,
  iconClassName,
}: LogoProps) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <LogoMark className={cn("h-8 w-8", iconClassName)} />
      {variant === "horizontal" && (
        <span
          className="text-[1.0625rem] font-semibold tracking-[-0.02em] text-foreground"
          style={{ fontFamily: "var(--font-display)" }}
        >
          Silicofeller
        </span>
      )}
    </div>
  );
}

export function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* chip substrate */}
      <rect
        x="2.5"
        y="2.5"
        width="35"
        height="35"
        rx="8"
        stroke="#0A0A0A"
        strokeOpacity="0.15"
        strokeWidth="1"
      />
      {/* circuit-trace "S" */}
      <path
        d="M28 11 H17 a4 4 0 0 0 0 8 h6 a4 4 0 0 1 0 8 H12"
        stroke="#0A0A0A"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* neural cross-connection */}
      <path
        d="M14 14 L26 26"
        stroke="#0A0A0A"
        strokeOpacity="0.25"
        strokeWidth="1"
        strokeDasharray="1.5 2.5"
      />
      {/* qubit nodes */}
      <circle cx="28" cy="11" r="2" fill="#6D5AF0" />
      <circle cx="12" cy="27" r="2" fill="#6D5AF0" />
      <circle cx="20" cy="19" r="1.4" fill="#0A0A0A" />
      <circle cx="14" cy="14" r="0.9" fill="#8B7AF7" />
      <circle cx="26" cy="26" r="0.9" fill="#0A0A0A" />
    </svg>
  );
}