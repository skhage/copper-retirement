/**
 * ActionLog.tsx
 * Audit trail of agent recommendations and human approve/reject decisions.
 * Shows chronological log of triage actions with reviewer attribution.
 */
import { USE_MOCK_DATA, getMockActionLog } from '../mock/mockData';
import type { ActionLogEntry } from '../mock/mockData';
import { formatTimestamp } from '../lib/formatters';

const DECISION_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  approved: { bg: 'bg-green-100', text: 'text-green-800', label: 'APPROVED' },
  rejected: { bg: 'bg-red-100', text: 'text-red-800', label: 'REJECTED' },
  pending_approval: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'PENDING' },
};

export function ActionLog() {
  const entries = USE_MOCK_DATA
    ? getMockActionLog()
    : []; // TODO: fetch from Lakebase audit table

  return (
    <div className="bg-card rounded-lg border shadow-sm">
      <div className="flex items-center justify-between p-3 border-b">
        <h2 className="text-sm font-semibold">Action Log</h2>
        <span className="text-xs text-muted-foreground">
          {entries.length} actions recorded
        </span>
      </div>

      <div className="divide-y">
        {entries.map((entry) => {
          const style = DECISION_STYLES[entry.decision] || DECISION_STYLES.pending_approval;

          return (
            <div key={entry.action_id} className="flex items-start gap-4 p-3">
              {/* Decision badge */}
              <span className={`text-xs font-bold px-2 py-1 rounded ${style.bg} ${style.text} flex-shrink-0`}>
                {style.label}
              </span>

              {/* Details */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-muted-foreground">
                    {entry.incident_id}
                  </span>
                  <span className="text-xs text-muted-foreground">•</span>
                  <span className="text-xs font-medium uppercase text-muted-foreground">
                    {entry.action_type}
                  </span>
                </div>
                <p className="text-sm mt-0.5">{entry.description}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-muted-foreground">
                    {entry.reviewer}
                  </span>
                  <span className="text-xs text-muted-foreground">•</span>
                  <span className="text-xs text-muted-foreground">
                    {formatTimestamp(entry.timestamp)}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {entries.length === 0 && (
        <div className="text-center py-8 text-sm text-muted-foreground">
          No actions recorded yet.
        </div>
      )}
    </div>
  );
}
