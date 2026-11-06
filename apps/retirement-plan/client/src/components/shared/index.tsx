/**
 * components/shared — shared building blocks for every tab of the unified accelerator app
 * (BRAND_GUIDE §0). Colors come only from styles/tokens.css via Tailwind keys.
 */
import { Component, useEffect, useId, useState, type ReactNode, type ErrorInfo } from 'react';
import { ExternalLink, Inbox, CheckCircle2, Calculator, MinusCircle, AlertTriangle, Info, type LucideIcon } from 'lucide-react';

export { LakeLinkHeader, LakeLinkHeader as BrandHeader, getBrandName, getFootprintLabel } from '../LakeLinkHeader';
export { TabBar, tabId, panelId } from './TabBar';
export type { TabDef } from './TabBar';

/** Charter rule: synthetic data must be labeled in the UI. */
export function SyntheticBadge({ label = 'SYNTHETIC' }: { label?: string }) {
  return <span className="ll-badge-synthetic" title="Synthetic demo data — not real customer or network records">{label}</span>;
}

/** One KPI card (label, value, sub). valueClass must be a text-safe token class. */
export function KpiCard({ label, value, sub, valueClass = 'text-secondary', busy = false, hint }: { label: string; value: ReactNode; sub?: ReactNode; valueClass?: string; busy?: boolean; hint?: string }) {
  return (
    <div className="rounded-lg border border-border bg-card p-3 shadow-sm" aria-busy={busy || undefined}>
      <div className="flex items-center gap-1 mb-1">
        <p className="text-xs text-muted-foreground">{label}</p>
        {hint && <KpiHint label={label} hint={hint} />}
      </div>
      <p className={`text-xl font-bold ${valueClass}`}>{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
    </div>
  );
}

/**
 * BRAND_GUIDE §0.4 one-line tooltip (WCAG 1.4.13): shows on hover AND focus, stays while hovered,
 * Esc closes. Lucide Info 14px / 1.5px stroke in a 24px button (8px grid). No title attribute.
 */
function KpiHint({ label, hint }: { label: string; hint: string }) {
  const id = useId();
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open]);
  return (
    <span className="relative inline-flex" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <button type="button" aria-label={`About ${label}`} aria-describedby={id}
        className="inline-flex h-6 w-6 items-center justify-center rounded text-muted-foreground"
        onFocus={() => setOpen(true)} onBlur={() => setOpen(false)}>
        <Info size={14} strokeWidth={1.5} aria-hidden="true" />
      </button>
      <span id={id} role="tooltip" hidden={!open}
        className="absolute left-0 top-full z-20 mt-1 w-64 rounded bg-secondary px-2 py-1 text-xs text-secondary-foreground shadow-sm">
        {hint}
      </span>
    </span>
  );
}

/**
 * Verification mapping (BRAND_GUIDE §0.2, ACC-APP-CITATION-STATUS-MAP): any status starting with
 * 'verified_' (register: verified_url_200, verified_statute_text; matrix: VERIFIED_STATUTE_TEXT,
 * VERIFIED_OFFICIAL_PAGE) is verified. Everything else (unverified_detail, UNVERIFIED_CONFLICT,
 * NOT_FOUND, STATE_GAP, ...) is UNVERIFIED. Never test for the literal string 'verified'.
 */
export function isVerifiedStatus(status?: string | null): boolean {
  return !!status && status.trim().toLowerCase().startsWith('verified_');
}

/**
 * ACC-APP-REG-BADGE-STATUS — status badge lookup per BRAND_GUIDE §0.2 #status-badges (binding).
 * Case-insensitive after trim. Unknown / null / empty falls back to UNVERIFIED (fail safe).
 * `citable` = may be shown as a cited fact (Verified, Derived, verified absence). isVerifiedStatus stays the strict verified_* alias.
 */
export type StatusKind = 'verified_statute' | 'verified_page' | 'derived' | 'no_state_rule' | 'unverified';
export interface StatusBadgeSpec { kind: StatusKind; label: string; textClass: string; Icon: LucideIcon; citable: boolean; tooltip: string }
const BADGES: Record<StatusKind, StatusBadgeSpec> = {
  verified_statute: { kind: 'verified_statute', label: 'Verified · statute text', textClass: 'text-success', Icon: CheckCircle2, citable: true,
    tooltip: 'Quoted or paraphrased from the full text of the cited statute, rule or order.' },
  verified_page: { kind: 'verified_page', label: 'Verified · official page', textClass: 'text-success', Icon: CheckCircle2, citable: true,
    tooltip: 'Official page confirmed live. Content is summarized from the page, not quoted verbatim.' },
  derived: { kind: 'derived', label: 'Derived from statute', textClass: 'text-foreground', Icon: Calculator, citable: true,
    tooltip: 'This value was computed from verified statute text and is not stated directly. See the note for the derivation.' },
  no_state_rule: { kind: 'no_state_rule', label: 'No state requirement', textClass: 'text-muted-foreground', Icon: MinusCircle, citable: true,
    tooltip: 'The cited statute was read in full and has no hold-period requirement. This is a verified absence, not a gap.' },
  unverified: { kind: 'unverified', label: 'Unverified', textClass: 'text-warning', Icon: AlertTriangle, citable: false,
    tooltip: 'Not yet confirmed against the official text. Do not cite as fact.' },
};
export function getStatusBadge(status?: string | null): StatusBadgeSpec {
  const s = (status || '').trim().toLowerCase();
  if (s === 'verified_statute_text') return BADGES.verified_statute;
  if (s === 'verified_official_page' || s === 'verified_url_200') return BADGES.verified_page;
  if (s === 'derived_from_statute') return BADGES.derived;
  if (s === 'no_state_hold_period') return BADGES.no_state_rule;
  return BADGES.unverified;
}
export function isCitableStatus(status?: string | null): boolean {
  return getStatusBadge(status).citable;
}
/** Icon + word (never color-only, WCAG 1.4.1); tooltip in title AND sr-only (not hover-only). */
export function StatusBadge({ status }: { status?: string | null }) {
  const b = getStatusBadge(status);
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium ${b.textClass}`} title={b.tooltip} data-status={b.kind}>
      <b.Icon size={14} strokeWidth={1.5} aria-hidden="true" />{b.label}<span className="sr-only">: {b.tooltip}</span>
    </span>
  );
}

/**
 * Citation contract (charter hard rule): every regulatory fact shows the source title + official URL.
 * Secondary line = citation + last_verified (BRAND_GUIDE §0.2). Never renders a link without a URL.
 * ACC-APP-JUR-CITATION-URL: optional `citationUrl` = section-level page containing the cited value. When set,
 * the title links there and the official source URL (`url`) is still shown as "Official source".
 */
export function CitationLink({ title, url, verificationStatus, citation, lastVerified, citationUrl, hideStatusChip }: {
  title: string; url?: string | null; verificationStatus?: string | null; citation?: string | null; lastVerified?: string | null; citationUrl?: string | null;
  /** BRAND_GUIDE 'One status signal per row': set when the row already renders a StatusBadge. */
  hideStatusChip?: boolean;
}) {
  // ACC-DES-DEF-REG-MATRIX-HIDDEN-GAPS: no-URL state is distinct from UNVERIFIED-with-URL.
  if (!url) return <span className="ll-badge-synthetic">No official source found</span>;
  const unverified = verificationStatus != null && verificationStatus !== '' && !isCitableStatus(verificationStatus);
  const secondary = [citation, lastVerified ? `verified ${lastVerified}` : null].filter(Boolean).join(' · ');
  const href = citationUrl || url;
  const showSource = !!citationUrl && citationUrl !== url;
  return (
    <span className="inline-flex flex-col text-xs">
      <span className="inline-flex items-center gap-1">
        <a href={href} target="_blank" rel="noopener noreferrer" title={secondary || href} className="text-primary-strong underline underline-offset-2 hover:no-underline">
          {title}
          <ExternalLink size={12} strokeWidth={1.5} className="inline ml-0.5" aria-hidden="true" />
          <span className="sr-only"> (opens official source in new tab)</span>
        </a>
        {unverified && !hideStatusChip && <span className="ll-badge-synthetic">UNVERIFIED</span>}
      </span>
      {secondary && <span className="text-muted-foreground">{secondary}</span>}
      {showSource && (
        <a href={url} target="_blank" rel="noopener noreferrer" className="text-muted-foreground underline underline-offset-2 hover:no-underline">
          Official source<span className="sr-only"> for {title} (opens in new tab)</span>
        </a>
      )}
    </span>
  );
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-card p-8 text-center">
      <Inbox size={24} strokeWidth={1.5} className="mx-auto text-muted-foreground" aria-hidden="true" />
      <h2 className="text-base font-semibold text-secondary mt-2">{title}</h2>
      {children && <div className="text-sm text-muted-foreground mt-2 max-w-xl mx-auto">{children}</div>}
    </div>
  );
}

/** Per-tab error boundary so one failing tab never blanks the whole accelerator. */
export class ErrorBoundary extends Component<{ name: string; children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error(`[accelerator:${this.props.name}]`, error, info); }
  render() {
    if (this.state.error) {
      return (
        <EmptyState title={`The ${this.props.name} tab hit an error`}>
          <p>{this.state.error.message}</p>
          <button type="button" className="mt-3 text-xs bg-primary-strong text-primary-foreground px-3 py-1.5 rounded" onClick={() => this.setState({ error: null })}>Retry</button>
        </EmptyState>
      );
    }
    return this.props.children;
  }
}

/** Per-tab page template header: H2 title + the business question it answers + optional badges. */
export function TabHeader({ title, question, badges }: { title: string; question: string; badges?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-2 mb-4">
      <div>
        <h2 className="text-xl font-bold text-secondary">{title}</h2>
        <p className="text-sm text-muted-foreground">{question}</p>
      </div>
      {badges && <div className="flex items-center gap-2">{badges}</div>}
    </div>
  );
}
