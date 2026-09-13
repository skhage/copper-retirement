/**
 * MigrationTable.tsx
 * Tabular view of migration plan: wire center, wave, dates, status,
 * customers, cost, constraint. Sortable and filterable.
 */
import { useMemo, useState } from 'react';
import { mockWireCenters, USE_MOCK_DATA } from '../mock/mockData';
import { ConstraintFlags } from './ConstraintFlags';
import { formatCurrency, formatCount, formatPercent } from '../lib/formatters';
import type { WireCenterPlan } from '../mock/mockData';
import type { PlanFilters } from '../App';

interface Props {
  filters: PlanFilters;
  onFilterChange: (filters: PlanFilters) => void;
  onWireCenterSelect: (wc: WireCenterPlan) => void;
}

type SortKey = 'wave' | 'wire_center_name' | 'state' | 'customers_affected' |
  'migration_cost_usd' | 'scheduled_start' | 'priority_score' | 'completion_pct';

export function MigrationTable({ filters, onFilterChange, onWireCenterSelect }: Props) {
  const data = USE_MOCK_DATA ? mockWireCenters : mockWireCenters;
  const [sortKey, setSortKey] = useState<SortKey>('wave');
  const [sortAsc, setSortAsc] = useState(true);

  const filtered = useMemo(() => {
    let rows = data.filter((wc) => {
      if (filters.wave !== 'all' && String(wc.wave) !== filters.wave) return false;
      if (filters.state !== 'all' && wc.state !== filters.state) return false;
      if (filters.status !== 'all' && wc.status !== filters.status) return false;
      if (filters.constraint !== 'all' && wc.constraint !== filters.constraint) return false;
      return true;
    });
    rows = [...rows].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === 'number' && typeof bv === 'number') return sortAsc ? av - bv : bv - av;
      return sortAsc ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
    });
    return rows;
  }, [data, filters, sortKey, sortAsc]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(true); }
  };

  const sortIcon = (key: SortKey) =>
    sortKey === key ? (sortAsc ? ' \u25B2' : ' \u25BC') : '';

  return (
    <div className="rounded-lg border bg-card shadow-sm overflow-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b bg-muted/30">
            {[
              { key: 'wave' as SortKey, label: 'Wave' },
              { key: 'wire_center_name' as SortKey, label: 'Wire Center' },
              { key: 'state' as SortKey, label: 'State' },
              { key: 'scheduled_start' as SortKey, label: 'Start' },
              { key: 'customers_affected' as SortKey, label: 'Customers' },
              { key: 'migration_cost_usd' as SortKey, label: 'Cost' },
              { key: 'priority_score' as SortKey, label: 'Priority' },
              { key: 'completion_pct' as SortKey, label: 'Progress' },
            ].map(({ key, label }) => (
              <th
                key={key}
                onClick={() => handleSort(key)}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleSort(key); } }}
                tabIndex={0}
                role="columnheader"
                aria-sort={sortKey === key ? (sortAsc ? 'ascending' : 'descending') : 'none'}
                className="px-3 py-2 text-left font-medium cursor-pointer hover:text-primary focus-visible:ring-2 focus-visible:ring-[#FF3621] focus-visible:outline-none"
              >
                {label}{sortIcon(key)}
              </th>
            ))}
            <th className="px-3 py-2 text-left font-medium">Status</th>
            <th className="px-3 py-2 text-left font-medium">Constraint</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((wc) => (
            <tr
              key={wc.wire_center_id}
              onClick={() => onWireCenterSelect(wc)}
              className="border-b hover:bg-muted/30 cursor-pointer transition-colors"
            >
              <td className="px-3 py-2 font-medium">W{wc.wave}</td>
              <td className="px-3 py-2 font-medium">{wc.wire_center_name}</td>
              <td className="px-3 py-2">{wc.state}</td>
              <td className="px-3 py-2 text-muted-foreground">{wc.scheduled_start}</td>
              <td className="px-3 py-2 text-right">{formatCount(wc.customers_affected)}</td>
              <td className="px-3 py-2 text-right">{formatCurrency(wc.migration_cost_usd)}</td>
              <td className="px-3 py-2 text-right">{wc.priority_score}</td>
              <td className="px-3 py-2">
                <div className="flex items-center gap-1">
                  <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full"
                      style={{ width: `${wc.completion_pct}%` }}
                    />
                  </div>
                  <span>{formatPercent(wc.completion_pct)}</span>
                </div>
              </td>
              <td className="px-3 py-2">
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                  wc.status === 'in_progress' ? 'bg-amber-100 text-amber-700' :
                  wc.status === 'completed' ? 'bg-green-100 text-green-700' :
                  wc.status === 'on_hold' ? 'bg-red-100 text-red-700' :
                  'bg-muted text-muted-foreground'
                }`}>
                  {wc.status.replace(/_/g, ' ')}
                </span>
              </td>
              <td className="px-3 py-2">
                <ConstraintFlags constraint={wc.constraint} size="md" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {filtered.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-8">
          No wire centers match the current filters.
        </p>
      )}
    </div>
  );
}
