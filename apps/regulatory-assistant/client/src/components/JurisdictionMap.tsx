/**
 * JurisdictionMap.tsx
 * Screen 2 — Jurisdiction Map.
 * US state choropleth (NOT deck.gl H3 — different from P7-MAP).
 * Color by compliance status: green (clear), yellow (pending), red (blocked/overdue).
 * Click state to set jurisdiction filter.
 *
 * Includes JurisdictionTable and StateRegCard inline.
 */
import { useState, useMemo } from 'react';
import {
  USE_MOCK_DATA,
  getMockJurisdictions,
  COMPLIANCE_COLORS,
} from '../mock/mockData';
import type { JurisdictionRow } from '../mock/mockData';

interface JurisdictionMapProps {
  jurisdictionFilter: string;
  onStateSelect: (state: string) => void;
}

// US state approximate positions for the scaffold placeholder
const STATE_POSITIONS: Record<string, { x: number; y: number }> = {
  CO: { x: 220, y: 190 },
  WA: { x: 95, y: 60 },
  OR: { x: 80, y: 110 },
  AZ: { x: 140, y: 250 },
  MN: { x: 370, y: 100 },
  ID: { x: 145, y: 100 },
};

export function JurisdictionMap({ jurisdictionFilter, onStateSelect }: JurisdictionMapProps) {
  const [selectedState, setSelectedState] = useState<JurisdictionRow | null>(null);

  const jurisdictions = useMemo(
    () => getMockJurisdictions(jurisdictionFilter !== 'all' ? jurisdictionFilter : undefined),
    [jurisdictionFilter]
  );

  const allJurisdictions = useMemo(() => getMockJurisdictions(), []);

  const handleStateClick = (jurisdiction: JurisdictionRow) => {
    setSelectedState(jurisdiction);
    onStateSelect(jurisdiction.state);
  };

  return (
    <div className="space-y-6">
      {/* Placeholder map */}
      <div className="relative bg-muted rounded-lg overflow-hidden" style={{ height: 400 }}>
        <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
          <p className="text-sm">US State Choropleth — install mapping library to render full map</p>
        </div>

        {/* Clickable state markers */}
        {allJurisdictions.map((j) => {
          const pos = STATE_POSITIONS[j.state];
          if (!pos) return null;
          return (
            <button
              key={j.state}
              onClick={() => handleStateClick(j)}
              className="absolute flex flex-col items-center group"
              style={{ left: pos.x, top: pos.y }}
            >
              <div
                className="w-10 h-10 rounded-full border-2 border-white shadow-md flex items-center justify-center text-xs font-bold text-white group-hover:scale-110 transition-transform"
                style={{ backgroundColor: COMPLIANCE_COLORS[j.compliance_status] }}
              >
                {j.state}
              </div>
              <span className="text-[10px] mt-0.5 text-muted-foreground">
                {j.compliance_status}
              </span>
            </button>
          );
        })}
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
