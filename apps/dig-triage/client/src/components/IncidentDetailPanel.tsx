/**
 * IncidentDetailPanel.tsx
 * Selected incident detail panel showing full incident information:
 * severity, cable type, contractor info, resolution time,
 * affected services, reroute status.
 */
import type { Incident } from '../mock/mockData';
import { SEVERITY_COLORS, STATUS_COLORS } from '../mock/mockData';
import { X } from 'lucide-react';
import {
  formatCurrency,
  formatHours,
  formatTimestamp,
  severityLabel,
  incidentAge,
} from '../lib/formatters';

interface IncidentDetailPanelProps {
  incident: Incident;
  onClose: () => void;
}

export function IncidentDetailPanel({ incident, onClose }: IncidentDetailPanelProps) {
  return (
    <div className="bg-card rounded-lg border shadow-sm">
      <div className="flex items-center justify-between p-3 border-b">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-bold">{incident.incident_id}</h3>
          <span
            className="text-xs font-bold px-2 py-0.5 rounded"
            style={{
              backgroundColor: SEVERITY_COLORS[incident.severity] + '20',
              color: SEVERITY_COLORS[incident.severity],
            }}
          >
            {severityLabel(incident.severity)}
          </span>
          <span
            className="text-xs px-2 py-0.5 rounded"
            style={{
              backgroundColor: STATUS_COLORS[incident.status] + '20',
              color: STATUS_COLORS[incident.status],
            }}
          >
            {incident.status.replace('_', ' ').toUpperCase()}
          </span>
        </div>
        <button
          onClick={onClose}
          aria-label="Close detail panel"
          className="text-muted-foreground hover:text-foreground text-lg leading-none focus-visible:ring-2 focus-visible:ring-[#FF3621] focus-visible:outline-none rounded"
        >
          <X size={18} strokeWidth={1.5} />
        </button>
      </div>

      <div className="grid grid-cols-4 gap-4 p-4">
        {/* Column 1: Incident details */}
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase">Incident</h4>
          <div>
            <p className="text-xs text-muted-foreground">Date/Time</p>
            <p className="text-sm">{formatTimestamp(incident.incident_timestamp)}</p>
            <p className="text-xs text-muted-foreground">{incidentAge(incident.incident_timestamp)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Cable Type</p>
            <p className="text-sm">{incident.cable_type.replace('_', ' ')}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Damage Type</p>
            <p className="text-sm">{incident.cable_damage_type}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Root Cause</p>
            <p className="text-sm">{incident.root_cause.replace('_', ' ')}</p>
          </div>
        </div>

        {/* Column 2: Location */}
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase">Location</h4>
          <div>
            <p className="text-xs text-muted-foreground">State</p>
            <p className="text-sm font-medium">{incident.state}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Coordinates</p>
            <p className="text-sm font-mono text-xs">
              {incident.latitude.toFixed(4)}, {incident.longitude.toFixed(4)}
            </p>
          </div>
        </div>

        {/* Column 3: Impact */}
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase">Impact</h4>
          <div>
            <p className="text-xs text-muted-foreground">Affected Pairs</p>
            <p className="text-sm font-bold">{incident.affected_pair_count}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Service Interruption</p>
            <p className={`text-sm font-medium ${incident.service_interruption ? 'text-red-600' : 'text-green-600'}`}>
              {incident.service_interruption ? 'YES' : 'No'}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Reroute Required</p>
            <p className={`text-sm font-medium ${incident.reroute_required ? 'text-orange-600' : 'text-green-600'}`}>
              {incident.reroute_required ? 'YES' : 'No'}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Repair Cost</p>
            <p className="text-sm font-bold">{formatCurrency(incident.repair_cost)}</p>
          </div>
        </div>

        {/* Column 4: Contractor + Resolution */}
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase">Response</h4>
          <div>
            <p className="text-xs text-muted-foreground">Contractor</p>
            <p className="text-sm">{incident.contractor_name}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Contractor at Fault</p>
            <p className={`text-sm font-medium ${incident.contractor_at_fault ? 'text-red-600' : 'text-muted-foreground'}`}>
              {incident.contractor_at_fault ? 'YES' : 'No'}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">811 One-Call Filed</p>
            <p className={`text-sm font-medium ${!incident.one_call_ticket_submitted ? 'text-red-600' : 'text-green-600'}`}>
              {incident.one_call_ticket_submitted ? 'Yes' : 'NOT FILED'}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Resolution Time</p>
            <p className="text-sm font-bold">{formatHours(incident.resolution_time_hours)}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
