/**
 * WaveSelector.tsx
 * Filter bar with wave, state, status, and constraint dropdowns.
 * Persists across Gantt/Table/Scenario tabs.
 */
import type { PlanFilters } from '../App';

interface Props {
  filters: PlanFilters;
  onFilterChange: (filters: PlanFilters) => void;
}

const STATES = ['all', 'CO', 'MN', 'WA', 'OR', 'AZ', 'ID'];
const WAVES = ['all', '1', '2', '3', '4', '5', '6', '7', '8'];
const STATUSES = ['all', 'planned', 'in_progress', 'fiber_provisioned', 'cutover', 'completed', 'on_hold', 'deferred'];
const CONSTRAINTS = ['all', 'none', 'contract_locked', 'regulatory_notice_pending', 'crew_capacity_constrained', 'revrec_locked'];

function labelFor(val: string): string {
  if (val === 'all') return 'All';
  return val.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function WaveSelector({ filters, onFilterChange }: Props) {
  const update = (key: keyof PlanFilters, value: string) => {
    onFilterChange({ ...filters, [key]: value });
  };

  return (
    <div className="flex gap-3 mb-3 items-center">
      <span className="text-xs font-medium text-muted-foreground">Filters:</span>

      {/* Wave */}
      <select
        value={filters.wave}
        onChange={(e) => update('wave', e.target.value)}
        className="text-xs border rounded px-2 py-1 bg-background"
      >
        {WAVES.map((w) => (
          <option key={w} value={w}>
            {w === 'all' ? 'All Waves' : `Wave ${w}`}
          </option>
        ))}
      </select>

      {/* State */}
      <select
        value={filters.state}
        onChange={(e) => update('state', e.target.value)}
        className="text-xs border rounded px-2 py-1 bg-background"
      >
        {STATES.map((s) => (
          <option key={s} value={s}>
            {s === 'all' ? 'All States' : s}
          </option>
        ))}
      </select>

      {/* Status */}
      <select
        value={filters.status}
        onChange={(e) => update('status', e.target.value)}
        className="text-xs border rounded px-2 py-1 bg-background"
      >
        {STATUSES.map((s) => (
          <option key={s} value={s}>
            {labelFor(s)}
          </option>
        ))}
      </select>

      {/* Constraint */}
      <select
        value={filters.constraint}
        onChange={(e) => update('constraint', e.target.value)}
        className="text-xs border rounded px-2 py-1 bg-background"
      >
        {CONSTRAINTS.map((c) => (
          <option key={c} value={c}>
            {c === 'all' ? 'All Constraints' : labelFor(c)}
          </option>
        ))}
      </select>
    </div>
  );
}
