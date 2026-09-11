/**
 * RegKPIs.tsx
 * Top bar KPI cards for the Regulatory Assistant.
 * Shows: jurisdictions covered, pending filings, days until next deadline,
 *        compliance %, overdue items, documents indexed.
 */
import { USE_MOCK_DATA, getMockKPIs } from '../mock/mockData';

interface RegKPIsProps {
  jurisdictionFilter: string;
}

export function RegKPIs({ jurisdictionFilter }: RegKPIsProps) {
  // TODO: Replace with useAnalyticsQuery('reg_kpis', params) when live
  const kpis = USE_MOCK_DATA ? getMockKPIs() : getMockKPIs();

  const cards = [
    { label: 'Jurisdictions', value: kpis.jurisdictions_covered, color: '' },
    { label: 'Pending Filings', value: kpis.pending_filings, color: kpis.pending_filings > 0 ? 'text-yellow-600' : '' },
    { label: 'Next Deadline', value: `${kpis.days_until_next_deadline}d`, color: kpis.days_until_next_deadline < 30 ? 'text-orange-600' : '' },
    { label: 'Compliance', value: `${kpis.compliance_pct}%`, color: kpis.compliance_pct < 80 ? 'text-yellow-600' : 'text-green-600' },
    { label: 'Overdue', value: kpis.overdue_items, color: kpis.overdue_items > 0 ? 'text-red-600 font-bold' : '' },
    { label: 'Documents', value: kpis.documents_indexed, color: '' },
  ];

  return (
    <div className="grid grid-cols-6 gap-3">
      {cards.map((card) => (
        <div key={card.label} className="text-center">
          <p className={`text-xl font-bold ${card.color}`}>{card.value}</p>
          <p className="text-xs text-muted-foreground">{card.label}</p>
        </div>
      ))}
    </div>
  );
}
