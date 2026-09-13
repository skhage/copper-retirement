/**
 * IncidentTable.tsx
 * Sortable/filterable table of dig-safe incidents.
 * Includes filter dropdowns for severity, state, and status.
 */
import { USE_MOCK_DATA, getMockIncidents, getMockStates, SEVERITY_LEVELS, SEVERITY_COLORS, STATUS_COLORS } from '../mock/mockData';
import type { Incident } from '../mock/mockData';
import type { TriageFilters } from '../App';
import {
  formatCurrency,
  formatHours,
  formatTimestamp,
  severityLabel,
  incidentAge,
} from '../lib/formatters';

interface IncidentTableProps {
  filters: TriageFilters;
  onFilterChange: (filters: TriageFilters) => void;
  onIncidentSelect: (incident: Incident) => void;
}

export function IncidentTable({ filters, onFilterChange, onIncidentSelect }: IncidentTableProps) {
  const incidents = USE_MOCK_DATA
    ? getMockIncidents(filters)
    : []; // TODO: fetch from SQL query

  return (
    <div className="bg-card rounded-lg border shadow-sm">
      {/* Filters */}
      <div className="flex items-center gap-4 p-3 border-b">
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium">Severity:</label>
          <select
            value={filters.severity}
            onChange={(e) => onFilterChange({ ...filters, severity: e.target.value })}
            aria-label="Filter by severity"
            className="border rounded px-2 py-1 text-sm focus-visible:ring-2 focus-visible:ring-[#FF3621] focus-visible:outline-none"
          >
            <option value="all">All</option>
            {SEVERITY_LEVELS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium">State:</label>
          <select
            value={filters.state}
            onChange={(e) => onFilterChange({ ...filters, state: e.target.value })}
            aria-label="Filter by state"
            className="border rounded px-2 py-1 text-sm focus-visible:ring-2 focus-visible:ring-[#FF3621] focus-visible:outline-none"
          >
            <option value="all">All</option>
            {getMockStates().map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium">Status:</label>
          <select
            value={filters.status}
            onChange={(e) => onFilterChange({ ...filters, status: e.target.value })}
            aria-label="Filter by status"
            className="border rounded px-2 py-1 text-sm focus-visible:ring-2 focus-visible:ring-[#FF3621] focus-visible:outline-none"
          >
            <option value="all">All</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </div>
        <span className="text-xs text-muted-foreground ml-auto">
          {incidents.length} incidents
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="text-left px-3 py-2 text-xs font-medium">ID</th>
              <th className="text-left px-3 py-2 text-xs font-medium">Date</th>
              <th className="text-left px-3 py-2 text-xs font-medium">Severity</th>
              <th className="text-left px-3 py-2 text-xs font-medium">State</th>
              <th className="text-left px-3 py-2 text-xs font-medium">Cable</th>
              <th className="text-left px-3 py-2 text-xs font-medium">Root Cause</th>
              <th className="text-left px-3 py-2 text-xs font-medium">Pairs</th>
              <th className="text-left px-3 py-2 text-xs font-medium">Cost</th>
              <th className="text-left px-3 py-2 text-xs font-medium">Resolution</th>
              <th className="text-left px-3 py-2 text-xs font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((inc) => (
              <tr
                key={inc.incident_id}
                onClick={() => onIncidentSelect(inc)}
                className="border-b hover:bg-muted/30 cursor-pointer transition-colors"
              >
                <td className="px-3 py-2 font-mono text-xs">{inc.incident_id}</td>
                <td className="px-3 py-2">
                  <span className="text-xs">{formatTimestamp(inc.incident_timestamp)}</span>
                  <br />
                  <span className="text-xs text-muted-foreground">{incidentAge(inc.incident_timestamp)}</span>
                </td>
                <td className="px-3 py-2">
                  <span
                    className="text-xs font-bold px-2 py-0.5 rounded"
                    style={{
                      backgroundColor: SEVERITY_COLORS[inc.severity] + '20',
                      color: SEVERITY_COLORS[inc.severity],
                    }}
                  >
                    {severityLabel(inc.severity)}
                  </span>
                </td>
                <td className="px-3 py-2 font-medium">{inc.state}</td>
                <td className="px-3 py-2 text-xs">{inc.cable_type.replace('_', ' ')}</td>
                <td className="px-3 py-2 text-xs">{inc.root_cause.replace('_', ' ')}</td>
                <td className="px-3 py-2 text-right">{inc.affected_pair_count}</td>
                <td className="px-3 py-2 text-right">{formatCurrency(inc.repair_cost)}</td>
                <td className="px-3 py-2">{formatHours(inc.resolution_time_hours)}</td>
                <td className="px-3 py-2">
                  <span
                    className="text-xs px-2 py-0.5 rounded"
                    style={{
                      backgroundColor: STATUS_COLORS[inc.status] + '20',
                      color: STATUS_COLORS[inc.status],
                    }}
                  >
                    {inc.status.replace('_', ' ')}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {incidents.length === 0 && (
        <div className="text-center py-8 text-sm text-muted-foreground">
          No incidents match the current filters.
        </div>
      )}
    </div>
  );
}
