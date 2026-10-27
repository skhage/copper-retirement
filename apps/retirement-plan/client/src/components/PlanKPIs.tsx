/**
 * PlanKPIs.tsx
 * Top bar with 6 KPI cards for the Retirement Plan Tracker.
 * V2 (2026-09-20): Fetches live KPIs from gold_wave_schedule.
 * ACC-DES-DEF-PLAN-KPI-FALLBACK (2026-10-27): no mock fallback. States: loading = '…' + aria-busy;
 * 403 = '—' + 'Data access pending'; other errors = '—' + 'Could not load'. computeKPIs() mock values are
 * reachable ONLY when USE_MOCK_DATA === true (false in the build), and then carry a MOCK badge.
 */
import { useState, useEffect } from 'react';
import { computeKPIs, USE_MOCK_DATA } from '../mock/mockData';
import { fetchLiveKPIs, errorState, failText } from '../lib/planApi';
import type { LiveKPIs, LoadState } from '../lib/planApi';
import { formatCount, formatCurrency, formatPercent } from '../lib/formatters';
import { KpiCard, SyntheticBadge } from './shared';

const LABELS = ['Wire Centers', 'Copper Devices', 'Avg Readiness', 'Crew-Days', 'Revenue at Risk', 'Customers Affected'];

export function PlanKPIs() {
  const [liveKPIs, setLiveKPIs] = useState<LiveKPIs | null>(null);
  const [state, setState] = useState<LoadState>(USE_MOCK_DATA ? 'mock' : 'loading');

  useEffect(() => {
    if (USE_MOCK_DATA) return;
    let cancelled = false;
    fetchLiveKPIs()
      .then((k) => { if (!cancelled) { setLiveKPIs(k); setState('live'); } })
      .catch((err) => {
        if (cancelled) return;
        console.warn('[PlanKPIs] Live fetch failed:', err);
        setLiveKPIs(null);
        setState(errorState(err));
      });
    return () => { cancelled = true; };
  }, []);

  const busy = state === 'loading';
  const mockKPIs = USE_MOCK_DATA ? computeKPIs() : null;

  const cards = liveKPIs
    ? [
        {
          label: 'Wire Centers',
          value: formatCount(liveKPIs.total_wire_centers),
          sub: `${liveKPIs.total_waves} waves · ${liveKPIs.total_states} states`,
          color: 'text-secondary',
        },
        {
          label: 'Copper Devices',
          value: formatCount(liveKPIs.total_devices),
          sub: `${formatCount(liveKPIs.total_critical_devices)} critical risk`,
          color: 'text-primary-strong',
        },
        {
          label: 'Avg Readiness',
          value: `${liveKPIs.avg_readiness}%`,
          sub: `${liveKPIs.fiber_ready_count} fiber-ready`,
          color: 'text-accent-strong',
        },
        {
          label: 'Crew-Days',
          value: formatCount(liveKPIs.total_crew_days),
          sub: `${liveKPIs.first_wave} → ${liveKPIs.last_wave}`,
          color: 'text-muted-foreground',
        },
        {
          label: 'Revenue at Risk',
          value: formatCurrency(Number(liveKPIs.total_revenue_at_risk)),
          sub: 'annual across all waves',
          color: 'text-warning',
        },
        {
          label: 'Customers Affected',
          value: formatCount(liveKPIs.total_customers),
          sub: `${liveKPIs.puc_required_count} PUC filings required`,
          color: 'text-primary-strong',
        },
      ]
    : mockKPIs
    ? [
        {
          label: 'Wire Centers',
          value: formatCount(mockKPIs.total_wire_centers),
          sub: `${formatPercent(mockKPIs.pct_completed)} complete`,
          color: 'text-secondary',
        },
        {
          label: 'Planned',
          value: formatPercent(mockKPIs.pct_planned),
          sub: 'awaiting start',
          color: 'text-muted-foreground',
        },
        {
          label: 'In Flight',
          value: formatPercent(mockKPIs.pct_in_flight),
          sub: 'active migration',
          color: 'text-primary-strong',
        },
        {
          label: 'Completed',
          value: formatPercent(mockKPIs.pct_completed),
          sub: 'fully retired',
          color: 'text-accent-strong',
        },
        {
          label: 'Budget Remaining',
          value: formatCurrency(mockKPIs.total_budget_remaining),
          sub: `of ${formatCurrency(mockKPIs.total_budget_allocated)} allocated`,
          color: 'text-warning',
        },
        {
          label: 'Customers Remaining',
          value: formatCount(mockKPIs.customers_remaining),
          sub: `${formatCount(mockKPIs.customers_migrated)} migrated`,
          color: 'text-primary-strong',
        },
      ]
    : LABELS.map((label) => ({ label, value: busy ? '…' : '—', sub: failText(state), color: 'text-muted-foreground' }));

  const note =
    state === 'live' ? 'Live from gold_wave_schedule (synthetic plan data).'
    : state === 'mock' ? 'Mock data mode (USE_MOCK_DATA): values are illustrative, not from any table.'
    : state === 'denied' ? 'Data access pending: the app service principal lacks SELECT on the plan tables.'
    : state === 'error' ? 'Could not load live plan KPIs.'
    : 'Loading plan KPIs…';

  return (
    <>
      <p className="text-xs text-muted-foreground mb-2 flex items-center gap-2" role="note" aria-live="polite">
        {state === 'mock' && <SyntheticBadge label="MOCK" />}
        <span>{note}</span>
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-4" aria-busy={busy || undefined}>
        {cards.map((card) => (
          <KpiCard key={card.label} label={card.label} value={card.value} sub={card.sub} valueClass={card.color} busy={busy} />
        ))}
      </div>
    </>
  );
}
