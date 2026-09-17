/**
 * ComplianceChecklist.tsx
 * Screen 3 — Compliance Checklist.
 * Hierarchical checklist: State → Wire Center → Requirement → Status.
 * Expandable tree view with filters and deadline timeline.
 */
import { useState, useMemo } from 'react';
import {
  CheckCircle2,
  Circle,
  AlertTriangle,
  XCircle,
  Flag,
  ChevronRight,
  ChevronDown,
} from 'lucide-react';
import {
  USE_MOCK_DATA,
  getMockChecklist,
  COMPLIANCE_COLORS,
  REQUIREMENT_TYPE_LABELS,
} from '../mock/mockData';
import type { ChecklistItem } from '../mock/mockData';

interface ComplianceChecklistProps {
  jurisdictionFilter: string;
}

export function ComplianceChecklist({ jurisdictionFilter }: ComplianceChecklistProps) {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [expandedStates, setExpandedStates] = useState<Set<string>>(new Set(['CO', 'OR', 'MN']));

  const items = useMemo(
    () => getMockChecklist({
      state: jurisdictionFilter !== 'all' ? jurisdictionFilter : undefined,
      status: statusFilter !== 'all' ? statusFilter : undefined,
      requirement_type: typeFilter !== 'all' ? typeFilter : undefined,
    }),
    [jurisdictionFilter, statusFilter, typeFilter]
  );

  // Group by state, then wire_center
  const grouped = useMemo(() => {
    const map: Record<string, Record<string, ChecklistItem[]>> = {};
    for (const item of items) {
      if (!map[item.state]) map[item.state] = {};
      if (!map[item.state][item.wire_center]) map[item.state][item.wire_center] = [];
      map[item.state][item.wire_center].push(item);
    }
    return map;
  }, [items]);

  const toggleState = (state: string) => {
    setExpandedStates((prev) => {
      const next = new Set(prev);
      if (next.has(state)) next.delete(state);
      else next.add(state);
      return next;
    });
  };

  const statusIcon = (status: string, color: string) => {
    const props = { size: 16, strokeWidth: 1.5, color };
    switch (status) {
      case 'complete': return <CheckCircle2 {...props} />;
      case 'pending': return <Circle {...props} />;
      case 'overdue': return <AlertTriangle {...props} />;
      case 'blocked': return <XCircle {...props} />;
      case 'flagged': return <Flag {...props} />;
      default: return <Circle {...props} />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-3">
        <div>
          <label className="text-xs text-muted-foreground">Status</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="block border rounded px-2 py-1 text-sm bg-background"
          >
            <option value="all">All</option>
            <option value="complete">Complete</option>
            <option value="pending">Pending</option>
            <option value="overdue">Overdue</option>
            <option value="blocked">Blocked</option>
            <option value="flagged">Flagged</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-muted-foreground">Requirement Type</label>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="block border rounded px-2 py-1 text-sm bg-background"
          >
            <option value="all">All Types</option>
            <option value="section_214">Section 214</option>
            <option value="state_puc">State PUC Filing</option>
            <option value="residential_notice">Residential Notice</option>
            <option value="911_coordination">911 Coordination</option>
            <option value="environmental">Environmental Review</option>
          </select>
        </div>
      </div>

      {/* Overdue banner */}
      {items.some((i) => i.status === 'overdue') && (
        <div className="rounded-lg p-3 flex items-center justify-between" style={{
          backgroundColor: 'rgba(255,54,33,0.06)',
          border: '1px solid rgba(255,54,33,0.2)',
        }}>
          <span className="text-sm" style={{ color: '#1B3139' }}>
            <AlertTriangle size={16} strokeWidth={1.5} color="#FF3621" style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: 6 }} />
            {items.filter((i) => i.status === 'overdue').length} overdue item(s) require immediate attention
          </span>
          <button className="text-xs text-white px-3 py-1 rounded" style={{ backgroundColor: '#FF3621' }}>
            Escalate to Legal
          </button>
        </div>
      )}

      {/* Hierarchical checklist */}
      <div className="border rounded-lg">
        {Object.entries(grouped).map(([state, wirecenters]) => (
          <div key={state} className="border-b last:border-b-0">
            {/* State header */}
            <button
              onClick={() => toggleState(state)}
              className="w-full flex items-center justify-between px-4 py-3 hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-2">
                {expandedStates.has(state)
                  ? <ChevronDown size={16} strokeWidth={1.5} color="#1B3139" />
                  : <ChevronRight size={16} strokeWidth={1.5} color="#1B3139" />}
                <span className="font-semibold">{state}</span>
                <span className="text-xs text-muted-foreground">
                  ({Object.values(wirecenters).flat().length} items)
                </span>
              </div>
              <div className="flex gap-1">
                {['complete', 'pending', 'overdue', 'blocked'].map((s) => {
                  const count = Object.values(wirecenters).flat().filter((i) => i.status === s).length;
                  if (count === 0) return null;
                  return (
                    <span
                      key={s}
                      className="text-[10px] px-1.5 py-0.5 rounded text-white"
                      style={{ backgroundColor: COMPLIANCE_COLORS[s] }}
                    >
                      {count} {s}
                    </span>
                  );
                })}
              </div>
            </button>

            {/* Wire center items */}
            {expandedStates.has(state) && (
              <div className="pl-6">
                {Object.entries(wirecenters).map(([wc, wcItems]) => (
                  <div key={wc} className="border-t">
                    <div className="px-4 py-2 text-sm font-medium text-muted-foreground bg-muted/30">
                      {wc}
                    </div>
                    {wcItems.map((item) => (
                      <div
                        key={item.id}
                        className="flex items-center gap-3 px-4 py-2 text-sm border-t hover:bg-muted/20"
                      >
                        <span
                          className="text-base"
                          style={{ color: COMPLIANCE_COLORS[item.status] }}
                        >
                          {statusIcon(item.status, COMPLIANCE_COLORS[item.status])}
                        </span>
                        <div className="flex-1">
                          <p className="font-medium">{item.requirement}</p>
                          <p className="text-xs text-muted-foreground">
                            {REQUIREMENT_TYPE_LABELS[item.requirement_type]} • Due: {item.due_date}
                            {item.completed_date && ` • Completed: ${item.completed_date}`}
                          </p>
                          {item.notes && (
                            <p className="text-xs text-muted-foreground mt-0.5 italic">{item.notes}</p>
                          )}
                        </div>
                        <span
                          className="text-xs px-2 py-0.5 rounded text-white"
                          style={{ backgroundColor: COMPLIANCE_COLORS[item.status] }}
                        >
                          {item.status}
                        </span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {Object.keys(grouped).length === 0 && (
          <div className="p-8 text-center text-muted-foreground">
            No checklist items match the current filters.
          </div>
        )}
      </div>
    </div>
  );
}
