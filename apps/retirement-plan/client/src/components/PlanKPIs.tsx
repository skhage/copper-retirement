/**
 * PlanKPIs.tsx
 * Top bar with 6 KPI cards for the Retirement Plan Tracker.
 * Shows: total wire centers, % planned, % in-flight, % completed,
 * budget allocated/remaining, customers migrated/remaining.
 */
import { computeKPIs, USE_MOCK_DATA } from '../mock/mockData';
import { formatCount, formatCurrency, formatPercent } from '../lib/formatters';

export function PlanKPIs() {
  // TODO: Replace with live SQL query (config/queries/plan_kpis.sql) when USE_MOCK_DATA=false
  const kpis = USE_MOCK_DATA ? computeKPIs() : computeKPIs();

  const cards = [
    {
      label: 'Wire Centers',
      value: formatCount(kpis.total_wire_centers),
      sub: `${formatPercent(kpis.pct_completed)} complete`,
      color: 'text-[#1B3139]',
    },
    {
      label: 'Planned',
      value: formatPercent(kpis.pct_planned),
      sub: 'awaiting start',
      color: 'text-[#6E8898]',
    },
    {
      label: 'In Flight',
      value: formatPercent(kpis.pct_in_flight),
      sub: 'active migration',
      color: 'text-primary',
    },
    {
      label: 'Completed',
      value: formatPercent(kpis.pct_completed),
      sub: 'fully retired',
      color: 'text-accent',
    },
    {
      label: 'Budget Remaining',
      value: formatCurrency(kpis.total_budget_remaining),
      sub: `of ${formatCurrency(kpis.total_budget_allocated)} allocated`,
      color: 'text-[#FF8C69]',
    },
    {
      label: 'Customers Remaining',
      value: formatCount(kpis.customers_remaining),
      sub: `${formatCount(kpis.customers_migrated)} migrated`,
      color: 'text-primary',
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
