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
export function KpiCard({ label, value, sub, valueClass = 'text-secondary' }: { label: string; value: ReactNode; sub?: ReactNode; valueClass?: string }) {
  return (
    <div className="rounded-lg border border-border bg-card p-3 shadow-sm">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className={`text-xl font-bold ${valueClass}`}>{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
    </div>
  );
}

/**
 * Citation contract (charter hard rule): every regulatory fact shows the source title + official URL.
 * Renders an UNVERIFIED badge when verification_status !== 'verified'. Never renders without a URL.
 */
export function CitationLink({ title, url, verificationStatus }: { title: string; url: string; verificationStatus?: string }) {
  const unverified = verificationStatus && verificationStatus.toLowerCase() !== 'verified';
  return (
    <span className="inline-flex items-center gap-1 text-xs">
      <a href={url} target="_blank" rel="noopener noreferrer" className="text-primary-strong underline underline-offset-2 hover:no-underline">
        {title}
        <ExternalLink size={12} strokeWidth={1.5} className="inline ml-0.5" aria-hidden="true" />
        <span className="sr-only"> (opens official source in new tab)</span>
      </a>
      {unverified && <span className="ll-badge-synthetic">UNVERIFIED</span>}
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
