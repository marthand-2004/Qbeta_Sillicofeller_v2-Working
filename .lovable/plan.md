# Silicofeller Auth — White/Black/Purple Re-skin

Shift the existing auth pages from the blue/cyan "quantum" palette to a Decagon-inspired enterprise system: ~80% white, ~15% black, ~5% purple accent. No structural route changes — only design tokens, logo, hero, buttons, and a few page surfaces.

## Design tokens (`src/styles.css`)

Replace the current blue/cyan light theme values:

- `--background` `#FFFFFF`
- `--secondary` / surface `#FAFAFA`
- `--card` `#FFFFFF`
- `--border` / `--input` `#E5E7EB`
- `--foreground` `#0A0A0A`
- `--muted-foreground` `#525252` (with `#737373` available as a softer muted variant)
- `--primary` `#000000`, `--primary-foreground` `#FFFFFF` (black CTAs)
- `--accent` `#6D5AF0` (purple, used sparingly)
- `--accent-foreground` `#FFFFFF`
- New: `--accent-soft` `#EDE9FE`, `--accent-2` `#8B7AF7`
- `--ring` switches from blue to `#0A0A0A` (black focus ring) with a faint purple glow option for primary actions
- Replace gradient tokens:
  - Remove `--gradient-quantum` (blue→cyan) and `--gradient-hero` (blue radial)
  - Add `--gradient-accent` `linear-gradient(135deg, #6D5AF0, #8B7AF7)` for the rare highlight
  - Add `--gradient-hero` as a very subtle white radial with a faint purple wash near a corner
- `--shadow-card` `0 10px 40px rgba(0,0,0,0.05)` per spec
- Bump card radius usage to ~`24px` via existing `rounded-3xl` (no global `--radius` change needed)

All values rewritten in `oklch` to match the file's existing format. Dark theme stays as-is (out of scope).

## Logo (`src/components/silicofeller-logo.tsx`)

Re-color the existing inline SVG:

- Chip substrate outline: black at low opacity (`#0A0A0A` / 0.15)
- "S" circuit trace: solid `#000000`
- Neural dashed cross-connection: black at 0.25 opacity
- Qubit nodes: two nodes in `#6D5AF0`, one accent in `#8B7AF7`, center node black
- Wordmark: `#0A0A0A` in the existing display font
- Remove the blue→cyan gradient definition

Both `horizontal` and `icon` variants keep their current API.

## Buttons

- Primary CTA: use the default shadcn `Button` (now black via new `--primary` token). Remove the inline `style={{ background: "var(--gradient-quantum)" }}` overrides on Sign in / Create account buttons. Pill shape per spec → add `rounded-full` and `h-11` on the main CTAs.
- Hover handled by existing `hover:bg-primary/90` (resolves to `#171717`-ish).
- Secondary / social buttons: already white with `#E5E7EB` border via `variant="outline"` — no change beyond inheriting new tokens. Make their radius match (`rounded-full`) for consistency.
- Links (`Forgot password?`, footer "Sign up"): change from `text-primary` (now black) to `text-accent` so the purple still reads as the interactive accent. Add `hover:text-accent/80`.

## Quantum hero (`src/components/auth/quantum-hero.tsx`)

Keep the composition (chip blueprint + floating glass cards + pulsing nodes) but re-skin:

- Background: white with `--gradient-hero` (very faint purple radial in one corner, otherwise white)
- Grid backdrop lines: `#0A0A0A` at ~0.06 opacity
- Circuit trace paths: `#0A0A0A` at ~0.7 opacity, thinner stroke
- Qubit lattice nodes: black dots with a few `#6D5AF0` highlights and a soft `#EDE9FE` halo on the pulsing ones
- Floating glass cards: white background, `1px solid #E5E7EB`, `shadow-card`, black text; a small purple status dot / accent chip per card
- Headline & body copy stay black (`--foreground`)
- Remove any blue/cyan fills or gradient strokes

## Auth card (`src/components/auth/auth-card.tsx`)

- Background `#FFFFFF`, border `1px solid #E5E7EB`, `shadow-card`, radius `24px` (swap `rounded-2xl` → `rounded-3xl`)
- Title in `#0A0A0A`; subtitle in `#525252` — already aligned once tokens change
- Remove any cyan/blue accent in the divider — keep `bg-border`

## Pages (sign-in, sign-up, forgot-password)

No layout/structure changes. Only:

- Replace the gradient CTA style overrides with the new black pill button
- Recolor inline links (`text-primary` → `text-accent` where they were meant as the accent)
- Forgot-password success check icon: black ring with `#6D5AF0` check, or solid `#EDE9FE` circle with `#6D5AF0` check (lighter, on-brand)
- Hero copy updates per spec:
  - Headline: "Design Quantum Chips Using AI"
  - Subheadline: "Transform engineering requirements into production-ready quantum architectures through natural language."

## Auth layout (`src/components/auth/auth-layout.tsx`)

- Page background `#FFFFFF` (drop any blue tint)
- Optional very subtle `--gradient-hero` wash behind the whole shell
- Footer text in `#737373`

## Out of scope

- No new routes, no dashboard, no billing page (spec mentions them, but current project scope is auth only — flagged for a future task)
- Dark theme palette untouched
- No new dependencies
- No AI-generated imagery — hero stays pure SVG

## Technical notes

- All color edits go through `src/styles.css` tokens; components keep using semantic classes (`bg-background`, `text-foreground`, `border-border`, `bg-primary`, `text-accent`, etc.). The only direct color references remaining will be inside the logo SVG and hero SVG, where literal hex is appropriate for illustration.
- `oklch` conversions for the new hexes will be computed and written into `:root` so Tailwind utilities like `bg-accent` and `text-accent` resolve to `#6D5AF0`.
- Verify visually at `/sign-in`, `/sign-up`, `/forgot-password` after the change.
