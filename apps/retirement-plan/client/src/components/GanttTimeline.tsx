/**
 * GanttTimeline.tsx
 * Horizontal Gantt chart: wire centers on Y-axis, 2026–2029 quarters on X-axis.
 * Color by wave. Constraint flags on bars. Click to select wire center.
 *
 * Rendering approach: Pure CSS/SVG Gantt (no external charting library).
 * Each bar is positioned via calculated left/width percentages
 * relative to the full 2026-Q1 → 2029-Q4 timeline.
 *
 * TODO: Add drag-to-reschedule once Lakebase write-back (P5-SCHEMA) lands.
 */
import { useMemo } from 'react';
import { mockWireCenters, USE_MOCK_DATA } from '../mock/mockData';
import { ConstraintFlags } from './ConstraintFlags';
import type { WireCenterPlan } from '../mock/mockData';
import type { PlanFilters } from '../App';

interface Props {
  filters: PlanFilters;
  onWireCenterSelect: (wc: WireCenterPlan | null) => void;
  selectedWireCenter: WireCenterPlan | null;
}

// Timeline range: 2026-01-01 to 2029-12-31 (4 years)
const TIMELINE_START = new Date('2026-01-01').getTime();
const TIMELINE_END = new Date('2030-01-01').getTime();
const TIMELINE_SPAN = TIMELINE_END - TIMELINE_START;

// Quarter labels
const QUARTERS = [
  '2026 Q1', '2026 Q2', '2026 Q3', '2026 Q4',
  '2027 Q1', '2027 Q2', '2027 Q3', '2027 Q4',
  '2028 Q1', '2028 Q2', '2028 Q3', '2028 Q4',
  '2029 Q1', '2029 Q2', '2029 Q3', '2029 Q4',
];

// Wave color palette
const WAVE_COLORS: Record<number, string> = {
  1: 'bg-[#FF3621]',
  2: 'bg-[#1B3139]',
  3: 'bg-[#00A972]',
  4: 'bg-[#6E8898]',
  5: 'bg-[#FF8C69]',
  6: 'bg-[#4A7C6F]',
  7: 'bg-[#C42D1A]',
  8: 'bg-[#2E4A55]',
};

const STATUS_OPACITY: Record<string, string> = {
  completed: 'opacity-100',
  in_progress: 'opacity-90',
  fiber_provisioned: 'opacity-80',
  cutover: 'opacity-80',
  planned: 'opacity-60',
  on_hold: 'opacity-40',
  deferred: 'opacity-30',
};

function toPercent(dateStr: string): number {
  const t = new Date(dateStr).getTime();
  return ((t - TIMELINE_START) / TIMELINE_SPAN) * 100;
}

export function GanttTimeline({ filters, onWireCenterSelect, selectedWireCenter }: Props) {
  const data = USE_MOCK_DATA ? mockWireCenters : mockWireCenters;

  const filtered = useMemo(() => {
    return data.filter((wc) => {
      if (filters.wave !== 'all' && String(wc.wave) !== filters.wave) return false;
      if (filters.state !== 'all' && wc.state !== filters.state) return false;
      if (filters.status !== 'all' && wc.status !== filters.status) return false;
      if (filters.constraint !== 'all' && wc.constraint !== filters.constraint) return false;
      return true;
    });
  }, [data, filters]);

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <h2 className="text-sm font-semibold mb-3">Retirement Wave Timeline (2026–2029)</h2>

      {/* Quarter header */}
      <div className="flex mb-1 border-b pb-1">
        <div className="w-48 flex-shrink-0 text-xs text-muted-foreground">Wire Center</div>
        <div className="flex-1 flex">
          {QUARTERS.map((q) => (
            <div key={q} className="flex-1 text-center text-[10px] text-muted-foreground">
              {q}
            </div>
          ))}
        </div>
      </div>

      {/* Gantt rows */}
      <div className="space-y-1">
        {filtered.map((wc) => {
          const left = toPercent(wc.scheduled_start);
          const right = toPercent(wc.scheduled_end);
          const width = right - left;
          const isSelected = selectedWireCenter?.wire_center_id === wc.wire_center_id;

          return (
            <div
              key={wc.wire_center_id}
              role="button"
              tabIndex={0}
              aria-label={`Wire center ${wc.wire_center_name}, Wave ${wc.wave}, ${wc.status.replace(/_/g, ' ')}`}
              className={`flex items-center h-8 cursor-pointer rounded transition-colors focus-visible:ring-2 focus-visible:ring-[#FF3621] focus-visible:outline-none ${
                isSelected ? 'bg-primary/5 ring-1 ring-primary/30' : 'hover:bg-muted/50'
              }`}
              onClick={() => onWireCenterSelect(isSelected ? null : wc)}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onWireCenterSelect(isSelected ? null : wc); } }}
            >
              {/* Label */}
              <div className="w-48 flex-shrink-0 flex items-center gap-1 px-1">
                <span className="text-xs font-medium truncate">
                  {wc.wire_center_name}
                </span>
                <ConstraintFlags constraint={wc.constraint} size="sm" />
              </div>

              {/* Bar area */}
              <div className="flex-1 relative h-6">
                {/* Quarter grid lines */}
                {QUARTERS.map((_, i) => (
                  <div
                    key={i}
                    className="absolute top-0 bottom-0 border-l border-dashed border-muted"
                    style={{ left: `${(i / 16) * 100}%` }}
                  />
                ))}

                {/* Gantt bar */}
                <div
                  className={`absolute top-1 h-4 rounded-sm ${
                    WAVE_COLORS[wc.wave] || 'bg-gray-400'
                  } ${STATUS_OPACITY[wc.status] || 'opacity-60'} transition-all`}
                  style={{ left: `${left}%`, width: `${Math.max(width, 0.5)}%` }}
                  title={`${wc.wire_center_name} | Wave ${wc.wave} | ${wc.status} | ${wc.scheduled_start} → ${wc.scheduled_end}`}
                >
                  {/* Completion fill */}
                  {wc.completion_pct > 0 && (
                    <div
                      className="absolute top-0 left-0 h-full bg-white/30 rounded-sm"
                      style={{ width: `${wc.completion_pct}%` }}
                    />
                  )}
                  {/* Wave label on bar */}
                  {width > 3 && (
                    <span className="text-[9px] text-white font-medium px-1 leading-4 truncate block">
                      W{wc.wave}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Wave legend */}
      <div className="flex gap-3 mt-3 pt-2 border-t">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((w) => (
          <div key={w} className="flex items-center gap-1">
            <div className={`w-3 h-3 rounded-sm ${WAVE_COLORS[w]}`} />
            <span className="text-[10px] text-muted-foreground">Wave {w}</span>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-8">
          No wire centers match the current filters.
        </p>
      )}
    </div>
  );
}
