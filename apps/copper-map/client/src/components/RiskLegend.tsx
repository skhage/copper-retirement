/**
 * RiskLegend.tsx
 * Color ramp legend mapping risk tiers to hex fill colors.
 * Displayed as a compact bar below the map.
 */
import { RISK_COLORS, RISK_TIERS } from '../mock/mockData';

const TIER_LABELS: Record<string, string> = {
  critical: 'Critical (≥75)',
  high: 'High (50–74)',
  medium: 'Medium (25–49)',
  low: 'Low (<25)',
};

export function RiskLegend() {
  return (
    <div className="flex items-center gap-4 px-4 py-2 bg-card rounded-md border text-xs">
      <span className="font-semibold text-muted-foreground">Risk Score:</span>
      {RISK_TIERS.map((tier) => (
        <div key={tier} className="flex items-center gap-1">
          <div
            className="w-3 h-3 rounded-sm"
            style={{ backgroundColor: RISK_COLORS[tier] }}
          />
          <span>{TIER_LABELS[tier]}</span>
        </div>
      ))}
    </div>
  );
}
