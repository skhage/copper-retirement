/**
 * RegKPIs.tsx
 * Top bar KPI cards for the Regulatory Assistant.
 * Shows: jurisdictions covered, pending filings, days until next deadline,
 *        compliance %, overdue items, documents indexed.
 *
 * Uses Lakelink Fiber semantic status colors per BRAND_GUIDE §2 & §6.
 */
import { USE_MOCK_DATA, getMockKPIs } from '../mock/mockData';

/* Lakelink Fiber semantic status colors (BRAND_GUIDE §2) */
const LL_CRITICAL = '#FF3621';
const LL_HIGH     = '#FF8C69';
const LL_MEDIUM   = '#FFD700';
const LL_LOW      = '#00A972';
const LL_TEXT_PRIMARY   = '#1B3139';
const LL_TEXT_SECONDARY = '#6E8898';

interface RegKPIsProps {
  jurisdictionFilter: string;
}

export function RegKPIs({ jurisdictionFilter }: RegKPIsProps) {
  // TODO: Replace with useAnalyticsQuery('reg_kpis', params) when live
  const kpis = USE_MOCK_DATA ? getMockKPIs() : getMockKPIs();

  const cards: { label: string; value: string | number; color: string }[] = [
    { label: 'Jurisdictions', value: kpis.jurisdictions_covered, color: LL_TEXT_PRIMARY },
    { label: 'Pending Filings', value: kpis.pending_filings, color: kpis.pending_filings > 0 ? LL_MEDIUM : LL_TEXT_PRIMARY },
    { label: 'Next Deadline', value: `${kpis.days_until_next_deadline}d`, color: kpis.days_until_next_deadline < 30 ? LL_HIGH : LL_TEXT_PRIMARY },
    { label: 'Compliance', value: `${kpis.compliance_pct}%`, color: kpis.compliance_pct < 80 ? LL_MEDIUM : LL_LOW },
    { label: 'Overdue', value: kpis.overdue_items, color: kpis.overdue_items > 0 ? LL_CRITICAL : LL_TEXT_PRIMARY },
    { label: 'Documents', value: kpis.documents_indexed, color: LL_TEXT_PRIMARY },
  ];

  return (
    <div className="grid grid-cols-6 gap-3">
      {cards.map((card) => (
        <div
          key={card.label}
          style={{
            background: '#FFFFFF',
            border: '1px solid #E5E2DD',
            borderRadius: 8,
            padding: 12,
            textAlign: 'center',
          }}
        >
          <p className="text-xl font-bold" style={{ color: card.color, margin: 0 }}>{card.value}</p>
          <p className="text-xs uppercase" style={{ color: LL_TEXT_SECONDARY, letterSpacing: '0.05em', margin: '4px 0 0' }}>{card.label}</p>
        </div>
      ))}
    </div>
  );
}
