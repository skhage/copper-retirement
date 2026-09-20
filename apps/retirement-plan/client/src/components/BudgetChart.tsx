/**
 * BudgetChart.tsx
 * Horizontal stacked bar chart showing budget allocation vs spent across waves.
 * Pure CSS approach — no external charting library.
 * Fetches live data from retirement_plan via /api/plan/budget.
 */
import { useState, useEffect, useMemo } from 'react';
import { fetchLiveBudget } from '../lib/planApi';
import { formatCurrency, formatCount, formatPercent } from '../lib/formatters';
import type { BudgetRow } from '../lib/planApi';

// Brand-aligned wave colors
const WAVE_COLORS = [
  '#FF3621', '#1B3139', '#00A972', '#6E8898',
  '#FF8C69', '#4A7C6F', '#C42D1A', '#2E4A55',
];

export function BudgetChart() {
  const [data, setData] = useState<BudgetRow[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchLiveBudget().then((rows) => {
      setData(rows);
      setIsLoading(false);
    });
  }, []);

  const rows = data || [];

  const maxAllocated = useMemo(
    () => Math.max(...rows.map((r) => Number(r.total_allocated) || 0), 1),
    [rows]
  );

  const totalAllocated = useMemo(
    () => rows.reduce((sum, r) => sum + (Number(r.total_allocated) || 0), 0),
    [rows]
  );
  const totalSpent = useMemo(
    () => rows.reduce((sum, r) => sum + (Number(r.total_spent) || 0), 0),
    [rows]
  );
  const totalRevAtRisk = useMemo(
    () => rows.reduce((sum, r) => sum + (Number(r.annual_revenue_at_risk) || 0), 0),
    [rows]
  );

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <h2 className="text-sm font-semibold">Budget Allocation by Wave</h2>
        {isLoading && (
          <span className="text-xs text-muted-foreground animate-pulse">Loading...</span>
        )}
        {!isLoading && data && (
          <span className="text-[10px] bg-[#00A972]/10 text-[#00A972] px-2 py-0.5 rounded font-medium">
            LIVE — {rows.length} waves
          </span>
        )}
        {!isLoading && !data && (
          <span className="text-[10px] bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
            NO DATA
          </span>
        )}
      </div>

      {/* Summary KPIs */}
      <div className="grid grid-cols-4 gap-3 mb-5">
        <div className="rounded border p-2">
          <p className="text-[10px] text-muted-foreground">Total Allocated</p>
          <p className="text-lg font-bold text-[#1B3139]">{formatCurrency(totalAllocated)}</p>
        </div>
        <div className="rounded border p-2">
          <p className="text-[10px] text-muted-foreground">Total Spent</p>
          <p className="text-lg font-bold text-[#FF3621]">{formatCurrency(totalSpent)}</p>
        </div>
        <div className="rounded border p-2">
          <p className="text-[10px] text-muted-foreground">Remaining</p>
          <p className="text-lg font-bold text-[#00A972]">{formatCurrency(totalAllocated - totalSpent)}</p>
        </div>
        <div className="rounded border p-2">
          <p className="text-[10px] text-muted-foreground">Revenue at Risk (Annual)</p>
          <p className="text-lg font-bold text-[#FF8C69]">{formatCurrency(totalRevAtRisk)}</p>
        </div>
      </div>

      {/* Horizontal bar chart */}
      <div className="space-y-3">
        {rows.map((row, idx) => {
          const allocated = Number(row.total_allocated) || 0;
          const spent = Number(row.total_spent) || 0;
          const remaining = allocated - spent;
          const pctOfMax = (allocated / maxAllocated) * 100;
          const spentPct = allocated > 0 ? (spent / allocated) * 100 : 0;
          const waveColor = WAVE_COLORS[idx % WAVE_COLORS.length];
          const completionPct = Number(row.avg_completion_pct) || 0;

          return (
            <div key={row.wave_label || `wave-${idx}`} className="group">
              {/* Row header */}
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-sm flex-shrink-0"
                    style={{ backgroundColor: waveColor }}
                  />
                  <span className="text-xs font-semibold">
                    {row.wave_label || `Wave ${row.retirement_wave}`}
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {row.wire_centers} WCs · {formatCount(Number(row.total_devices))} devices · {formatCount(Number(row.total_customers))} customers
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[10px]">
                  <span className="text-muted-foreground">
                    {formatPercent(completionPct)} complete
                  </span>
                  <span className="font-medium">
                    {formatCurrency(spent)} / {formatCurrency(allocated)}
                  </span>
                </div>
              </div>

              {/* Stacked bar */}
              <div
                className="relative h-6 rounded-sm bg-muted overflow-hidden"
                style={{ width: `${Math.max(pctOfMax, 8)}%` }}
              >
                {/* Spent portion */}
                <div
                  className="absolute top-0 left-0 h-full rounded-sm transition-all"
                  style={{
                    width: `${spentPct}%`,
                    backgroundColor: waveColor,
                    opacity: 0.9,
                  }}
                  title={`Spent: ${formatCurrency(spent)}`}
                />
                {/* Remaining portion (lighter) */}
                <div
                  className="absolute top-0 h-full rounded-sm transition-all"
                  style={{
                    left: `${spentPct}%`,
                    width: `${100 - spentPct}%`,
                    backgroundColor: waveColor,
                    opacity: 0.25,
                  }}
                  title={`Remaining: ${formatCurrency(remaining)}`}
                />
                {/* Label on bar */}
                {pctOfMax > 15 && (
                  <span className="absolute top-0 left-2 leading-6 text-[10px] font-medium text-white">
                    {formatCurrency(allocated)}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex gap-4 mt-4 pt-3 border-t">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-[#FF3621] opacity-90" />
          <span className="text-[10px] text-muted-foreground">Spent</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-[#FF3621] opacity-25" />
          <span className="text-[10px] text-muted-foreground">Remaining</span>
        </div>
      </div>

      {rows.length === 0 && !isLoading && (
        <p className="text-sm text-muted-foreground text-center py-8">
          No budget data available. Retirement plan table may not be populated.
        </p>
      )}
    </div>
  );
}
