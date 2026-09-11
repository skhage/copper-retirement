/**
 * mockData.ts
 * Mock data for the Commodity & Workforce Dashboard (P7-COMMODITY).
 * Provides realistic copper commodity prices, recovery records, contractor
 * performance data, and FX rates for the mock demo.
 *
 * Feature flag: set USE_MOCK_DATA=false in environment to switch to live SQL.
 * Mock data is modeled after SPEC_commodity_price.md and SPEC_contractor_performance.md.
 *
 * All data is SYNTHETIC.
 */

export const USE_MOCK_DATA = true;

// --- Types ---

export interface CopperPrice {
  date: string;
  spot_usd_lb: number;
  forward_3m_usd_lb: number;
  forward_15m_usd_lb: number;
  volume_lots: number;
  volatility_30d: number;
}

export interface ForecastPoint {
  month_offset: number;
  forecast_price_usd_lb: number;
  lower_bound: number;
  upper_bound: number;
  confidence: number;
}

export interface RecoveryRecord {
  recovery_id: string;
  project_name: string;
  wire_center: string;
  state: string;
  scrap_grade: string;
  weight_lbs: number;
  gross_value_usd: number;
  net_value_usd: number;
  recovery_date: string;
  cable_gauge_awg: number;
  cable_type: string;
  decommission_work_id: number;
}

export interface Contractor {
  contractor_id: number;
  name: string;
  type: string;
  state_coverage: string[];
  safety_score: number;
  osha_recordable_rate: number;
  sla_met_pct: number;
  completion_rate_pct: number;
  incident_count: number;
  overall_rating: number;
  active_projects: number;
  total_work_orders: number;
  avg_resolution_hours: number;
}

export interface FxRate {
  from_currency: string;
  to_currency: string;
  date: string;
  rate: number;
}

export interface SellHoldRecommendation {
  recommendation: 'SELL' | 'HOLD' | 'ACCUMULATE';
  confidence: number;
  current_spot: number;
  forecast_3m: number;
  forecast_12m: number;
  reasoning: string;
  updated_at: string;
}

// --- Mock KPIs ---

export const mockKPIs = {
  current_spot_usd_lb: 4.32,
  spot_30d_change_pct: 3.8,
  total_recovered_lbs: 1_127_400,
  total_scrap_value_usd: 3_312_000,
  net_recovery_value_usd: 2_814_000,
  active_contractors: 1_254,
  avg_safety_score: 76.4,
  decommission_projects: 847,
};

// --- Mock Price History (monthly 2018-2025, simplified) ---

const generatePriceHistory = (): CopperPrice[] => {
  const prices: CopperPrice[] = [];
  const startYear = 2018;
  const endYear = 2025;

  // Regime walk: $2.60 (2018) -> dip to $2.10 (COVID 2020-Q2) -> rally to $4.70 (2022) -> settle $3.80-4.40 (2023-2025)
  const regimePoints: [number, number][] = [
    [2018.0, 3.10], [2018.5, 2.75], [2019.0, 2.65], [2019.5, 2.60],
    [2020.0, 2.55], [2020.25, 2.10], [2020.5, 2.85], [2020.75, 3.20],
    [2021.0, 3.55], [2021.5, 4.30], [2022.0, 4.55], [2022.25, 4.70],
    [2022.5, 3.50], [2022.75, 3.60], [2023.0, 3.85], [2023.5, 3.90],
    [2024.0, 4.05], [2024.5, 4.25], [2025.0, 4.30], [2025.5, 4.32],
  ];

  const interpolate = (t: number): number => {
    for (let i = 0; i < regimePoints.length - 1; i++) {
      const [t0, p0] = regimePoints[i];
      const [t1, p1] = regimePoints[i + 1];
      if (t >= t0 && t <= t1) {
        const frac = (t - t0) / (t1 - t0);
        return p0 + frac * (p1 - p0);
      }
    }
    return regimePoints[regimePoints.length - 1][1];
  };

  for (let y = startYear; y <= endYear; y++) {
    for (let m = 0; m < 12; m++) {
      const t = y + m / 12;
      const spot = interpolate(t) + (Math.random() - 0.5) * 0.15;
      const contango = 0.03 + Math.random() * 0.04; // 3-7 cent contango
      prices.push({
        date: `${y}-${String(m + 1).padStart(2, '0')}-15`,
        spot_usd_lb: Math.round(spot * 100) / 100,
        forward_3m_usd_lb: Math.round((spot + contango) * 100) / 100,
        forward_15m_usd_lb: Math.round((spot + contango * 3.5) * 100) / 100,
        volume_lots: Math.floor(15000 + Math.random() * 10000),
        volatility_30d: Math.round((12 + Math.random() * 18) * 10) / 10,
      });
    }
  }
  return prices;
};

export const mockPriceHistory: CopperPrice[] = generatePriceHistory();

// --- Mock Forecast (12 months from P4-COMMODITY model) ---

export const mockForecast: ForecastPoint[] = Array.from({ length: 12 }, (_, i) => {
  const month = i + 1;
  const basePrice = 4.32;
  const trend = 0.025 * month;
  return {
    month_offset: month,
    forecast_price_usd_lb: Math.round((basePrice + trend) * 100) / 100,
    lower_bound: Math.round((basePrice + trend - 0.30 - 0.02 * month) * 100) / 100,
    upper_bound: Math.round((basePrice + trend + 0.30 + 0.02 * month) * 100) / 100,
    confidence: Math.round((0.95 - 0.015 * month) * 100) / 100,
  };
});

// --- Mock Sell/Hold Recommendation ---

export const mockRecommendation: SellHoldRecommendation = {
  recommendation: 'SELL',
  confidence: 0.78,
  current_spot: 4.32,
  forecast_3m: 4.40,
  forecast_12m: 4.62,
  reasoning:
    'Current spot price ($4.32/lb) is above 3-year moving average ($3.85/lb). ' +
    'Forward curve in contango suggests near-term price pressure easing. ' +
    'Recovered copper inventory at 1.1M lbs — recommend staged sell-off of ' +
    'bare_bright and #1_insulated grades within 90 days to lock in premium.',
  updated_at: '2025-12-15T14:30:00Z',
};

// --- Mock Recovery Records ---

export const mockRecoveryRecords: RecoveryRecord[] = [
  { recovery_id: 'REC-500001', project_name: 'Denver-CO Downtown Decom', wire_center: 'CO-DEN-001', state: 'CO', scrap_grade: 'bare_bright', weight_lbs: 12400, gross_value_usd: 52080, net_value_usd: 46872, recovery_date: '2025-11-20', cable_gauge_awg: 24, cable_type: 'aerial_drop', decommission_work_id: 50001 },
  { recovery_id: 'REC-500002', project_name: 'Minneapolis-MN North Decom', wire_center: 'MN-MPL-002', state: 'MN', scrap_grade: '#1_insulated', weight_lbs: 28600, gross_value_usd: 94380, net_value_usd: 75504, recovery_date: '2025-10-15', cable_gauge_awg: 22, cable_type: 'buried_distribution', decommission_work_id: 50002 },
  { recovery_id: 'REC-500003', project_name: 'Seattle-WA Eastside Decom', wire_center: 'WA-SEA-003', state: 'WA', scrap_grade: 'telecom_cable', weight_lbs: 45200, gross_value_usd: 108480, net_value_usd: 75936, recovery_date: '2025-09-08', cable_gauge_awg: 26, cable_type: 'underground_feeder', decommission_work_id: 50003 },
  { recovery_id: 'REC-500004', project_name: 'Portland-OR Central Decom', wire_center: 'OR-PDX-001', state: 'OR', scrap_grade: '#2_insulated', weight_lbs: 19800, gross_value_usd: 47520, net_value_usd: 33264, recovery_date: '2025-08-22', cable_gauge_awg: 19, cable_type: 'aerial_feeder', decommission_work_id: 50004 },
  { recovery_id: 'REC-500005', project_name: 'Phoenix-AZ Metro Decom', wire_center: 'AZ-PHX-001', state: 'AZ', scrap_grade: 'bare_bright', weight_lbs: 8900, gross_value_usd: 37380, net_value_usd: 33642, recovery_date: '2025-12-01', cable_gauge_awg: 24, cable_type: 'aerial_drop', decommission_work_id: 50005 },
  { recovery_id: 'REC-500006', project_name: 'Boise-ID Central Decom', wire_center: 'ID-BOI-001', state: 'ID', scrap_grade: 'mixed_scrap', weight_lbs: 31500, gross_value_usd: 56700, net_value_usd: 34020, recovery_date: '2025-07-10', cable_gauge_awg: 26, cable_type: 'buried_distribution', decommission_work_id: 50006 },
  { recovery_id: 'REC-500007', project_name: 'Colorado Springs-CO Decom', wire_center: 'CO-COS-002', state: 'CO', scrap_grade: '#1_insulated', weight_lbs: 22100, gross_value_usd: 72930, net_value_usd: 58344, recovery_date: '2025-11-05', cable_gauge_awg: 22, cable_type: 'underground_feeder', decommission_work_id: 50007 },
  { recovery_id: 'REC-500008', project_name: 'Tacoma-WA Decom', wire_center: 'WA-TAC-002', state: 'WA', scrap_grade: 'telecom_cable', weight_lbs: 38700, gross_value_usd: 92880, net_value_usd: 65016, recovery_date: '2025-06-18', cable_gauge_awg: 24, cable_type: 'aerial_feeder', decommission_work_id: 50008 },
];

// --- Mock Contractors ---

export const mockContractors: Contractor[] = [
  { contractor_id: 10001, name: 'Rocky Mountain Telecom Services', type: 'cable_removal', state_coverage: ['CO', 'WY', 'UT'], safety_score: 92, osha_recordable_rate: 1.2, sla_met_pct: 94, completion_rate_pct: 97, incident_count: 2, overall_rating: 4.6, active_projects: 8, total_work_orders: 156, avg_resolution_hours: 18.5 },
  { contractor_id: 10045, name: 'Northwest Line Construction', type: 'fiber_installation', state_coverage: ['WA', 'OR', 'ID'], safety_score: 88, osha_recordable_rate: 1.8, sla_met_pct: 91, completion_rate_pct: 95, incident_count: 3, overall_rating: 4.3, active_projects: 12, total_work_orders: 234, avg_resolution_hours: 22.0 },
  { contractor_id: 10089, name: 'Desert Utilities Corp', type: 'equipment_decommission', state_coverage: ['AZ', 'NM', 'NV'], safety_score: 85, osha_recordable_rate: 2.1, sla_met_pct: 87, completion_rate_pct: 93, incident_count: 4, overall_rating: 4.0, active_projects: 6, total_work_orders: 98, avg_resolution_hours: 24.5 },
  { contractor_id: 10112, name: 'Great Plains Infrastructure', type: 'cable_removal', state_coverage: ['MN', 'ND', 'SD', 'WI'], safety_score: 91, osha_recordable_rate: 1.3, sla_met_pct: 93, completion_rate_pct: 96, incident_count: 1, overall_rating: 4.5, active_projects: 10, total_work_orders: 189, avg_resolution_hours: 19.2 },
  { contractor_id: 10156, name: 'Pacific Copper Salvage', type: 'scrap_processing', state_coverage: ['WA', 'OR', 'CA'], safety_score: 78, osha_recordable_rate: 2.8, sla_met_pct: 82, completion_rate_pct: 90, incident_count: 6, overall_rating: 3.5, active_projects: 4, total_work_orders: 67, avg_resolution_hours: 32.0 },
  { contractor_id: 10198, name: 'Mountain West Excavation', type: 'trenching', state_coverage: ['CO', 'ID', 'MT'], safety_score: 82, osha_recordable_rate: 2.4, sla_met_pct: 85, completion_rate_pct: 91, incident_count: 5, overall_rating: 3.8, active_projects: 7, total_work_orders: 112, avg_resolution_hours: 26.8 },
];

// --- Mock FX Rates (last 5 trading days for context) ---

export const mockFxRates: FxRate[] = [
  { from_currency: 'EUR', to_currency: 'USD', date: '2025-12-15', rate: 1.0524 },
  { from_currency: 'GBP', to_currency: 'USD', date: '2025-12-15', rate: 1.2631 },
  { from_currency: 'CAD', to_currency: 'USD', date: '2025-12-15', rate: 0.7189 },
  { from_currency: 'AUD', to_currency: 'USD', date: '2025-12-15', rate: 0.6342 },
  { from_currency: 'JPY', to_currency: 'USD', date: '2025-12-15', rate: 0.0065 },
];

// --- Scrap Grade Reference ---

export const SCRAP_GRADES: Record<string, { label: string; lme_discount_pct: string; color: string }> = {
  bare_bright: { label: 'Bare Bright', lme_discount_pct: '90-95%', color: '#16a34a' },
  '#1_insulated': { label: '#1 Insulated', lme_discount_pct: '80-90%', color: '#2563eb' },
  '#2_insulated': { label: '#2 Insulated', lme_discount_pct: '65-80%', color: '#7c3aed' },
  telecom_cable: { label: 'Telecom Cable', lme_discount_pct: '50-70%', color: '#d97706' },
  mixed_scrap: { label: 'Mixed Scrap', lme_discount_pct: '40-55%', color: '#6b7280' },
};
