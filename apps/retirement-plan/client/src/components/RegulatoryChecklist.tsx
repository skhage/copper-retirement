/**
 * RegulatoryChecklist.tsx
 * Per-wire-center regulatory checklist with status tracking.
 * Fetches live data from /api/plan/regulatory: every cited federal + state requirement
 * (UC jurisdiction_requirements_cited) per wire center, each with citation + official URL.
 * Non-VERIFIED rows are shown as flagged gaps, never as fact (charter citation rule).
 *
 * Grouped by wire center and category. Shows completion status per item.
 * Filterable by state.
 */
import { useState, useEffect, useMemo } from 'react';
import { fetchLiveRegulatory, errorState } from '../lib/planApi';
import type { LoadState } from '../lib/planApi';
import { formatDate } from '../lib/formatters';
import { CheckCircle2, Circle, AlertTriangle, Clock, FileText } from 'lucide-react';
import type { RegulatoryItem } from '../lib/planApi';
import { CitationLink, EmptyState, isVerifiedStatus } from './shared';
import type { PlanFilters } from '../App';

interface Props {
  filters: PlanFilters;
}

const STATUS_CONFIG: Record<string, { icon: typeof CheckCircle2; color: string; label: string }> = {
  completed: { icon: CheckCircle2, color: 'text-accent-strong', label: 'Completed' },
  in_progress: { icon: Clock, color: 'text-warning', label: 'In Progress' },
  pending: { icon: Circle, color: 'text-muted-foreground', label: 'Pending' },
  overdue: { icon: AlertTriangle, color: 'text-danger', label: 'Overdue' },
  not_applicable: { icon: Circle, color: 'text-muted-foreground', label: 'N/A' },
};

const CATEGORY_COLORS: Record<string, string> = {
  puc_filing: 'bg-warning/10 text-warning',
  customer_notice: 'bg-muted text-foreground',
  e911_coordination: 'bg-danger/10 text-danger',
  backup_power: 'bg-muted text-foreground',
  section_214: 'bg-warning/10 text-warning',
  public_notice: 'bg-success/10 text-success',
  tribal_notice: 'bg-muted text-foreground',
  environmental: 'bg-success/10 text-success',
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
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const isLoading = loadState === 'loading';
  const [expandedWC, setExpandedWC] = useState<Set<string>>(new Set());

  // ACC-DES-DEF-PLAN-CHECKLIST-A11Y (4): a failed load is never shown as 'no data' (empty result != absence).
  useEffect(() => {
    fetchLiveRegulatory()
      .then((rows) => { setData(rows); setLoadState('live'); })
      .catch((err) => { console.warn('[RegulatoryChecklist] Live fetch failed:', err); setData(null); setLoadState(errorState(err)); });
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
        <FileText size={16} strokeWidth={1.5} className="text-primary" aria-hidden="true" />
        <h2 className="text-sm font-semibold">Regulatory Compliance Checklist</h2>
        {isLoading && (
          <span className="text-xs text-muted-foreground animate-pulse">Loading...</span>
        )}
        {!isLoading && data && (
          <span className="text-xs bg-accent/10 text-accent-strong px-2 py-0.5 rounded font-medium">
            LIVE — {totalItems} items across {groups.length} wire centers
          </span>
        )}
      </div>

      {/* Summary bar */}
      {loadState === 'denied' && (
        <EmptyState title="Data access pending">
          <p>The app service principal lacks SELECT on jurisdiction_requirements_cited. The checklist will load once grants are applied.</p>
        </EmptyState>
      )}
      {loadState === 'error' && (
        <EmptyState title="Could not load the regulatory checklist">
          <p>The data service did not respond. This is a load failure, not an absence of requirements.</p>
        </EmptyState>
      )}

      {loadState === 'live' && (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div className="rounded border p-2">
          <p className="text-xs text-muted-foreground">Wire Centers</p>
          <p className="text-lg font-bold text-secondary">{groups.length}</p>
        </div>
        <div className="rounded border p-2">
          <p className="text-xs text-muted-foreground">Required Items</p>
          <p className="text-lg font-bold text-primary-strong">{totalRequired}</p>
        </div>
        <div className="rounded border p-2">
          <p className="text-xs text-muted-foreground">Completed</p>
          <p className="text-lg font-bold text-accent-strong">{totalCompleted}</p>
        </div>
        <div className="rounded border p-2">
          <p className="text-xs text-muted-foreground">Compliance Rate</p>
          <p className="text-lg font-bold text-muted-foreground">
            {totalRequired > 0 ? `${((totalCompleted / totalRequired) * 100).toFixed(0)}%` : '—'}
          </p>
        </div>
      </div>
      )}

      {/* Wire center accordion */}
      <div className="space-y-2">
        {groups.map((g) => {
          const isExpanded = expandedWC.has(g.wireCenter);
          const pct = g.totalRequired > 0 ? (g.completedCount / g.totalRequired) * 100 : 100;
          const pctColor =
            pct >= 100 ? 'bg-viz-3' : pct >= 50 ? 'bg-viz-5' : 'bg-viz-1';

          return (
            <div key={g.wireCenter} className="rounded border overflow-hidden">
              {/* Accordion header */}
              <button
                onClick={() => toggleWC(g.wireCenter)}
                className="w-full flex items-center justify-between px-3 py-2 hover:bg-muted/30 transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                aria-expanded={isExpanded}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold">{g.wireCenterName}</span>
                  <span className="text-xs bg-muted text-muted-foreground px-1.5 py-0.5 rounded">
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
                    <span className="text-xs text-muted-foreground">
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
                        <Icon size={14} strokeWidth={1.5} className={`${cfg.color} mt-0.5 flex-shrink-0`} aria-hidden="true" />
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className={`font-medium ${cfg.color}`}>{cfg.label}</span>
                            <span className="font-medium">{item.checklist_item}</span>
                            <span className={`text-xs px-1 py-0 rounded ${catClass}`}>
                              {(item.item_category || '').replace(/_/g, ' ')}
                            </span>
                            {(item.required === 'true' || item.required === true as any) && (
                              <span className="text-xs bg-danger/10 text-danger px-1 rounded">Required</span>
                            )}
                          </div>
                          {item.description && (
                            <p className="text-muted-foreground mt-0.5">{item.description}</p>
                          )}
                          {item.verification_status && !isVerifiedStatus(item.verification_status) && (
                            <span className="ll-badge-synthetic">Flagged gap - not a verified fact ({item.verification_status})</span>
                          )}
                          <div className="mt-0.5">
                            <CitationLink
                              title={`${item.jurisdiction_code === 'US' ? 'Federal' : item.state_code}: ${item.citation || item.checklist_item}`}
                              url={item.official_url}
                              citationUrl={item.citation_url}
                              verificationStatus={item.verification_status}
                              citation={item.citation}
                              lastVerified={item.last_verified}
                            />
                          </div>
                          <div className="flex gap-3 mt-0.5 text-muted-foreground">
                            {item.deadline_date && (
                              <span>Due: {formatDate(item.deadline_date)}</span>
                            )}
                            {item.assigned_to && (
                              <span>Assigned: {item.assigned_to}</span>
                            )}
                            {item.completed_date && (
                              <span className="text-accent-strong">Completed: {formatDate(item.completed_date)}</span>
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

      {groups.length === 0 && loadState === 'live' && (
        <p className="text-sm text-muted-foreground text-center py-8">
          No regulatory checklist data available for the selected filters.
        </p>
      )}
    </div>
  );
}
