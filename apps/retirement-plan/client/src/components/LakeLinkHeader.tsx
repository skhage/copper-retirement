/**
 * LakeLinkHeader.tsx
 * Shared nav header for all Lakelink Fiber apps (BRAND_GUIDE §5 Nav Header).
 *
 * Spec:
 *   - Left: brand wordmark (secondary, 600 weight, 16px) — partner rebrand via BRAND_NAME / tokens.css
 *   - Left: App subtitle (h1) + tagline (muted-foreground)
 *   - Right: Data source badge (LIVE/MOCK + SYNTHETIC)
 *   - Background: bg-background with border-border
 *
 * Colors come ONLY from tokens.css via Tailwind keys (ACC-APP-TOKENS-WIRE). No hex literals.
 */

/** Wordmark text. Partners change this together with --brand-name in tokens.css. */
export const BRAND_NAME = 'Lakelink Fiber';

export interface LakeLinkHeaderProps {
  /** App subtitle shown below wordmark */
  subtitle: string;
  /** Optional tagline below subtitle */
  tagline?: string;
  /** Data source: 'LIVE' | 'MOCK'. Defaults to 'MOCK'. */
  dataSource?: 'LIVE' | 'MOCK';
  /** Whether to show the SYNTHETIC badge. Defaults true. */
  showSynthetic?: boolean;
  /** Optional right-side children (e.g. global filters) */
  children?: React.ReactNode;
}

export function LakeLinkHeader({
  subtitle,
  tagline,
  dataSource = 'MOCK',
  showSynthetic = true,
  children,
}: LakeLinkHeaderProps) {
  const badgeBg = dataSource === 'LIVE' ? 'bg-accent/20' : 'bg-viz-4/20';

  return (
    <header className="bg-background border-b border-border px-4 md:px-6 py-4 flex flex-wrap items-center justify-between gap-3 font-sans">
      {/* Left: wordmark + subtitle */}
      <div>
        <p className="text-base font-semibold text-secondary leading-tight m-0">{BRAND_NAME}</p>
        <h1 className="text-2xl font-bold text-secondary leading-tight mt-1">{subtitle}</h1>
        {tagline && <p className="text-[13px] text-muted-foreground mt-0.5">{tagline}</p>}
      </div>

      {/* Right: children (filters etc.) + data source badge */}
      <div className="flex items-center gap-3">
        {children}
        <span className={`text-[11px] px-2.5 py-1 rounded font-medium text-secondary ${badgeBg}`}>
          {dataSource} DATA
        </span>
        {showSynthetic && <span className="ll-badge-synthetic">SYNTHETIC</span>}
      </div>
    </header>
  );
}
