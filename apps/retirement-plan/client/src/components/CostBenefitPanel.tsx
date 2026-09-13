/**
 * CostBenefitPanel.tsx
 * Per-wire-center cost/benefit breakdown panel.
 * Shows: migration cost, revenue at risk, scrap recovery value,
 * net savings, constraint details, milestones.
 */
import { mockMilestones } from '../mock/mockData';
import { formatCurrency, formatCount, formatPercent } from '../lib/formatters';
import { X } from 'lucide-react';
import { ConstraintFlags } from './ConstraintFlags';
import type { WireCenterPlan } from '../mock/mockData';

interface Props {
  wireCenter: WireCenterPlan;
  onClose: () => void;
}

export function CostBenefitPanel({ wireCenter, onClose }: Props) {
  const wc = wireCenter;
  const milestones = mockMilestones.filter(
    (m) => m.wire_center_id === wc.wire_center_id
  );

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold">{wc.wire_center_name}</h3>
          <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">
            Wave {wc.wave}
          </span>
          <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded">
            {wc.state}
          </span>
          <ConstraintFlags constraint={wc.constraint} size="md" />
        </div>
        <button
          onClick={onClose}
          aria-label="Close detail panel"
          className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 focus-visible:ring-2 focus-visible:ring-[#FF3621] focus-visible:outline-none rounded"
        >
          <X size={14} strokeWidth={1.5} /> Close
        </button>
      </div>

      {/* 4-column cost/benefit grid */}
      <div className="grid grid-cols-4 gap-4 mb-4">
        <div className="rounded border p-3">
          <p className="text-xs text-muted-foreground">Migration Cost</p>
          <p className="text-lg font-bold text-red-600">
            {formatCurrency(wc.migration_cost_usd)}
          </p>
        </div>
        <div className="rounded border p-3">
          <p className="text-xs text-muted-foreground">Revenue at Risk (MRR)</p>
          <p className="text-lg font-bold text-amber-600">
            {formatCurrency(wc.revenue_at_risk_mrr)}
          </p>
        </div>
        <div className="rounded border p-3">
          <p className="text-xs text-muted-foreground">Scrap Recovery</p>
          <p className="text-lg font-bold text-green-600">
            {formatCurrency(wc.scrap_recovery_usd)}
          </p>
        </div>
        <div className="rounded border p-3">
          <p className="text-xs text-muted-foreground">Net Annual Savings</p>
          <p className="text-lg font-bold text-accent">
            {formatCurrency(wc.net_savings_usd)}
          </p>
        </div>
      </div>

      {/* Details row */}
      <div className="grid grid-cols-5 gap-3 mb-4 text-xs">
        <div>
          <span className="text-muted-foreground">Customers:</span>{' '}
          <span className="font-medium">{formatCount(wc.customers_affected)}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Devices:</span>{' '}
          <span className="font-medium">{formatCount(wc.copper_devices)}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Completion:</span>{' '}
          <span className="font-medium">{formatPercent(wc.completion_pct)}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Crew:</span>{' '}
          <span className="font-medium">{wc.assigned_crew}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Priority:</span>{' '}
          <span className="font-medium">{wc.priority_score}/100</span>
        </div>
      </div>

      {/* Constraint detail */}
      {wc.constraint !== 'none' && wc.constraint_detail && (
        <div className="rounded bg-amber-50 border border-amber-200 p-2 mb-4 text-xs text-amber-800">
          <strong>Constraint:</strong> {wc.constraint_detail}
        </div>
      )}

      {/* Milestones */}
      {milestones.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold mb-2">Milestones</h4>
          <div className="space-y-1">
            {milestones.map((m) => (
              <div
                key={m.milestone_id}
                className="flex items-center gap-2 text-xs"
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    m.status === 'achieved'
                      ? 'bg-green-500'
                      : m.status === 'in_progress'
                      ? 'bg-amber-500'
                      : m.status === 'at_risk'
                      ? 'bg-red-500'
                      : 'bg-muted'
                  }`}
                />
                <span className="font-medium">{m.name}</span>
                <span className="text-muted-foreground">
                  {m.actual_date || m.planned_date}
                </span>
                {m.critical_path && (
                  <span className="text-[9px] bg-red-100 text-red-700 px-1 rounded">
                    CP
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
