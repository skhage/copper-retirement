/**
 * components/shared — shared building blocks for every tab of the unified accelerator app
 * (BRAND_GUIDE §0). Colors come only from styles/tokens.css via Tailwind keys.
 */
import { Component, type ReactNode, type ErrorInfo } from 'react';
import { ExternalLink, Inbox } from 'lucide-react';

export { LakeLinkHeader, BRAND_NAME } from '../LakeLinkHeader';
export { TabBar, tabId, panelId } from './TabBar';
export type { TabDef } from './TabBar';

/** Charter rule: synthetic data must be labeled in the UI. */
export function SyntheticBadge({ label = 'SYNTHETIC' }: { label?: string }) {
  return <span className="ll-badge-synthetic" title="Synthetic demo data — not real customer or network records">{label}</span>;
}

/** One KPI card (label, value, sub). valueClass must be a text-safe token class. */
export function KpiCard({ label, value, sub, valueClass = 'text-secondary', busy = false }: { label: string; value: ReactNode; sub?: ReactNode; valueClass?: string; busy?: boolean }) {
  return (
    <div className="rounded-lg border border-border bg-card p-3 shadow-sm" aria-busy={busy || undefined}>
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className={`text-xl font-bold ${valueClass}`}>{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
    </div>
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
 * Citation contract (charter hard rule): every regulatory fact shows the source title + official URL.
 * Secondary line = citation + last_verified (BRAND_GUIDE §0.2). Never renders a link without a URL.
 * ACC-APP-JUR-CITATION-URL: optional `citationUrl` = section-level page containing the cited value. When set,
 * the title links there and the official source URL (`url`) is still shown as "Official source".
 */
export function CitationLink({ title, url, verificationStatus, citation, lastVerified, citationUrl }: {
  title: string; url?: string | null; verificationStatus?: string | null; citation?: string | null; lastVerified?: string | null; citationUrl?: string | null;
}) {
  if (!url) return <span className="ll-badge-synthetic">Source not yet verified</span>;
  const unverified = verificationStatus != null && verificationStatus !== '' && !isVerifiedStatus(verificationStatus);
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
        {unverified && <span className="ll-badge-synthetic">UNVERIFIED</span>}
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
