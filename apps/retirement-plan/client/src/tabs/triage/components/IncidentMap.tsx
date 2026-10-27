/**
 * IncidentMap.tsx
 * Map overlay showing dig-safe incidents colored by severity.
 * Uses pin markers on a placeholder map until deck.gl is integrated.
 *
 * Severity colors:
 *   critical → --risk-critical, major → --risk-high, minor → --risk-medium, info → --viz-2 (styles/tokens.css)
 *
 * Click incident marker to select for detail panel + agent chat.
 *
 * TODO: Replace placeholder with deck.gl ScatterplotLayer once deps installed.
 * TODO: Add real-time incident feed via SSE once P6-TRIAGE is deployed.
 */
import { useState, useEffect } from 'react';
import { USE_MOCK_DATA, getMockIncidents, SEVERITY_COLORS, NEUTRAL_FILL } from '../mock/mockData';
import type { Incident } from '../mock/mockData';
import type { TriageFilters } from '../App';
import { fetchIncidents, describeApiError } from '../lib/triageApi';

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
  const [allIncidents, setAllIncidents] = useState<Incident[]>(
    USE_MOCK_DATA ? getMockIncidents() : []
  );
  const [isLoading, setIsLoading] = useState(!USE_MOCK_DATA);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    if (USE_MOCK_DATA) return;
    setIsLoading(true);
    fetchIncidents(200)
      .then((data) => {
        setAllIncidents(data as unknown as Incident[]);
        setIsLoading(false);
      })
      .catch((err) => {
        // COO-Q-20261027-0550-2: never fall back to mock incidents on a live failure.
        console.warn('[IncidentMap] Live fetch failed:', err);
        setAllIncidents([]);
        setLoadError(describeApiError(err));
        setIsLoading(false);
      });
  }, []);

  // Client-side filtering
  const incidents = allIncidents.filter((inc) => {
    if (filters.severity && filters.severity !== 'all' && inc.severity !== filters.severity) return false;
    if (filters.state && filters.state !== 'all' && inc.state !== filters.state) return false;
    if (filters.status && filters.status !== 'all' && inc.status !== filters.status) return false;
    return true;
  });

  const MAP_WIDTH = 800;
  const MAP_HEIGHT = 480;

  return (
    <div className="bg-card rounded-lg border shadow-sm">
      <div className="flex items-center justify-between p-3 border-b">
        <h2 className="text-sm font-semibold">Incident Map</h2>
        <span className="text-xs text-muted-foreground">
          {isLoading ? 'Loading live data...' : loadError ? loadError : `${incidents.length} incidents shown`}
          {USE_MOCK_DATA && <span className="ml-1 ll-badge-synthetic">MOCK</span>}
          {!USE_MOCK_DATA && !isLoading && !loadError && (
            <span className="ml-1 text-accent-strong">● LIVE</span>
          )}
        </span>
      </div>

      {/* Placeholder map — swap for deck.gl ScatterplotLayer */}
      <div
        className="relative bg-muted overflow-hidden"
        style={{ width: '100%', height: MAP_HEIGHT, maxWidth: MAP_WIDTH }}
      >
        {/* US outline placeholder */}
        <div className="absolute inset-0 flex items-center justify-center text-muted-foreground text-sm">
          Schematic US view (lat/lon projection)
        </div>

        {/* Incident markers */}
        {incidents.map((inc) => {
          const { x, y } = toPixel(inc.latitude, inc.longitude, MAP_WIDTH, MAP_HEIGHT);
          const isSelected = selectedIncident?.incident_id === inc.incident_id;

          return (
            <button
              key={inc.incident_id}
              onClick={() => onIncidentSelect(isSelected ? null : inc)}
              aria-label={`Incident ${inc.incident_id}: ${inc.severity} severity, ${inc.cable_damage_type} in ${inc.state}`}
              className="absolute rounded-full border-2 border-card shadow-md hover:scale-125 motion-reduce:hover:scale-100 transition-transform cursor-pointer focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              style={{
                left: `${(x / MAP_WIDTH) * 100}%`,
                top: `${(y / MAP_HEIGHT) * 100}%`,
                width: isSelected ? 20 : 14,
                height: isSelected ? 20 : 14,
                backgroundColor: SEVERITY_COLORS[inc.severity] || NEUTRAL_FILL,
                transform: 'translate(-50%, -50%)',
                zIndex: isSelected ? 10 : 1,
                outline: isSelected ? '3px solid rgb(var(--color-secondary))' : 'none',
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
