/**
 * TriageKPIs.tsx
 * Top bar showing 6 KPI cards for the dig-safe triage console.
 * Live values are an as-of replay (COO-Q-20261026-0550-3): anchored to the latest incident in the
 * SYNTHETIC table silver_dig_incident_enriched, not wall-clock today, so the cards are never all zero.
 * States (ACC-DES-DEF-TRIAGE-KPI-FALLBACK): loading = '…' + aria-busy; 403 = '—' + 'Data access pending';
 * other errors = '—' + 'Could not load'. Mock values render ONLY when USE_MOCK_DATA === true, with SyntheticBadge.
 */
import { useState, useEffect } from 'react';
import { USE_MOCK_DATA, getMockKPIs } from '../mock/mockData';
import type { TriageKPIs as TriageKPIsType } from '../mock/mockData';
import { fetchKPIs, ApiError } from '../lib/triageApi';
import { formatCount } from '../lib/formatters';
import { KpiCard, SyntheticBadge } from '../../../components/shared';

type LoadState = 'loading' | 'live' | 'mock' | 'denied' | 'error';

export function TriageKPIs() {
  // Never seed with fabricated numbers: mock values only exist when USE_MOCK_DATA is on.
  const [kpis, setKpis] = useState<TriageKPIsType | null>(USE_MOCK_DATA ? getMockKPIs() : null);
  const [state, setState] = useState<LoadState>(USE_MOCK_DATA ? 'mock' : 'loading');
  const [asOf, setAsOf] = useState<string | null>(null);
  const [windowDays, setWindowDays] = useState(30);

  useEffect(() => {
    if (USE_MOCK_DATA) return;
    let cancelled = false;
    fetchKPIs()
      .then((data) => {
        if (cancelled) return;
        setKpis(data);
        setAsOf(data.as_of ? data.as_of.slice(0, 10) : null);
        setWindowDays(data.window_days || 30);
        setState('live');
      })
      .catch((err) => {
        if (cancelled) return;
        console.warn('[TriageKPIs] Live fetch failed:', err);
        setKpis(null);
        setState(err instanceof ApiError && err.status === 403 ? 'denied' : 'error');
      });
    return () => { cancelled = true; };
  }, []);

  const busy = state === 'loading';
  const failSub = state === 'denied' ? 'Data access pending' : state === 'error' ? 'Could not load' : undefined;
  const val = (fn: (k: TriageKPIsType) => string) => (kpis ? fn(kpis) : busy ? '…' : '—');
  const sub = (ok: string) => (kpis ? ok : failSub);

  const cards = [
    { label: 'Open at as-of', value: val((k) => formatCount(k.open_incidents)), valueClass: 'text-primary-strong', sub: sub('not yet resolved') },
    { label: 'Avg Resolution', value: val((k) => `${k.avg_resolution_hours.toFixed(1)}h`), valueClass: 'text-warning', sub: sub(`last ${windowDays} days`) },
    { label: 'Last 7 Days', value: val((k) => formatCount(k.incidents_this_week)), valueClass: 'text-secondary', sub: sub('new incidents') },
    { label: 'Reroutes Required', value: val((k) => formatCount(k.reroutes_pending)), valueClass: 'text-muted-foreground', sub: sub(`last ${windowDays} days`) },
    { label: 'Active Contractors', value: val((k) => formatCount(k.active_contractors)), valueClass: 'text-accent-strong', sub: sub('available for dispatch') },
    { label: 'Critical', value: val((k) => formatCount(k.critical_incidents)), valueClass: 'text-primary-strong', sub: sub(`last ${windowDays} days`) },
  ];

  const note =
    state === 'live' ? `Replay as of ${asOf ?? 'latest incident'} (synthetic incident data; windows end at the as-of date, not today).`
    : state === 'mock' ? 'Mock data mode (USE_MOCK_DATA): values are illustrative, not from any table.'
    : state === 'denied' ? 'Data access pending: the app service principal lacks SELECT on the triage source table.'
    : state === 'error' ? 'Could not load live triage KPIs.'
    : 'Loading triage KPIs…';

  return (
    <>
    <p className="text-xs text-muted-foreground mb-2 flex items-center gap-2" role="note" aria-live="polite">
      {state === 'mock' && <SyntheticBadge label="MOCK" />}
      <span>{note}</span>
    </p>
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-4" aria-busy={busy || undefined}>
      {cards.map((c) => (
        <KpiCard key={c.label} label={c.label} value={c.value} sub={c.sub} valueClass={c.valueClass} busy={busy} />
      ))}
    </div>
    </>
  );
}
