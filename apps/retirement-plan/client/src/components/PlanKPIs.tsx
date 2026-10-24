/**
 * PlanKPIs.tsx
 * Top bar with 6 KPI cards for the Retirement Plan Tracker.
 * V2 (2026-09-20): Fetches live KPIs from gold_wave_schedule.
 * Falls back to mock computeKPIs() if live data unavailable.
 */
import { useState, useEffect } from 'react';
import { computeKPIs, USE_MOCK_DATA } from '../mock/mockData';
import { fetchLiveKPIs } from '../lib/planApi';
import type { LiveKPIs } from '../lib/planApi';
import { formatCount, formatCurrency, formatPercent } from '../lib/formatters';

export function PlanKPIs() {
  const [liveKPIs, setLiveKPIs] = useState<LiveKPIs | null>(null);

  useEffect(() => {
    fetchLiveKPIs().then(setLiveKPIs);
  }, []);

  const mockKPIs = computeKPIs();

  // Build card data from live or mock KPIs
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
    : [
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
      ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-lg border bg-card p-3 shadow-sm"
        >
          <p className="text-xs text-muted-foreground mb-1">{card.label}</p>
          <p className={`text-xl font-bold ${card.color}`}>{card.value}</p>
          <p className="text-xs text-muted-foreground mt-1">{card.sub}</p>
        </div>
      ))}
    </div>
  );
}
