/**
 * IncidentDetailPanel.tsx
 * Selected incident detail panel showing full incident information:
 * severity, cable type, contractor info, resolution time,
 * affected services, reroute status.
 *
 * V2 (2026-09-20): Enriched with UC function data — shows triage priority,
 * nearest device, wire center, impacted services, nearby incidents,
 * and reroute suggestions from live UC functions.
 */
import type { Incident } from '../mock/mockData';
import { SEVERITY_COLORS, STATUS_COLORS, badgeStyle } from '../mock/mockData';
import type { IncidentDetail, NearbyIncident, RerouteSuggestion } from '../lib/triageApi';
import { X, Radio, MapPin, AlertTriangle, ArrowRightLeft } from 'lucide-react';
import {
  formatCurrency,
  formatHours,
  formatTimestamp,
  severityLabel,
  incidentAge,
  toNumber,
} from '../lib/formatters';

interface IncidentDetailPanelProps {
  incident: Incident;
  enrichedData?: IncidentDetail | null;
  nearbyIncidents?: NearbyIncident[];
  rerouteSuggestion?: RerouteSuggestion | null;
  isLoadingEnriched?: boolean;
  onClose: () => void;
}

const PRIORITY_COLORS: Record<string, string> = {
  P1: 'rgb(var(--risk-critical))',
  P2: 'rgb(var(--risk-high))',
  P3: 'rgb(var(--risk-medium))',
  P4: 'rgb(var(--viz-2))',
};

export function IncidentDetailPanel({
  incident,
  enrichedData,
  nearbyIncidents = [],
  rerouteSuggestion,
  isLoadingEnriched = false,
  onClose,
}: IncidentDetailPanelProps) {
  return (
    <div className="bg-card rounded-lg border shadow-sm">
      <div className="flex items-center justify-between p-3 border-b">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-bold">{incident.incident_id}</h3>
          <span
            className="text-xs font-bold px-2 py-0.5 rounded"
            style={badgeStyle(SEVERITY_COLORS[incident.severity])}
          >
            {severityLabel(incident.severity)}
          </span>
          <span
            className="text-xs px-2 py-0.5 rounded"
            style={badgeStyle(STATUS_COLORS[incident.status])}
          >
            {incident.status.replace('_', ' ').toUpperCase()}
          </span>
          {/* Triage priority from UC function */}
          {enrichedData?.triage_priority && (
            <span
              className="text-xs font-bold px-2 py-0.5 rounded"
              style={badgeStyle(PRIORITY_COLORS[enrichedData.triage_priority])}
            >
              {enrichedData.triage_priority}
            </span>
          )}
          {isLoadingEnriched && (
            <span className="text-xs text-muted-foreground animate-pulse">Loading UC data...</span>
          )}
        </div>
        <button
          onClick={onClose}
          aria-label="Close detail panel"
          className="text-muted-foreground hover:text-foreground text-lg leading-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none rounded"
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
          {enrichedData?.recommended_action && (
            <div>
              <p className="text-xs text-muted-foreground">Recommended Action</p>
              <p className="text-sm font-medium text-primary-strong">
                {enrichedData.recommended_action.replace(/_/g, ' ')}
              </p>
            </div>
          )}
        </div>

        {/* Column 2: Location + Wire Center */}
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
          {/* UC enriched: Wire Center */}
          {enrichedData?.wire_center_name && (
            <div>
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <Radio size={12} strokeWidth={1.5} /> Wire Center
              </p>
              <p className="text-sm font-medium">{enrichedData.wire_center_name}</p>
              <p className="text-xs text-muted-foreground">{enrichedData.wire_center_id}</p>
            </div>
          )}
          {/* UC enriched: Nearest Device */}
          {enrichedData?.nearest_device_type && (
            <div>
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <MapPin size={12} strokeWidth={1.5} /> Nearest Device
              </p>
              <p className="text-sm">
                {enrichedData.nearest_device_type}{' '}
                <span className="text-xs text-muted-foreground">
                  ({parseFloat(enrichedData.nearest_device_distance_km || '0').toFixed(1)} km)
                </span>
              </p>
              <p className="text-xs text-muted-foreground">
                {toNumber(enrichedData.nearby_copper_device_count)} nearby copper devices
              </p>
            </div>
          )}
        </div>

        {/* Column 3: Impact (enriched with UC data) */}
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase">Impact</h4>
          <div>
            <p className="text-xs text-muted-foreground">Affected Pairs</p>
            <p className="text-sm font-bold">{incident.affected_pair_count}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Service Interruption</p>
            <p className={`text-sm font-medium ${incident.service_interruption ? 'text-danger' : 'text-success'}`}>
              {incident.service_interruption ? 'YES' : 'No'}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Reroute Required</p>
            <p className={`text-sm font-medium ${incident.reroute_required ? 'text-warning' : 'text-success'}`}>
              {incident.reroute_required ? 'YES' : 'No'}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Repair Cost</p>
            <p className="text-sm font-bold">{formatCurrency(incident.repair_cost)}</p>
          </div>
          {/* UC enriched: Customer/service impact */}
          {enrichedData && (
            <>
              <div>
                <p className="text-xs text-muted-foreground">Impacted Customers</p>
                <p className="text-sm font-bold">{toNumber(enrichedData.impacted_customer_count)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Impacted Services</p>
                <p className="text-sm font-bold">{toNumber(enrichedData.impacted_service_count)}</p>
                {enrichedData.impacted_service_types && (
                  <p className="text-xs text-muted-foreground">{enrichedData.impacted_service_types}</p>
                )}
              </div>
            </>
          )}
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
            <p className={`text-sm font-medium ${incident.contractor_at_fault ? 'text-danger' : 'text-muted-foreground'}`}>
              {incident.contractor_at_fault ? 'YES' : 'No'}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">811 One-Call Filed</p>
            <p className={`text-sm font-medium ${!incident.one_call_ticket_submitted ? 'text-danger' : 'text-success'}`}>
              {incident.one_call_ticket_submitted ? 'Yes' : 'NOT FILED'}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Resolution Time</p>
            <p className="text-sm font-bold">{formatHours(incident.resolution_time_hours)}</p>
          </div>
        </div>
      </div>

      {/* Reroute Suggestion (from UC reroute_suggest function) */}
      {rerouteSuggestion && (
        <div className="mx-4 mb-4 p-3 rounded-lg border bg-background">
          <div className="flex items-center gap-2 mb-2">
            <ArrowRightLeft size={16} strokeWidth={1.5} className="text-primary" aria-hidden="true" />
            <h4 className="text-xs font-semibold uppercase">Reroute Suggestion</h4>
            {rerouteSuggestion.wire_center_fiber_ready === 'true' && (
              <span className="text-xs bg-accent/15 text-accent-strong px-2 py-0.5 rounded">Fiber Ready</span>
            )}
          </div>
          <div className="flex gap-6">
            <div>
              <p className="text-xs text-muted-foreground">Option</p>
              <p className="text-sm font-semibold">{rerouteSuggestion.reroute_option?.replace(/_/g, ' ')}</p>
            </div>
            <div className="flex-1">
              <p className="text-xs text-muted-foreground">Rationale</p>
              <p className="text-sm">{rerouteSuggestion.reroute_rationale}</p>
            </div>
          </div>
        </div>
      )}

      {/* Nearby Incidents (from UC proximity_search function) */}
      {nearbyIncidents.length > 0 && (
        <div className="mx-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={16} strokeWidth={1.5} className="text-warning" aria-hidden="true" />
            <h4 className="text-xs font-semibold uppercase text-muted-foreground">
              Nearby Incidents ({nearbyIncidents.length} within 50 km)
            </h4>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {nearbyIncidents.slice(0, 6).map((ni) => (
              <div key={ni.incident_id} className="text-xs border rounded p-2 bg-muted/50">
                <span className="font-medium">INC-{ni.incident_id}</span>
                <span
                  className="ml-1 px-1 py-0.5 rounded text-xs font-bold"
                  style={badgeStyle(SEVERITY_COLORS[ni.severity as keyof typeof SEVERITY_COLORS])}
                >
                  {ni.severity}
                </span>
                <p className="text-muted-foreground mt-0.5">
                  {parseFloat(ni.distance_from_search_km).toFixed(1)} km — {ni.root_cause?.replace(/_/g, ' ')}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
