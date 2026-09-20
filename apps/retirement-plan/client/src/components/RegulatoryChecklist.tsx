/**
 * RegulatoryChecklist.tsx
 * Per-wire-center regulatory checklist with status tracking.
 * Fetches live data from /api/plan/regulatory (copper_app.regulatory_checklist_status).
 *
 * Grouped by wire center and category. Shows completion status per item.
 * Filterable by state.
 */
import { useState, useEffect, useMemo } from 'react';
import { fetchLiveRegulatory } from '../lib/planApi';
import { formatDate } from '../lib/formatters';
import { CheckCircle2, Circle, AlertTriangle, Clock, FileText } from 'lucide-react';
import type { RegulatoryItem } from '../lib/planApi';
import type { PlanFilters } from '../App';

interface Props {
  filters: PlanFilters;
}

const STATUS_CONFIG: Record<string, { icon: typeof CheckCircle2; color: string; label: string }> = {
  completed: { icon: CheckCircle2, color: 'text-[#00A972]', label: 'Completed' },
  in_progress: { icon: Clock, color: 'text-amber-500', label: 'In Progress' },
  pending: { icon: Circle, color: 'text-muted-foreground', label: 'Pending' },
  overdue: { icon: AlertTriangle, color: 'text-[#FF3621]', label: 'Overdue' },
  not_applicable: { icon: Circle, color: 'text-muted-foreground/50', label: 'N/A' },
};

const CATEGORY_COLORS: Record<string, string> = {
  puc_filing: 'bg-amber-100 text-amber-700',
  customer_notice: 'bg-blue-100 text-blue-700',
  e911_coordination: 'bg-red-100 text-red-700',
  backup_power: 'bg-purple-100 text-purple-700',
  section_214: 'bg-orange-100 text-orange-700',
  public_notice: 'bg-green-100 text-green-700',
  tribal_notice: 'bg-indigo-100 text-indigo-700',
  environmental: 'bg-teal-100 text-teal-700',
};

interface WireCenterGroup {
  wireCenter: string;
  wireCenterName: string;
  state: string;
  items: RegulatoryItem[];
  completedCount: number;
  totalRequired: number;
}

export function RegulatoryChecklist({ filters }: Props) {
  const [data, setData] = useState<RegulatoryItem[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedWC, setExpandedWC] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchLiveRegulatory().then((rows) => {
      setData(rows);
      setIsLoading(false);
    });
  }, []);

  const groups = useMemo(() => {
    if (!data) return [];
    const filtered = data.filter((item) => {
      if (filters.state !== 'all' && item.state_code !== filters.state) return false;
      return true;
    });
    const map = new Map<string, WireCenterGroup>();
    for (const item of filtered) {
      const key = item.wire_center_id;
      if (!map.has(key)) {
        map.set(key, {
          wireCenter: item.wire_center_id,
          wireCenterName: item.wire_center_name,
          state: item.state_code,
          items: [],
          completedCount: 0,
          totalRequired: 0,
        });
      }
      const g = map.get(key)!;
      g.items.push(item);
      if (item.required === 'true' || item.required === true as any) {
        g.totalRequired++;
        if (item.status === 'completed') g.completedCount++;
      }
    }
    return Array.from(map.values()).sort((a, b) => {
      const aRatio = a.totalRequired > 0 ? a.completedCount / a.totalRequired : 1;
      const bRatio = b.totalRequired > 0 ? b.completedCount / b.totalRequired : 1;
      return aRatio - bRatio; // Least complete first
    });
  }, [data, filters]);

  const toggleWC = (id: string) => {
    setExpandedWC((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  // Summary stats
  const totalItems = groups.reduce((s, g) => s + g.items.length, 0);
  const totalCompleted = groups.reduce((s, g) => s + g.completedCount, 0);
  const totalRequired = groups.reduce((s, g) => s + g.totalRequired, 0);

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <FileText size={16} strokeWidth={1.5} className="text-[#FF3621]" />
        <h2 className="text-sm font-semibold">Regulatory Compliance Checklist</h2>
        {isLoading && (
          <span className="text-xs text-muted-foreground animate-pulse">Loading...</span>
        )}
        {!isLoading && data && (
          <span className="text-[10px] bg-[#00A972]/10 text-[#00A972] px-2 py-0.5 rounded font-medium">
            LIVE — {totalItems} items across {groups.length} wire centers
          </span>
        )}
      </div>

      {/* Summary bar */}
      <div className="grid grid-cols-4 gap-3 mb-4">
        <div className="rounded border p-2">
          <p className="text-[10px] text-muted-foreground">Wire Centers</p>
          <p className="text-lg font-bold text-[#1B3139]">{groups.length}</p>
        </div>
        <div className="rounded border p-2">
          <p className="text-[10px] text-muted-foreground">Required Items</p>
          <p className="text-lg font-bold text-[#FF3621]">{totalRequired}</p>
        </div>
        <div className="rounded border p-2">
          <p className="text-[10px] text-muted-foreground">Completed</p>
          <p className="text-lg font-bold text-[#00A972]">{totalCompleted}</p>
        </div>
        <div className="rounded border p-2">
          <p className="text-[10px] text-muted-foreground">Compliance Rate</p>
          <p className="text-lg font-bold text-[#6E8898]">
            {totalRequired > 0 ? `${((totalCompleted / totalRequired) * 100).toFixed(0)}%` : '—'}
          </p>
        </div>
      </div>

      {/* Wire center accordion */}
      <div className="space-y-2">
        {groups.map((g) => {
          const isExpanded = expandedWC.has(g.wireCenter);
          const pct = g.totalRequired > 0 ? (g.completedCount / g.totalRequired) * 100 : 100;
          const pctColor =
            pct >= 100 ? 'bg-[#00A972]' : pct >= 50 ? 'bg-amber-500' : 'bg-[#FF3621]';

          return (
            <div key={g.wireCenter} className="rounded border overflow-hidden">
              {/* Accordion header */}
              <button
                onClick={() => toggleWC(g.wireCenter)}
                className="w-full flex items-center justify-between px-3 py-2 hover:bg-muted/30 transition-colors focus-visible:ring-2 focus-visible:ring-[#FF3621] focus-visible:outline-none"
                aria-expanded={isExpanded}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold">{g.wireCenterName}</span>
                  <span className="text-[10px] bg-muted text-muted-foreground px-1.5 py-0.5 rounded">
                    {g.state}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1">
                    <div className="w-20 h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${pctColor}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-muted-foreground">
                      {g.completedCount}/{g.totalRequired}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {isExpanded ? '\u25B2' : '\u25BC'}
                  </span>
                </div>
              </button>

              {/* Checklist items */}
              {isExpanded && (
                <div className="border-t divide-y">
                  {g.items.map((item) => {
                    const cfg = STATUS_CONFIG[item.status] || STATUS_CONFIG.pending;
                    const Icon = cfg.icon;
                    const catClass = CATEGORY_COLORS[item.item_category] || 'bg-muted text-muted-foreground';

                    return (
                      <div
                        key={item.checklist_id}
                        className="flex items-start gap-2 px-3 py-2 text-xs"
                      >
                        <Icon size={14} strokeWidth={1.5} className={`${cfg.color} mt-0.5 flex-shrink-0`} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{item.checklist_item}</span>
                            <span className={`text-[9px] px-1 py-0 rounded ${catClass}`}>
                              {(item.item_category || '').replace(/_/g, ' ')}
                            </span>
                            {(item.required === 'true' || item.required === true as any) && (
                              <span className="text-[9px] bg-red-100 text-red-600 px-1 rounded">Required</span>
                            )}
                          </div>
                          {item.description && (
                            <p className="text-muted-foreground mt-0.5 truncate">{item.description}</p>
                          )}
                          <div className="flex gap-3 mt-0.5 text-muted-foreground">
                            {item.deadline_date && (
                              <span>Due: {formatDate(item.deadline_date)}</span>
                            )}
                            {item.assigned_to && (
                              <span>Assigned: {item.assigned_to}</span>
                            )}
                            {item.completed_date && (
                              <span className="text-[#00A972]">Completed: {formatDate(item.completed_date)}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {groups.length === 0 && !isLoading && (
        <p className="text-sm text-muted-foreground text-center py-8">
          No regulatory checklist data available for the selected filters.
        </p>
      )}
    </div>
  );
}
