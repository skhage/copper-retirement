/**
 * ImpactDetailPanel.tsx
 * Slide-out detail panel for a selected wire center.
 * Shows customer/revenue/network/cost breakdown + constraints.
 */
import { Card, CardContent } from '@databricks/appkit-ui/react';
import type { WireCenterImpact } from '../mock/retirementData';
import { PRIORITY_COLORS } from '../mock/retirementData';

interface Props {
  wireCenter: WireCenterImpact;
  onClose: () => void;
}

function ScoreBar({ label, score, max }: { label: string; score: number; max: number }) {
  const pct = Math.min(100, (score / max) * 100);
  const color = pct >= 75 ? '#EB1600' : pct >= 50 ? '#FF8C00' : pct >= 25 ? '#FFD700' : '#40d1f5';
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">{score}/{max}</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

export function ImpactDetailPanel({ wireCenter: wc, onClose }: Props) {
  return (
    <div className="w-96 bg-white border-l shadow-lg overflow-y-auto p-4">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <span
              className="inline-block w-3 h-3 rounded-full"
              style={{ backgroundColor: PRIORITY_COLORS[wc.priority_tier] }}
            />
            <h2 className="text-lg font-bold">{wc.wire_center_name}</h2>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {wc.wire_center_id} &middot; {wc.state} &middot;
            <span className="capitalize"> {wc.priority_tier.replace('-', ' ')}</span>
            &middot; Priority {wc.retirement_priority}/100
          </p>
        </div>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-lg px-1">&times;</button>
      </div>

      {/* Risk scores */}
      <div className="mb-4">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">Risk Scores</h3>
        <ScoreBar label="Churn Risk" score={wc.churn_risk_score} max={100} />
        <ScoreBar label="Network Disruption" score={wc.network_disruption_score} max={100} />
        <ScoreBar label="Retirement Priority" score={wc.retirement_priority} max={100} />
      </div>

      {/* Customer impact */}
      <Card className="mb-3">
        <CardContent className="p-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">Customer Impact</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div><span className="text-muted-foreground">Total Affected</span><br /><strong>{wc.customers_affected}</strong></div>
            <div><span className="text-muted-foreground">Business</span><br /><strong>{wc.business_customers}</strong></div>
            <div><span className="text-muted-foreground">Residential</span><br /><strong>{wc.residential_customers}</strong></div>
            <div><span className="text-muted-foreground">Contract-Locked</span><br /><strong className="text-red-600">{wc.customers_contract_locked}</strong></div>
          </div>
        </CardContent>
      </Card>

      {/* Revenue impact */}
      <Card className="mb-3">
        <CardContent className="p-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">Revenue at Risk</h3>
          <p className="text-2xl font-bold">${(wc.revenue_at_risk_mrr / 1000).toFixed(1)}K <span className="text-sm font-normal text-muted-foreground">MRR</span></p>
          <p className="text-xs text-muted-foreground mb-2">${(wc.revenue_at_risk_mrr * 12 / 1000).toFixed(0)}K annualized</p>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="text-center p-1 bg-gray-50 rounded"><span className="text-muted-foreground block">Voice</span><strong>${(wc.revenue_voice_mrr / 1000).toFixed(1)}K</strong></div>
            <div className="text-center p-1 bg-gray-50 rounded"><span className="text-muted-foreground block">Broadband</span><strong>${(wc.revenue_broadband_mrr / 1000).toFixed(1)}K</strong></div>
            <div className="text-center p-1 bg-gray-50 rounded"><span className="text-muted-foreground block">Fixed Line</span><strong>${(wc.revenue_fixed_line_mrr / 1000).toFixed(1)}K</strong></div>
          </div>
        </CardContent>
      </Card>

      {/* Network impact */}
      <Card className="mb-3">
        <CardContent className="p-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">Network Impact</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div><span className="text-muted-foreground">Copper Devices</span><br /><strong>{wc.copper_devices}</strong></div>
            <div><span className="text-muted-foreground">Services Affected</span><br /><strong>{wc.services_affected}</strong></div>
            <div><span className="text-muted-foreground">Active Alarms</span><br /><strong>{wc.active_alarms}</strong></div>
            <div><span className="text-muted-foreground">Fiber Ready</span><br /><strong className="text-green-600">{wc.fiber_ready_pct}%</strong></div>
          </div>
        </CardContent>
      </Card>

      {/* Cost/benefit */}
      <Card className="mb-3">
        <CardContent className="p-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">Cost &amp; Recovery</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div><span className="text-muted-foreground">Retirement Cost</span><br /><strong>${(wc.retirement_cost_usd / 1000).toFixed(0)}K</strong></div>
            <div><span className="text-muted-foreground">Scrap Recovery</span><br /><strong className="text-green-600">${(wc.scrap_recovery_usd / 1000).toFixed(0)}K</strong></div>
            <div><span className="text-muted-foreground">Net Cost</span><br /><strong>${(wc.net_cost_usd / 1000).toFixed(0)}K</strong></div>
            <div><span className="text-muted-foreground">Duration</span><br /><strong>{wc.estimated_duration_weeks} weeks</strong></div>
          </div>
        </CardContent>
      </Card>

      {/* Constraints */}
      <div className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Constraints</h3>
        {wc.regulatory_notice_required && (
          <div className="flex items-center gap-2 text-sm bg-amber-50 border border-amber-200 rounded p-2">
            <span className="text-amber-600">&#9888;</span>
            <span>{wc.notice_period_days}-day regulatory notice required</span>
          </div>
        )}
        {wc.customers_contract_locked > 0 && (
          <div className="flex items-center gap-2 text-sm bg-red-50 border border-red-200 rounded p-2">
            <span className="text-red-600">&#128274;</span>
            <span>{wc.customers_contract_locked} customers contract-locked</span>
          </div>
        )}
        {wc.has_active_dig_incident && (
          <div className="flex items-center gap-2 text-sm bg-red-50 border border-red-200 rounded p-2">
            <span className="text-red-600">&#9888;</span>
            <span>Active dig-safe incident in area</span>
          </div>
        )}
      </div>
    </div>
  );
}
