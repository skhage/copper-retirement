/**
 * JurisdictionMap.tsx
 * Screen 2 — Jurisdiction Map.
 * US state choropleth using react-simple-maps (AlbersUsa projection).
 * Color by compliance status: green (clear), yellow (pending), red (blocked/overdue).
 * Click state to set jurisdiction filter. Hover shows tooltip.
 *
 * Includes JurisdictionTable and StateRegCard inline.
 */
import { useState, useMemo, useCallback } from 'react';
import {
  ComposableMap,
  Geographies,
  Geography,
  Annotation,
} from 'react-simple-maps';
import {
  getMockJurisdictions,
  COMPLIANCE_COLORS,
} from '../mock/mockData';
import type { JurisdictionRow } from '../mock/mockData';

interface JurisdictionMapProps {
  jurisdictionFilter: string;
  onStateSelect: (state: string) => void;
}

// US Atlas TopoJSON (states)
const GEO_URL = 'https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json';

// Map full state name → abbreviation for matching TopoJSON → jurisdiction data
const STATE_NAME_TO_ABBR: Record<string, string> = {
  Alabama: 'AL', Alaska: 'AK', Arizona: 'AZ', Arkansas: 'AR', California: 'CA',
  Colorado: 'CO', Connecticut: 'CT', Delaware: 'DE', Florida: 'FL', Georgia: 'GA',
  Hawaii: 'HI', Idaho: 'ID', Illinois: 'IL', Indiana: 'IN', Iowa: 'IA',
  Kansas: 'KS', Kentucky: 'KY', Louisiana: 'LA', Maine: 'ME', Maryland: 'MD',
  Massachusetts: 'MA', Michigan: 'MI', Minnesota: 'MN', Mississippi: 'MS', Missouri: 'MO',
  Montana: 'MT', Nebraska: 'NE', Nevada: 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
  'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND',
  Ohio: 'OH', Oklahoma: 'OK', Oregon: 'OR', Pennsylvania: 'PA', 'Rhode Island': 'RI',
  'South Carolina': 'SC', 'South Dakota': 'SD', Tennessee: 'TN', Texas: 'TX', Utah: 'UT',
  Vermont: 'VT', Virginia: 'VA', Washington: 'WA', 'West Virginia': 'WV',
  Wisconsin: 'WI', Wyoming: 'WY',
};

// Lakelink brand palette for non-jurisdiction states
const DEFAULT_FILL = '#E8E4DF';       // warm neutral
const HOVER_FILL = '#6E8898';          // brand muted steel
const STROKE_COLOR = '#FFFFFF';

export function JurisdictionMap({ jurisdictionFilter, onStateSelect }: JurisdictionMapProps) {
  const [selectedState, setSelectedState] = useState<JurisdictionRow | null>(null);
  const [tooltipContent, setTooltipContent] = useState('');
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  const jurisdictions = useMemo(
    () => getMockJurisdictions(jurisdictionFilter !== 'all' ? jurisdictionFilter : undefined),
    [jurisdictionFilter]
  );

  const allJurisdictions = useMemo(() => getMockJurisdictions(), []);

  // Quick lookup: state abbreviation → jurisdiction row
  const jurisdictionByAbbr = useMemo(() => {
    const map = new Map<string, JurisdictionRow>();
    for (const j of allJurisdictions) {
      map.set(j.state, j);
    }
    return map;
  }, [allJurisdictions]);

  const handleStateClick = useCallback((jurisdiction: JurisdictionRow) => {
    setSelectedState(jurisdiction);
    onStateSelect(jurisdiction.state);
  }, [onStateSelect]);

  const handleGeoClick = useCallback(
    (geoName: string) => {
      const abbr = STATE_NAME_TO_ABBR[geoName];
      if (!abbr) return;
      const jRow = jurisdictionByAbbr.get(abbr);
      if (jRow) handleStateClick(jRow);
    },
    [jurisdictionByAbbr, handleStateClick]
  );

  return (
    <div className="space-y-6">
      {/* SVG Choropleth */}
      <div
        className="relative bg-muted rounded-lg overflow-hidden"
        style={{ height: 440 }}
        role="img"
        aria-label="US jurisdiction compliance map — color-coded by compliance status. Use the table below for keyboard-accessible details."
        onMouseLeave={() => { setTooltipContent(''); setTooltipPos(null); }}
      >
        {/* Tooltip */}
        {tooltipContent && tooltipPos && (
          <div
            className="pointer-events-none absolute z-10 rounded px-2 py-1 text-xs font-medium text-white shadow-lg"
            style={{
              left: tooltipPos.x + 12,
              top: tooltipPos.y - 28,
              backgroundColor: '#1B3139',
            }}
          >
            {tooltipContent}
          </div>
        )}

        {/* Loading indicator — shown while TopoJSON fetches */}
        {!mapLoaded && (
          <div className="absolute inset-0 flex flex-col items-center justify-center z-[5]">
            <div
              className="animate-spin rounded-full"
              style={{
                width: 28,
                height: 28,
                border: '3px solid rgba(27,49,57,0.12)',
                borderTopColor: '#00A972',
              }}
            />
            <span className="mt-3 text-xs" style={{ color: '#6E8898' }}>Loading map...</span>
          </div>
        )}

        <ComposableMap projection="geoAlbersUsa" width={800} height={440}>
          <Geographies geography={GEO_URL}>
            {({ geographies }) => {
              if (geographies.length > 0 && !mapLoaded) {
                // Schedule state update after render
                setTimeout(() => setMapLoaded(true), 0);
              }
              return geographies.map((geo) => {
                const geoName: string = geo.properties.name;
                const abbr = STATE_NAME_TO_ABBR[geoName];
                const jRow = abbr ? jurisdictionByAbbr.get(abbr) : undefined;
                const fill = jRow
                  ? COMPLIANCE_COLORS[jRow.compliance_status]
                  : DEFAULT_FILL;
                const isSelected =
                  selectedState && abbr === selectedState.state;

                return (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    fill={fill}
                    stroke={isSelected ? '#1B3139' : STROKE_COLOR}
                    strokeWidth={isSelected ? 2 : 0.5}
                    style={{
                      default: { outline: 'none' },
                      hover: { fill: jRow ? fill : HOVER_FILL, outline: 'none', opacity: 0.85, cursor: 'pointer' },
                      pressed: { outline: 'none' },
                    }}
                    onClick={() => handleGeoClick(geoName)}
                    onMouseMove={(evt: React.MouseEvent) => {
                      const rect = (evt.currentTarget as SVGElement).closest('div')?.getBoundingClientRect();
                      if (rect) {
                        setTooltipPos({ x: evt.clientX - rect.left, y: evt.clientY - rect.top });
                      }
                      setTooltipContent(
                        jRow
                          ? `${geoName} (${abbr}) — ${jRow.compliance_status}`
                          : geoName
                      );
                    }}
                    onMouseLeave={() => {
                      setTooltipContent('');
                      setTooltipPos(null);
                    }}
                  />
                );
              });
            }}
          </Geographies>
        </ComposableMap>

        {/* Legend */}
        <div className="absolute bottom-3 left-3 flex gap-3 bg-background/80 backdrop-blur rounded px-3 py-1.5 text-xs">
          {(['clear', 'pending', 'blocked', 'overdue'] as const).map((s) => (
            <div key={s} className="flex items-center gap-1">
              <span
                className="inline-block w-3 h-3 rounded-sm"
                style={{ backgroundColor: COMPLIANCE_COLORS[s] }}
              />
              <span className="capitalize">{s}</span>
            </div>
          ))}
          <div className="flex items-center gap-1">
            <span
              className="inline-block w-3 h-3 rounded-sm"
              style={{ backgroundColor: DEFAULT_FILL }}
            />
            <span>No data</span>
          </div>
        </div>
      </div>

      {/* State detail card (when selected) */}
      {selectedState && (
        <div className="border rounded-lg p-4 bg-background">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold">{selectedState.state_name}</h3>
            <span
              className="text-xs px-2 py-0.5 rounded text-white"
              style={{ backgroundColor: COMPLIANCE_COLORS[selectedState.compliance_status] }}
            >
              {selectedState.compliance_status}
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-xs text-muted-foreground">State PUC</p>
              <p className="font-medium">{selectedState.state_puc}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Notice Period</p>
              <p className="font-medium">{selectedState.notice_period_days} days</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Filing Type</p>
              <p className="font-medium">{selectedState.filing_type}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Section 214 Required</p>
              <p className="font-medium">{selectedState.section_214_required ? 'Yes' : 'No'}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Residential Notice</p>
              <p className="font-medium">{selectedState.residential_notice_days} days</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Pending Filings</p>
              <p className="font-medium">{selectedState.pending_filings}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Next Deadline</p>
              <p className="font-medium">{selectedState.next_deadline}</p>
            </div>
          </div>
        </div>
      )}

      {/* Jurisdiction table */}
      <div>
        <h3 className="font-semibold mb-2">Jurisdiction Requirements</h3>
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="text-left px-3 py-2">State</th>
                <th className="text-left px-3 py-2">PUC</th>
                <th className="text-center px-3 py-2">Notice (days)</th>
                <th className="text-left px-3 py-2">Filing Type</th>
                <th className="text-center px-3 py-2">§214</th>
                <th className="text-center px-3 py-2">Status</th>
                <th className="text-left px-3 py-2">Next Deadline</th>
              </tr>
            </thead>
            <tbody>
              {jurisdictions.map((j) => (
                <tr
                  key={j.state}
                  className="border-t hover:bg-muted/50 cursor-pointer"
                  onClick={() => handleStateClick(j)}
                >
                  <td className="px-3 py-2 font-medium">{j.state_name}</td>
                  <td className="px-3 py-2">{j.state_puc}</td>
                  <td className="px-3 py-2 text-center">{j.notice_period_days}</td>
                  <td className="px-3 py-2">{j.filing_type}</td>
                  <td className="px-3 py-2 text-center">{j.section_214_required ? '✓' : '—'}</td>
                  <td className="px-3 py-2 text-center">
                    <span
                      className="text-xs px-2 py-0.5 rounded text-white"
                      style={{ backgroundColor: COMPLIANCE_COLORS[j.compliance_status] }}
                    >
                      {j.compliance_status}
                    </span>
                  </td>
                  <td className="px-3 py-2">{j.next_deadline}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
