/**
 * TriageKPIs.tsx
 * Top bar showing 6 KPI cards for the dig-safe triage console.
 * Uses mock data until dig_safe_incident table + P6-TRIAGE agent land.
 */
import { USE_MOCK_DATA, getMockKPIs } from '../mock/mockData';
import { formatCount } from '../lib/formatters';

interface KPICard {
  label: string;
  value: string;
  color: string;
  subtext?: string;
}

export function TriageKPIs() {
  // TODO: Replace with live SQL query when USE_MOCK_DATA=false
  const kpis = getMockKPIs();

  const cards: KPICard[] = [
    {
      label: 'Open Incidents',
      value: formatCount(kpis.open_incidents),
      color: 'text-primary',
      subtext: `${kpis.critical_incidents} critical`,
    },
    {
      label: 'Avg Resolution',
      value: `${kpis.avg_resolution_hours.toFixed(1)}h`,
      color: 'text-[#FF8C69]',
      subtext: 'resolved incidents',
    },
    {
      label: 'This Week',
      value: formatCount(kpis.incidents_this_week),
      color: 'text-[#1B3139]',
      subtext: 'new incidents',
    },
    {
      label: 'Reroutes Pending',
      value: formatCount(kpis.reroutes_pending),
      color: 'text-[#6E8898]',
      subtext: 'awaiting approval',
    },
    {
      label: 'Active Contractors',
      value: formatCount(kpis.active_contractors),
      color: 'text-accent',
      subtext: 'available for dispatch',
    },
    {
      label: 'Critical',
      value: formatCount(kpis.critical_incidents),
      color: 'text-primary',
      subtext: 'require immediate action',
    },
  ];

  return (
    <div className="grid grid-cols-6 gap-3 mb-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-card rounded-lg border p-3 shadow-sm"
        >
          <p className="text-xs text-muted-foreground mb-1">{card.label}</p>
          <p className={`text-xl font-bold ${card.color}`}>{card.value}</p>
          {card.subtext && (
            <p className="text-xs text-muted-foreground mt-1">{card.subtext}</p>
          )}
        </div>
      ))}
    </div>
  );
}
