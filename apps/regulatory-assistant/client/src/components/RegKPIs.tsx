/**
 * RegKPIs.tsx
 * Top bar KPI cards for the Regulatory Assistant.
 * Shows: jurisdictions covered, pending filings, days until next deadline,
 *        compliance %, overdue items, documents indexed.
 *
 * Uses AppKit Card/CardContent and follows BRAND_GUIDE §6 KPI Card spec:
 *   - Background: --ll-surface-elevated (#FFFFFF)
 *   - Label: uppercase, tracking-wide, --ll-text-secondary (#6E8898), 12px
 *   - Value: --ll-text-primary (#1B3139) or semantic color, 28px bold
 *   - Subtitle: --ll-text-secondary, 11px (optional)
 *   - Border: 1px #E5E2DD, radius 8px, no shadows
 *
 * Layout: grid-cols-6 (6 KPIs — brand guide allows 6 for 6 items).
 */
import { USE_MOCK_DATA, getMockKPIs } from '../mock/mockData';

/* Lakelink Fiber semantic status colors (BRAND_GUIDE §2) */
const LL_CRITICAL = '#FF3621';
const LL_HIGH     = '#FF8C69';
const LL_MEDIUM   = '#FFD700';
const LL_LOW      = '#00A972';
const LL_TEXT_PRIMARY   = '#1B3139';
const LL_TEXT_SECONDARY = '#6E8898';
const LL_BORDER = '#E5E2DD';

interface RegKPIsProps {
  jurisdictionFilter: string;
}

export function RegKPIs({ jurisdictionFilter }: RegKPIsProps) {
  // TODO: Replace with useAnalyticsQuery('reg_kpis', params) when live
  const kpis = USE_MOCK_DATA ? getMockKPIs() : getMockKPIs();

  const cards: { label: string; value: string | number; color: string; sub?: string }[] = [
    { label: 'Jurisdictions', value: kpis.jurisdictions_covered, color: LL_TEXT_PRIMARY, sub: 'States covered' },
    { label: 'Pending Filings', value: kpis.pending_filings, color: kpis.pending_filings > 0 ? LL_MEDIUM : LL_TEXT_PRIMARY, sub: 'Awaiting submission' },
    { label: 'Next Deadline', value: `${kpis.days_until_next_deadline}d`, color: kpis.days_until_next_deadline < 30 ? LL_HIGH : LL_TEXT_PRIMARY, sub: 'Until next filing' },
    { label: 'Compliance', value: `${kpis.compliance_pct}%`, color: kpis.compliance_pct < 80 ? LL_MEDIUM : LL_LOW, sub: 'Overall rate' },
    { label: 'Overdue', value: kpis.overdue_items, color: kpis.overdue_items > 0 ? LL_CRITICAL : LL_TEXT_PRIMARY, sub: 'Items past due' },
    { label: 'Documents', value: kpis.documents_indexed, color: LL_TEXT_PRIMARY, sub: 'Indexed for search' },
  ];

  return (
    <div className="grid grid-cols-6 gap-3">
      {cards.map((card) => (
        <div
          key={card.label}
          style={{
            background: '#FFFFFF',
            border: `1px solid ${LL_BORDER}`,
            borderRadius: 8,
            padding: 12,
          }}
        >
          <p
            role="status"
            aria-label={card.label}
            style={{
              fontSize: '0.75rem',
              color: LL_TEXT_SECONDARY,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              margin: 0,
            }}
          >
            {card.label}
          </p>
          <p
            style={{
              fontSize: '1.75rem',
              fontWeight: 700,
              color: card.color,
              margin: '4px 0 0',
              lineHeight: 1.2,
            }}
          >
            {card.value}
          </p>
          {card.sub && (
            <p
              style={{
                fontSize: '0.6875rem',
                color: LL_TEXT_SECONDARY,
                margin: '4px 0 0',
              }}
            >
              {card.sub}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
