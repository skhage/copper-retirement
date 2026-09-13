/**
 * retirementData.ts
 * Retirement-impact data model for the Copper Retirement Impact Map.
 * CEO directive: this app is about WHERE to dig copper out and WHAT HAPPENS.
 * All data is SYNTHETIC.
 */

export const USE_MOCK_DATA = true;

export interface WireCenterImpact {
  wire_center_id: string;
  wire_center_name: string;
  h3_cell: string;
  center_lat: number;
  center_lon: number;
  state: string;
  customers_affected: number;
  residential_customers: number;
  business_customers: number;
  customers_contract_locked: number;
  churn_risk_score: number;
  revenue_at_risk_mrr: number;
  revenue_voice_mrr: number;
  revenue_broadband_mrr: number;
  revenue_fixed_line_mrr: number;
  copper_devices: number;
  services_affected: number;
  network_disruption_score: number;
  fiber_ready_pct: number;
  active_alarms: number;
  retirement_cost_usd: number;
  scrap_recovery_usd: number;
  net_cost_usd: number;
  estimated_duration_weeks: number;
  retirement_priority: number;
  priority_tier: 'retire-now' | 'plan-next' | 'evaluate' | 'defer';
  status: 'not-started' | 'planning' | 'in-progress' | 'completed';
  regulatory_notice_required: boolean;
  notice_period_days: number;
  has_active_dig_incident: boolean;
}

export interface RetirementKPIs {
  total_revenue_at_risk_mrr: number;
  total_customers_on_copper: number;
  wire_centers_to_retire: number;
  total_services_affected: number;
  avg_retirement_cost: number;
  total_net_cost: number;
  fiber_ready_pct_avg: number;
  contract_locked_customers: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: string;
  impact_summary?: {
    total_customers_affected: number;
    total_revenue_impact_mrr: number;
    total_cost: number;
    net_cost: number;
    services_disrupted: number;
    recommendation: string;
  };
}

export interface Filters {
  state: string;
  priorityTier: string;
}

export const PRIORITY_COLORS: Record<string, string> = {
  'retire-now': '#FF3621',
  'plan-next': '#FF8C69',
  'evaluate': '#FFD700',
  'defer': '#60A5FA',
};

export const PRIORITY_TIERS = ['retire-now', 'plan-next', 'evaluate', 'defer'] as const;

export const SUGGESTED_QUESTIONS: string[] = [
  'What if we retire all copper in Colorado first?',
  'Show me the revenue impact of retiring Denver Downtown',
  'Which wire centers can we retire with zero contract-locked customers?',
  'What is the total cost to retire all retire-now wire centers?',
  'How many customers are affected if we retire copper in Idaho?',
];

const WCS: WireCenterImpact[] = [
  { wire_center_id: 'CO-DEN-001', wire_center_name: 'Denver Downtown', h3_cell: '892a100d2c3ffff', center_lat: 39.74, center_lon: -104.99, state: 'CO', customers_affected: 231, residential_customers: 178, business_customers: 53, customers_contract_locked: 18, churn_risk_score: 32, revenue_at_risk_mrr: 46200, revenue_voice_mrr: 12800, revenue_broadband_mrr: 22400, revenue_fixed_line_mrr: 11000, copper_devices: 144, services_affected: 389, network_disruption_score: 45, fiber_ready_pct: 82, active_alarms: 312, retirement_cost_usd: 812000, scrap_recovery_usd: 198000, net_cost_usd: 614000, estimated_duration_weeks: 16, retirement_priority: 88, priority_tier: 'retire-now', status: 'planning', regulatory_notice_required: true, notice_period_days: 180, has_active_dig_incident: false },
  { wire_center_id: 'CO-COS-002', wire_center_name: 'Colorado Springs', h3_cell: '892a100d2c7ffff', center_lat: 38.83, center_lon: -104.82, state: 'CO', customers_affected: 156, residential_customers: 128, business_customers: 28, customers_contract_locked: 8, churn_risk_score: 28, revenue_at_risk_mrr: 28400, revenue_voice_mrr: 8200, revenue_broadband_mrr: 13600, revenue_fixed_line_mrr: 6600, copper_devices: 98, services_affected: 245, network_disruption_score: 35, fiber_ready_pct: 74, active_alarms: 186, retirement_cost_usd: 524000, scrap_recovery_usd: 142000, net_cost_usd: 382000, estimated_duration_weeks: 12, retirement_priority: 76, priority_tier: 'plan-next', status: 'not-started', regulatory_notice_required: true, notice_period_days: 180, has_active_dig_incident: false },
  { wire_center_id: 'CO-BOU-003', wire_center_name: 'Boulder West', h3_cell: '892a100d2cbffff', center_lat: 40.01, center_lon: -105.27, state: 'CO', customers_affected: 89, residential_customers: 72, business_customers: 17, customers_contract_locked: 4, churn_risk_score: 22, revenue_at_risk_mrr: 14200, revenue_voice_mrr: 4100, revenue_broadband_mrr: 6800, revenue_fixed_line_mrr: 3300, copper_devices: 52, services_affected: 134, network_disruption_score: 22, fiber_ready_pct: 91, active_alarms: 78, retirement_cost_usd: 286000, scrap_recovery_usd: 88000, net_cost_usd: 198000, estimated_duration_weeks: 8, retirement_priority: 92, priority_tier: 'retire-now', status: 'not-started', regulatory_notice_required: true, notice_period_days: 180, has_active_dig_incident: false },
  { wire_center_id: 'MN-MPL-001', wire_center_name: 'Minneapolis North', h3_cell: '892a100d2cfffff', center_lat: 44.98, center_lon: -93.27, state: 'MN', customers_affected: 198, residential_customers: 156, business_customers: 42, customers_contract_locked: 22, churn_risk_score: 41, revenue_at_risk_mrr: 38600, revenue_voice_mrr: 11200, revenue_broadband_mrr: 18200, revenue_fixed_line_mrr: 9200, copper_devices: 127, services_affected: 334, network_disruption_score: 52, fiber_ready_pct: 68, active_alarms: 278, retirement_cost_usd: 698000, scrap_recovery_usd: 176000, net_cost_usd: 522000, estimated_duration_weeks: 14, retirement_priority: 72, priority_tier: 'plan-next', status: 'not-started', regulatory_notice_required: true, notice_period_days: 270, has_active_dig_incident: false },
  { wire_center_id: 'WA-SEA-001', wire_center_name: 'Seattle Eastside', h3_cell: '892a100d2d7ffff', center_lat: 47.61, center_lon: -122.33, state: 'WA', customers_affected: 212, residential_customers: 164, business_customers: 48, customers_contract_locked: 28, churn_risk_score: 48, revenue_at_risk_mrr: 52400, revenue_voice_mrr: 14200, revenue_broadband_mrr: 26800, revenue_fixed_line_mrr: 11400, copper_devices: 138, services_affected: 412, network_disruption_score: 62, fiber_ready_pct: 58, active_alarms: 346, retirement_cost_usd: 924000, scrap_recovery_usd: 218000, net_cost_usd: 706000, estimated_duration_weeks: 18, retirement_priority: 58, priority_tier: 'evaluate', status: 'not-started', regulatory_notice_required: true, notice_period_days: 365, has_active_dig_incident: true },
  { wire_center_id: 'WA-TAC-002', wire_center_name: 'Tacoma Central', h3_cell: '892a100d2dbffff', center_lat: 47.25, center_lon: -122.44, state: 'WA', customers_affected: 108, residential_customers: 88, business_customers: 20, customers_contract_locked: 6, churn_risk_score: 25, revenue_at_risk_mrr: 18600, revenue_voice_mrr: 5400, revenue_broadband_mrr: 8800, revenue_fixed_line_mrr: 4400, copper_devices: 64, services_affected: 172, network_disruption_score: 28, fiber_ready_pct: 85, active_alarms: 92, retirement_cost_usd: 348000, scrap_recovery_usd: 96000, net_cost_usd: 252000, estimated_duration_weeks: 8, retirement_priority: 84, priority_tier: 'retire-now', status: 'not-started', regulatory_notice_required: true, notice_period_days: 365, has_active_dig_incident: false },
  { wire_center_id: 'OR-PDX-001', wire_center_name: 'Portland Central', h3_cell: '892a100d2dfffff', center_lat: 45.52, center_lon: -122.68, state: 'OR', customers_affected: 176, residential_customers: 142, business_customers: 34, customers_contract_locked: 14, churn_risk_score: 38, revenue_at_risk_mrr: 34200, revenue_voice_mrr: 9800, revenue_broadband_mrr: 16400, revenue_fixed_line_mrr: 8000, copper_devices: 112, services_affected: 296, network_disruption_score: 42, fiber_ready_pct: 76, active_alarms: 224, retirement_cost_usd: 612000, scrap_recovery_usd: 158000, net_cost_usd: 454000, estimated_duration_weeks: 12, retirement_priority: 74, priority_tier: 'plan-next', status: 'not-started', regulatory_notice_required: true, notice_period_days: 210, has_active_dig_incident: false },
  { wire_center_id: 'AZ-PHX-001', wire_center_name: 'Phoenix Metro', h3_cell: '892a100d2e3ffff', center_lat: 33.45, center_lon: -112.07, state: 'AZ', customers_affected: 187, residential_customers: 148, business_customers: 39, customers_contract_locked: 10, churn_risk_score: 30, revenue_at_risk_mrr: 32800, revenue_voice_mrr: 9200, revenue_broadband_mrr: 15800, revenue_fixed_line_mrr: 7800, copper_devices: 118, services_affected: 312, network_disruption_score: 34, fiber_ready_pct: 79, active_alarms: 198, retirement_cost_usd: 548000, scrap_recovery_usd: 164000, net_cost_usd: 384000, estimated_duration_weeks: 10, retirement_priority: 82, priority_tier: 'retire-now', status: 'planning', regulatory_notice_required: true, notice_period_days: 180, has_active_dig_incident: false },
  { wire_center_id: 'AZ-TUS-002', wire_center_name: 'Tucson South', h3_cell: '892a100d2e7ffff', center_lat: 32.22, center_lon: -110.97, state: 'AZ', customers_affected: 78, residential_customers: 64, business_customers: 14, customers_contract_locked: 3, churn_risk_score: 18, revenue_at_risk_mrr: 11400, revenue_voice_mrr: 3200, revenue_broadband_mrr: 5600, revenue_fixed_line_mrr: 2600, copper_devices: 42, services_affected: 118, network_disruption_score: 18, fiber_ready_pct: 88, active_alarms: 56, retirement_cost_usd: 218000, scrap_recovery_usd: 72000, net_cost_usd: 146000, estimated_duration_weeks: 6, retirement_priority: 90, priority_tier: 'retire-now', status: 'not-started', regulatory_notice_required: true, notice_period_days: 180, has_active_dig_incident: false },
  { wire_center_id: 'ID-BOI-001', wire_center_name: 'Boise Central', h3_cell: '892a100d2ebffff', center_lat: 43.62, center_lon: -116.21, state: 'ID', customers_affected: 92, residential_customers: 76, business_customers: 16, customers_contract_locked: 4, churn_risk_score: 20, revenue_at_risk_mrr: 14800, revenue_voice_mrr: 4200, revenue_broadband_mrr: 7200, revenue_fixed_line_mrr: 3400, copper_devices: 56, services_affected: 146, network_disruption_score: 20, fiber_ready_pct: 86, active_alarms: 82, retirement_cost_usd: 296000, scrap_recovery_usd: 92000, net_cost_usd: 204000, estimated_duration_weeks: 8, retirement_priority: 86, priority_tier: 'retire-now', status: 'not-started', regulatory_notice_required: true, notice_period_days: 150, has_active_dig_incident: false },
  { wire_center_id: 'ID-TWF-002', wire_center_name: 'Twin Falls', h3_cell: '892a100d2efffff', center_lat: 42.56, center_lon: -114.46, state: 'ID', customers_affected: 45, residential_customers: 38, business_customers: 7, customers_contract_locked: 1, churn_risk_score: 14, revenue_at_risk_mrr: 6200, revenue_voice_mrr: 1800, revenue_broadband_mrr: 2800, revenue_fixed_line_mrr: 1600, copper_devices: 24, services_affected: 68, network_disruption_score: 12, fiber_ready_pct: 94, active_alarms: 28, retirement_cost_usd: 108000, scrap_recovery_usd: 38000, net_cost_usd: 70000, estimated_duration_weeks: 4, retirement_priority: 95, priority_tier: 'retire-now', status: 'not-started', regulatory_notice_required: true, notice_period_days: 150, has_active_dig_incident: false },
];

const MOCK_KPIS: RetirementKPIs = {
  total_revenue_at_risk_mrr: WCS.reduce((s, w) => s + w.revenue_at_risk_mrr, 0),
  total_customers_on_copper: WCS.reduce((s, w) => s + w.customers_affected, 0),
  wire_centers_to_retire: WCS.length,
  total_services_affected: WCS.reduce((s, w) => s + w.services_affected, 0),
  avg_retirement_cost: Math.round(WCS.reduce((s, w) => s + w.retirement_cost_usd, 0) / WCS.length),
  total_net_cost: WCS.reduce((s, w) => s + w.net_cost_usd, 0),
  fiber_ready_pct_avg: Math.round(WCS.reduce((s, w) => s + w.fiber_ready_pct, 0) / WCS.length),
  contract_locked_customers: WCS.reduce((s, w) => s + w.customers_contract_locked, 0),
};

export function generateMockResponse(question: string): ChatMessage {
  const q = question.toLowerCase();
  if (q.includes('colorado')) {
    const co = WCS.filter((w) => w.state === 'CO');
    return { id: `a-${Date.now()}`, role: 'agent', content: `Retiring all copper in **Colorado** (${co.length} wire centers) affects **${co.reduce((s, w) => s + w.customers_affected, 0)} customers** with **$${(co.reduce((s, w) => s + w.revenue_at_risk_mrr, 0) / 1000).toFixed(1)}K MRR** at risk. ${co.reduce((s, w) => s + w.customers_contract_locked, 0)} customers are contract-locked. Net cost: $${(co.reduce((s, w) => s + w.net_cost_usd, 0) / 1000000).toFixed(2)}M. **Recommendation:** Start with Boulder West (priority 92, 91% fiber-ready, lowest disruption).`, timestamp: new Date().toISOString(), impact_summary: { total_customers_affected: co.reduce((s, w) => s + w.customers_affected, 0), total_revenue_impact_mrr: co.reduce((s, w) => s + w.revenue_at_risk_mrr, 0), total_cost: co.reduce((s, w) => s + w.retirement_cost_usd, 0), net_cost: co.reduce((s, w) => s + w.net_cost_usd, 0), services_disrupted: co.reduce((s, w) => s + w.services_affected, 0), recommendation: 'Start with Boulder West, then Denver Downtown, then Colorado Springs.' } };
  }
  if (q.includes('denver')) {
    const d = WCS.find((w) => w.wire_center_id === 'CO-DEN-001')!;
    return { id: `a-${Date.now()}`, role: 'agent', content: `**Denver Downtown**: ${d.customers_affected} customers (${d.business_customers} business, ${d.residential_customers} residential). Revenue: **$${(d.revenue_at_risk_mrr / 1000).toFixed(1)}K MRR**. Network disruption: ${d.network_disruption_score}/100. ${d.customers_contract_locked} contract-locked. Cost: $${(d.retirement_cost_usd / 1000).toFixed(0)}K, scrap recovery: $${(d.scrap_recovery_usd / 1000).toFixed(0)}K.`, timestamp: new Date().toISOString(), impact_summary: { total_customers_affected: d.customers_affected, total_revenue_impact_mrr: d.revenue_at_risk_mrr, total_cost: d.retirement_cost_usd, net_cost: d.net_cost_usd, services_disrupted: d.services_affected, recommendation: 'Strong retire-now candidate. Begin 180-day regulatory notice. Prioritize 53 business customers first.' } };
  }
  return { id: `a-${Date.now()}`, role: 'agent', content: `Across ${WCS.length} wire centers: **${MOCK_KPIS.total_customers_on_copper} customers** on copper, **$${(MOCK_KPIS.total_revenue_at_risk_mrr / 1000).toFixed(0)}K MRR** at risk. ${WCS.filter((w) => w.priority_tier === 'retire-now').length} retire-now candidates with high fiber readiness. Ask about a specific state or wire center.`, timestamp: new Date().toISOString() };
}

export function getMockWireCenters(filters?: Partial<Filters>): WireCenterImpact[] {
  let wcs = [...WCS];
  if (filters?.state && filters.state !== 'all') wcs = wcs.filter((w) => w.state === filters.state);
  if (filters?.priorityTier && filters.priorityTier !== 'all') wcs = wcs.filter((w) => w.priority_tier === filters.priorityTier);
  return wcs;
}

export function getMockKPIs(): RetirementKPIs { return { ...MOCK_KPIS }; }
export function getMockWireCenter(id: string) { return WCS.find((w) => w.wire_center_id === id); }

/** Converged KPI set (BRAND_GUIDE §6 — used by SummaryKPIs and app.py) */
export interface ConvergedKPIs {
  copper_devices: number;
  critical_risk_pct: number;
  revenue_at_risk_mrr: number;
  states_count: number;
  services_affected: number;
}

export function getConvergedKPIs(): ConvergedKPIs {
  const retireNow = WCS.filter((w) => w.priority_tier === 'retire-now').length;
  return {
    copper_devices: WCS.reduce((s, w) => s + w.copper_devices, 0),
    critical_risk_pct: Math.round((retireNow / WCS.length) * 1000) / 10,
    revenue_at_risk_mrr: MOCK_KPIS.total_revenue_at_risk_mrr,
    states_count: new Set(WCS.map((w) => w.state)).size,
    services_affected: MOCK_KPIS.total_services_affected,
  };
}
