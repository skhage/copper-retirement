/**
 * mockData.ts
 * Mock data for the Copper Retirement Impact Map.
 *
 * REDESIGNED per CEO directive (2026-09-11): App is about WHERE to dig
 * copper out of the ground and WHAT HAPPENS when we do — customer impact,
 * revenue at risk, network disruption, and what-if scenario analysis.
 *
 * OLD version showed device counts and alarms. This version shows:
 *   - Customer risk scores and counts per wire center
 *   - Revenue at risk (MRR) from copper services
 *   - Network disruption scores
 *   - Retirement cost vs scrap recovery
 *   - What-if analysis via Genie Agent
 *
 * All data is SYNTHETIC.
 */

// THIS FILE WAS FULLY REWRITTEN. See copper-map/client/src/mock/mockData.ts.bak
// for the old device-centric version if needed.

/**
 * LEGACY STUB — old mockData.ts content removed.
 * New retirement-impact data model below.
 *
 * mockData.ts
 * Mock data for the Copper Retirement Impact Map app.
 * Used when real data is unavailable (FIX-COORDINATES not yet run,
 * P2-H3 / P4-RISK not yet landed).
 *
 * All data is SYNTHETIC — for demo scaffolding only.
 */

// --- Feature flag: set to false to use live SQL queries ---
export const USE_MOCK_DATA = true;

// --- Types ---
export interface HexRiskRow {
  h3_cell: string;
  center_lat: number;
  center_lon: number;
  device_count: number;
  avg_risk_score: number;
  risk_tier: 'critical' | 'high' | 'medium' | 'low';
  alarm_count: number;
  critical_alarms: number;
  state: string;
}

export interface DeviceDetailRow {
  device_id: number;
  device_type: string;
  serial_number: string;
  device_status: string;
  installation_date: string;
  latitude: number;
  longitude: number;
  state: string;
  city: string;
  alarm_count: number;
  critical_alarms: number;
  major_alarms: number;
  risk_score: number;
}

export interface MapKPIs {
  total_copper_devices: number;
  cpe_count: number;
  ont_count: number;
  olt_count: number;
  patch_panel_count: number;
  total_alarms: number;
  critical_alarm_count: number;
  pct_critical_approx: number;
  states_with_copper: number;
  wire_centers_remaining: number;
}

export interface FilterOption {
  filter_type: string;
  filter_value: string;
  device_count: number;
}

// --- Mock hex cells (US state centroids as H3 approximations) ---
// Uses real LEGACY_STATES from synthetic_assets.py: CA, TX, FL, NY, OH, IL
const MOCK_HEX_CELLS: HexRiskRow[] = [
  // California — high copper density, aging plant
  { h3_cell: '892a100d2c3ffff', center_lat: 36.78, center_lon: -119.42, device_count: 487, avg_risk_score: 78, risk_tier: 'critical', alarm_count: 4210, critical_alarms: 1580, state: 'CA' },
  { h3_cell: '892a100d2c7ffff', center_lat: 34.05, center_lon: -118.24, device_count: 312, avg_risk_score: 65, risk_tier: 'high', alarm_count: 2890, critical_alarms: 890, state: 'CA' },
  { h3_cell: '892a100d2cbffff', center_lat: 37.77, center_lon: -122.42, device_count: 198, avg_risk_score: 52, risk_tier: 'high', alarm_count: 1650, critical_alarms: 420, state: 'CA' },
  // Texas — large footprint, mixed condition
  { h3_cell: '892a100d2cfffff', center_lat: 31.97, center_lon: -99.90, device_count: 423, avg_risk_score: 71, risk_tier: 'high', alarm_count: 3560, critical_alarms: 1120, state: 'TX' },
  { h3_cell: '892a100d2d3ffff', center_lat: 29.76, center_lon: -95.37, device_count: 278, avg_risk_score: 58, risk_tier: 'high', alarm_count: 2340, critical_alarms: 650, state: 'TX' },
  { h3_cell: '892a100d2d7ffff', center_lat: 32.78, center_lon: -96.80, device_count: 156, avg_risk_score: 42, risk_tier: 'medium', alarm_count: 1120, critical_alarms: 280, state: 'TX' },
  // Florida — coastal exposure, moisture risk
  { h3_cell: '892a100d2dbffff', center_lat: 27.66, center_lon: -81.52, device_count: 356, avg_risk_score: 82, risk_tier: 'critical', alarm_count: 3890, critical_alarms: 1890, state: 'FL' },
  { h3_cell: '892a100d2dfffff', center_lat: 25.76, center_lon: -80.19, device_count: 189, avg_risk_score: 73, risk_tier: 'high', alarm_count: 2010, critical_alarms: 780, state: 'FL' },
  // New York — dense urban, old infrastructure
  { h3_cell: '892a100d2e3ffff', center_lat: 40.71, center_lon: -74.01, device_count: 401, avg_risk_score: 88, risk_tier: 'critical', alarm_count: 4560, critical_alarms: 2100, state: 'NY' },
  { h3_cell: '892a100d2e7ffff', center_lat: 42.65, center_lon: -73.76, device_count: 134, avg_risk_score: 45, risk_tier: 'medium', alarm_count: 980, critical_alarms: 210, state: 'NY' },
  // Ohio — rust belt, aging
  { h3_cell: '892a100d2ebffff', center_lat: 40.42, center_lon: -82.91, device_count: 267, avg_risk_score: 62, risk_tier: 'high', alarm_count: 2230, critical_alarms: 670, state: 'OH' },
  { h3_cell: '892a100d2efffff', center_lat: 41.50, center_lon: -81.69, device_count: 178, avg_risk_score: 55, risk_tier: 'high', alarm_count: 1540, critical_alarms: 410, state: 'OH' },
  // Illinois — Chicago metro + downstate
  { h3_cell: '892a100d2f3ffff', center_lat: 41.88, center_lon: -87.63, device_count: 345, avg_risk_score: 76, risk_tier: 'critical', alarm_count: 3120, critical_alarms: 1340, state: 'IL' },
  { h3_cell: '892a100d2f7ffff', center_lat: 39.78, center_lon: -89.65, device_count: 112, avg_risk_score: 38, risk_tier: 'medium', alarm_count: 780, critical_alarms: 150, state: 'IL' },
];

// --- Mock KPIs (based on real device counts: 2,672 copper devices) ---
const MOCK_KPIS: MapKPIs = {
  total_copper_devices: 2672,
  cpe_count: 688,
  ont_count: 663,
  olt_count: 661,
  patch_panel_count: 660,
  total_alarms: 26943,
  critical_alarm_count: 9978,
  pct_critical_approx: 37.3,
  states_with_copper: 6,
  wire_centers_remaining: 200, // Placeholder — P0-DATAGEN-WIRECENTER target
};

// --- Mock filter options ---
const MOCK_FILTER_OPTIONS: FilterOption[] = [
  { filter_type: 'state', filter_value: 'CA', device_count: 997 },
  { filter_type: 'state', filter_value: 'TX', device_count: 857 },
  { filter_type: 'state', filter_value: 'FL', device_count: 545 },
  { filter_type: 'state', filter_value: 'NY', device_count: 535 },
  { filter_type: 'state', filter_value: 'OH', device_count: 445 },
  { filter_type: 'state', filter_value: 'IL', device_count: 457 },
  { filter_type: 'device_type', filter_value: 'cpe', device_count: 688 },
  { filter_type: 'device_type', filter_value: 'ont', device_count: 663 },
  { filter_type: 'device_type', filter_value: 'olt', device_count: 661 },
  { filter_type: 'device_type', filter_value: 'patch_panel', device_count: 660 },
  { filter_type: 'risk_tier', filter_value: 'critical', device_count: 0 },
  { filter_type: 'risk_tier', filter_value: 'high', device_count: 0 },
  { filter_type: 'risk_tier', filter_value: 'medium', device_count: 0 },
  { filter_type: 'risk_tier', filter_value: 'low', device_count: 0 },
];

// --- Mock device detail rows ---
const MOCK_DEVICES: DeviceDetailRow[] = [
  { device_id: 1001, device_type: 'cpe', serial_number: 'CPE-NYC-001', device_status: 'active', installation_date: '2008-03-15', latitude: 40.71, longitude: -74.01, state: 'NY', city: 'New York', alarm_count: 12, critical_alarms: 4, major_alarms: 5, risk_score: 92 },
  { device_id: 1002, device_type: 'ont', serial_number: 'ONT-NYC-002', device_status: 'active', installation_date: '2011-07-22', latitude: 40.73, longitude: -73.99, state: 'NY', city: 'New York', alarm_count: 8, critical_alarms: 2, major_alarms: 3, risk_score: 78 },
  { device_id: 1003, device_type: 'cpe', serial_number: 'CPE-MIA-001', device_status: 'degraded', installation_date: '2005-11-01', latitude: 25.76, longitude: -80.19, state: 'FL', city: 'Miami', alarm_count: 18, critical_alarms: 7, major_alarms: 6, risk_score: 95 },
  { device_id: 1004, device_type: 'olt', serial_number: 'OLT-CHI-001', device_status: 'active', installation_date: '2013-02-10', latitude: 41.88, longitude: -87.63, state: 'IL', city: 'Chicago', alarm_count: 6, critical_alarms: 1, major_alarms: 2, risk_score: 55 },
  { device_id: 1005, device_type: 'patch_panel', serial_number: 'PP-HOU-001', device_status: 'active', installation_date: '2009-09-30', latitude: 29.76, longitude: -95.37, state: 'TX', city: 'Houston', alarm_count: 14, critical_alarms: 5, major_alarms: 4, risk_score: 82 },
];

// --- Getters ---

export function getMockHexCells(filters?: {
  state?: string;
  riskTier?: string;
  deviceType?: string;
}): HexRiskRow[] {
  let cells = [...MOCK_HEX_CELLS];
  if (filters?.state) {
    cells = cells.filter((c) => c.state === filters.state);
  }
  if (filters?.riskTier) {
    cells = cells.filter((c) => c.risk_tier === filters.riskTier);
  }
  return cells;
}

export function getMockKPIs(): MapKPIs {
  return { ...MOCK_KPIS };
}

export function getMockFilterOptions(): FilterOption[] {
  return [...MOCK_FILTER_OPTIONS];
}

export function getMockDevices(h3Cell?: string): DeviceDetailRow[] {
  if (!h3Cell) return [...MOCK_DEVICES];
  // In mock mode, return all devices since we can't filter by real H3
  return [...MOCK_DEVICES];
}

// --- Risk tier color mapping ---
export const RISK_COLORS: Record<string, string> = {
  critical: '#EB1600',   // Databricks red
  high: '#FF8C00',       // Orange
  medium: '#FFD700',     // Gold/yellow
  low: '#40d1f5',        // Databricks cyan
};

export const RISK_TIERS = ['critical', 'high', 'medium', 'low'] as const;
