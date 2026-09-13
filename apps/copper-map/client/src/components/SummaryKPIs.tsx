/**
 * SummaryKPIs.tsx
 * Converged KPI bar: Copper Devices, Critical Risk %, Revenue at Risk,
 * States, Services Affected.
 *
 * Follows BRAND_GUIDE §6 KPI Card spec:
 *   - Background: --ll-surface-elevated (#FFFFFF)
 *   - Label: uppercase, tracking-wide, --ll-text-secondary (#6E8898), 12px
 *   - Value: --ll-text-primary (#1B3139) or semantic color, 28px bold
 *   - Subtitle: --ll-text-secondary, 11px
 *   - Border: 1px #E5E2DD, radius 8px, no shadows
 *
 * Shared between AppKit (client/) and Dash (app.py) — both must show
 * the same 5 metrics in the same order.
 */
import { Card, CardContent, Skeleton } from '@databricks/appkit-ui/react';
import { USE_MOCK_DATA, getConvergedKPIs } from '../mock/retirementData';
import type { ConvergedKPIs } from '../mock/retirementData';

/* Lakelink Fiber brand tokens */
const LL_CRITICAL = '#FF3621';
const LL_TEXT_PRIMARY = '#1B3139';

interface KPICard {
  label: string;
  value: string;
  sub: string;
  color: string;
}

function buildCards(k: ConvergedKPIs): KPICard[] {
  return [
    {
      label: 'Copper Devices',
      value: k.copper_devices.toLocaleString(),
      sub: 'Across all wire centers',
      color: LL_TEXT_PRIMARY,
    },
    {
      label: 'Critical Risk',
      value: `${k.critical_risk_pct}%`,
      sub: 'Wire centers retire-now',
      color: k.critical_risk_pct >= 40 ? LL_CRITICAL : LL_TEXT_PRIMARY,
    },
    {
      label: 'Revenue at Risk',
      value: `$${(k.revenue_at_risk_mrr / 1000).toFixed(0)}K`,
      sub: `$${(k.revenue_at_risk_mrr * 12 / 1_000_000).toFixed(1)}M annualized`,
      color: LL_CRITICAL,
    },
    {
      label: 'States',
      value: String(k.states_count),
      sub: 'With copper plant',
      color: LL_TEXT_PRIMARY,
    },
    {
      label: 'Services Affected',
      value: k.services_affected.toLocaleString(),
      sub: 'Copper-dependent',
      color: LL_TEXT_PRIMARY,
    },
  ];
}

export function SummaryKPIs() {
  const kpis = USE_MOCK_DATA ? getConvergedKPIs() : getConvergedKPIs(); // TODO: live query

  if (!kpis) {
    return (
      <div className="grid grid-cols-5 gap-3 mb-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-3">
              <Skeleton className="h-4 w-3/4 mb-2" />
              <Skeleton className="h-8 w-1/2" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const cards = buildCards(kpis);

  return (
    <div className="grid grid-cols-5 gap-3 mb-4">
      {cards.map((c) => (
        <Card key={c.label} style={{ border: '1px solid #E5E2DD', borderRadius: 8 }}>
          <CardContent className="p-3">
            <p
              role="status"
              aria-label={c.label}
              style={{
                fontSize: '0.75rem',
                color: '#6E8898',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                margin: 0,
              }}
            >
              {c.label}
            </p>
            <p
              style={{
                fontSize: '1.75rem',
                fontWeight: 700,
                color: c.color,
                margin: '4px 0 0',
                lineHeight: 1.2,
              }}
            >
              {c.value}
            </p>
            <p
              style={{
                fontSize: '0.6875rem',
                color: '#6E8898',
                margin: '4px 0 0',
              }}
            >
              {c.sub}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
