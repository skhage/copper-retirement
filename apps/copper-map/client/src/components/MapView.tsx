/**
 * MapView.tsx
 * Full-screen deck.gl map with H3 hex layer colored by risk score.
 *
 * Uses DeckGL + H3HexagonLayer from @deck.gl/geo-layers.
 * When real H3 data lands (P2-H3 + P4-RISK), replace mock data
 * with useAnalyticsQuery('hex_risk_summary', params).
 *
 * Dependencies: @deck.gl/core, @deck.gl/layers, @deck.gl/react,
 *              @deck.gl/geo-layers, h3-js, maplibre-gl
 */
import { useMemo, useCallback } from 'react';
import { useAnalyticsQuery, Skeleton } from '@databricks/appkit-ui/react';
import { sql } from '@databricks/appkit-ui/js';
import {
  USE_MOCK_DATA,
  getMockHexCells,
  RISK_COLORS,
} from '../mock/mockData';
import type { HexRiskRow } from '../mock/mockData';
import type { Filters } from './FilterPanel';

interface MapViewProps {
  filters: Filters;
  onHexSelect: (cell: HexRiskRow | null) => void;
}

// US center for initial view
const INITIAL_VIEW_STATE = {
  longitude: -98.5,
  latitude: 39.8,
  zoom: 4,
  pitch: 0,
  bearing: 0,
};

/**
 * Risk score → RGBA color tuple for deck.gl.
 * Critical (>=75): red, High (>=50): orange, Medium (>=25): gold, Low: cyan
 */
function riskToColor(score: number): [number, number, number, number] {
  if (score >= 75) return [235, 22, 0, 200];    // critical — red
  if (score >= 50) return [255, 140, 0, 180];   // high — orange
  if (score >= 25) return [255, 215, 0, 160];   // medium — gold
  return [64, 209, 245, 140];                   // low — cyan
}

export function MapView({ filters, onHexSelect }: MapViewProps) {
  // Build query params from filters
  const params = useMemo(
    () => ({
      state_filter: sql.string(filters.state === 'all' ? '' : filters.state),
      risk_tier: sql.string(filters.riskTier === 'all' ? '' : filters.riskTier),
      device_type: sql.string(filters.deviceType === 'all' ? '' : filters.deviceType),
    }),
    [filters.state, filters.riskTier, filters.deviceType]
  );

  const { data, loading, error } = useAnalyticsQuery('hex_risk_summary', params, {
    autoStart: !USE_MOCK_DATA,
  });

  // Resolve hex data from mock or live query
  const hexData: HexRiskRow[] = USE_MOCK_DATA
    ? getMockHexCells({
        state: filters.state === 'all' ? undefined : filters.state,
        riskTier: filters.riskTier === 'all' ? undefined : filters.riskTier,
        deviceType: filters.deviceType === 'all' ? undefined : filters.deviceType,
      })
    : (data as HexRiskRow[] | undefined) ?? [];

  const handleClick = useCallback(
    (info: { object?: HexRiskRow }) => {
      onHexSelect(info.object ?? null);
    },
    [onHexSelect]
  );

  if (!USE_MOCK_DATA && loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-muted rounded-lg">
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!USE_MOCK_DATA && error) {
    return (
      <div className="flex-1 flex items-center justify-center bg-muted rounded-lg text-destructive p-4">
        Map data error: {String(error)}
      </div>
    );
  }

  // ---------------------------------------------------------------
  // SCAFFOLD PLACEHOLDER
  // When deck.gl is installed, replace this with:
  //
  //   import DeckGL from '@deck.gl/react';
  //   import { H3HexagonLayer } from '@deck.gl/geo-layers';
  //   import { Map } from 'react-map-gl/maplibre';
  //
  //   const hexLayer = new H3HexagonLayer({
  //     id: 'risk-hex',
  //     data: hexData,
  //     getHexagon: (d: HexRiskRow) => d.h3_cell,
  //     getFillColor: (d: HexRiskRow) => riskToColor(d.avg_risk_score),
  //     getElevation: (d: HexRiskRow) => d.device_count,
  //     elevationScale: 50,
  //     extruded: true,
  //     pickable: true,
  //     onClick: handleClick,
  //   });
  //
  //   <DeckGL initialViewState={INITIAL_VIEW_STATE} controller layers={[hexLayer]}>
  //     <Map mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json" />
  //   </DeckGL>
  // ---------------------------------------------------------------

  return (
    <div className="flex-1 bg-muted rounded-lg relative overflow-hidden" style={{ minHeight: 500 }}>
      {/* Static placeholder map */}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground">
        <p className="text-lg font-semibold mb-2">Copper Prioritization Map</p>
        <p className="text-sm">deck.gl H3HexagonLayer — install dependencies to render</p>
        <p className="text-xs mt-1">npm install @deck.gl/core @deck.gl/layers @deck.gl/react @deck.gl/geo-layers h3-js maplibre-gl react-map-gl</p>
      </div>

      {/* Mock hex cell summary */}
      <div className="absolute bottom-4 left-4 right-4 grid grid-cols-2 md:grid-cols-4 gap-2">
        {hexData.slice(0, 8).map((cell) => (
          <button
            key={cell.h3_cell}
            className="p-2 rounded text-xs text-left border"
            style={{ borderLeftColor: RISK_COLORS[cell.risk_tier], borderLeftWidth: 4 }}
            onClick={() => onHexSelect(cell)}
          >
            <span className="font-semibold">{cell.state}</span>
            <span className="text-muted-foreground ml-1">
              {cell.device_count} devices • risk {cell.avg_risk_score}
            </span>
          </button>
        ))}
      </div>

      {USE_MOCK_DATA && (
        <div className="absolute top-2 right-2">
          <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
            SYNTHETIC DATA
          </span>
        </div>
      )}
    </div>
  );
}

export { riskToColor, INITIAL_VIEW_STATE };
