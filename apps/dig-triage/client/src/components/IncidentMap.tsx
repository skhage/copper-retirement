/**
 * IncidentMap.tsx
 * Map overlay showing dig-safe incidents colored by severity.
 * Uses pin markers on a placeholder map until deck.gl is integrated.
 *
 * Severity colors:
 *   critical → red (#EB1600)
 *   major    → orange (#FF8C00)
 *   minor    → gold (#FFD700)
 *   info     → cyan (#40d1f5)
 *
 * Click incident marker to select for detail panel + agent chat.
 *
 * TODO: Replace placeholder with deck.gl ScatterplotLayer once deps installed.
 * TODO: Add real-time incident feed via SSE once P6-TRIAGE is deployed.
 */
import { USE_MOCK_DATA, getMockIncidents, SEVERITY_COLORS } from '../mock/mockData';
import type { Incident } from '../mock/mockData';
import type { TriageFilters } from '../App';

interface IncidentMapProps {
  filters: TriageFilters;
  onIncidentSelect: (incident: Incident | null) => void;
  selectedIncident: Incident | null;
}

// US bounding box for the placeholder map
const US_BOUNDS = {
  minLat: 24.5, maxLat: 49.4,
  minLon: -125.0, maxLon: -66.9,
};

/** Convert lat/lon to pixel position within the map container */
function toPixel(
  lat: number,
  lon: number,
  width: number,
  height: number,
): { x: number; y: number } {
  const x = ((lon - US_BOUNDS.minLon) / (US_BOUNDS.maxLon - US_BOUNDS.minLon)) * width;
  const y = ((US_BOUNDS.maxLat - lat) / (US_BOUNDS.maxLat - US_BOUNDS.minLat)) * height;
  return { x, y };
}

export function IncidentMap({ filters, onIncidentSelect, selectedIncident }: IncidentMapProps) {
  const incidents = USE_MOCK_DATA
    ? getMockIncidents(filters)
    : []; // TODO: fetch from SQL query

  const MAP_WIDTH = 800;
  const MAP_HEIGHT = 480;

  return (
    <div className="bg-card rounded-lg border shadow-sm">
      <div className="flex items-center justify-between p-3 border-b">
        <h2 className="text-sm font-semibold">Incident Map</h2>
        <span className="text-xs text-muted-foreground">
          {incidents.length} incidents shown
        </span>
      </div>

      {/* Placeholder map — swap for deck.gl ScatterplotLayer */}
      <div
        className="relative bg-slate-100 overflow-hidden"
        style={{ width: '100%', height: MAP_HEIGHT, maxWidth: MAP_WIDTH }}
      >
        {/* US outline placeholder */}
        <div className="absolute inset-0 flex items-center justify-center text-slate-300 text-sm">
          [deck.gl map placeholder — install deps to activate]
        </div>

        {/* Incident markers */}
        {incidents.map((inc) => {
          const { x, y } = toPixel(inc.latitude, inc.longitude, MAP_WIDTH, MAP_HEIGHT);
          const isSelected = selectedIncident?.incident_id === inc.incident_id;

          return (
            <button
              key={inc.incident_id}
              onClick={() => onIncidentSelect(isSelected ? null : inc)}
              className="absolute rounded-full border-2 border-white shadow-md hover:scale-125 transition-transform cursor-pointer"
              style={{
                left: `${(x / MAP_WIDTH) * 100}%`,
                top: `${(y / MAP_HEIGHT) * 100}%`,
                width: isSelected ? 20 : 14,
                height: isSelected ? 20 : 14,
                backgroundColor: SEVERITY_COLORS[inc.severity] || '#888',
                transform: 'translate(-50%, -50%)',
                zIndex: isSelected ? 10 : 1,
                outline: isSelected ? '3px solid #1a73e8' : 'none',
              }}
              title={`${inc.incident_id}: ${inc.severity} — ${inc.cable_damage_type} (${inc.state})`}
            />
          );
        })}
      </div>

      {/* Severity legend */}
      <div className="flex items-center gap-4 p-2 border-t text-xs">
        {Object.entries(SEVERITY_COLORS).map(([severity, color]) => (
          <div key={severity} className="flex items-center gap-1">
            <span
              className="inline-block w-3 h-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="capitalize">{severity}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
