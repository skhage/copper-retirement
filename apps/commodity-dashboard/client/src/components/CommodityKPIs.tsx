/**
 * CommodityKPIs.tsx
 * Top bar with 8 KPI cards: spot price, 30d change, recovered weight,
 * scrap value, net recovery, active contractors, avg safety, decom projects.
 */
import { mockKPIs, USE_MOCK_DATA } from '../mock/mockData';
import { formatCurrency, formatPriceLb, formatPercent, formatWeight, formatCount } from '../lib/formatters';

interface KPICard {
  label: string;
  value: string;
  subtext?: string;
  color?: string;
}

export function CommodityKPIs() {
  // TODO: Replace with useAnalyticsQuery('commodity_kpis') when USE_MOCK_DATA=false
  const kpis = USE_MOCK_DATA ? mockKPIs : mockKPIs;

  const cards: KPICard[] = [
    {
      label: 'Copper Spot',
      value: formatPriceLb(kpis.current_spot_usd_lb),
      subtext: `${kpis.spot_30d_change_pct > 0 ? '+' : ''}${formatPercent(kpis.spot_30d_change_pct)} 30d`,
      color: kpis.spot_30d_change_pct >= 0 ? 'text-green-600' : 'text-red-600',
    },
    {
      label: 'Recovered Copper',
      value: formatWeight(kpis.total_recovered_lbs),
      subtext: 'Total program',
    },
    {
      label: 'Gross Scrap Value',
      value: formatCurrency(kpis.total_scrap_value_usd),
      subtext: 'Before processing',
    },
    {
      label: 'Net Recovery',
      value: formatCurrency(kpis.net_recovery_value_usd),
      subtext: 'After processing costs',
    },
    {
      label: 'Active Contractors',
      value: formatCount(kpis.active_contractors),
      subtext: 'With active agreements',
    },
    {
      label: 'Avg Safety Score',
      value: `${kpis.avg_safety_score}`,
      subtext: 'OSHA composite (0–100)',
      color: kpis.avg_safety_score >= 80 ? 'text-green-600' : 'text-yellow-600',
    },
    {
      label: 'Decom Projects',
      value: formatCount(kpis.decommission_projects),
      subtext: 'Active decommissions',
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3 mb-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-card border rounded-lg p-3 shadow-sm"
        >
          <p className="text-xs text-muted-foreground font-medium">{card.label}</p>
          <p className={`text-lg font-bold mt-1 ${card.color ?? ''}`}>{card.value}</p>
          {card.subtext && (
            <p className="text-xs text-muted-foreground mt-0.5">{card.subtext}</p>
          )}
        </div>
      ))}
    </div>
  );
}
