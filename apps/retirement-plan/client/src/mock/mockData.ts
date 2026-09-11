/**
 * mockData.ts
 * Mock data for the Retirement Plan Tracker (P7-PLAN).
 * Simulates P4-SEQ optimizer output: wire-center retirement waves 2026–2029.
 *
 * Data represents ~25 wire centers across 6 LEGACY_STATES with realistic:
 * - Wave assignments (1–8)
 * - Quarterly schedule dates (2026-Q2 through 2029-Q4)
 * - Migration costs, revenue-at-risk, scrap recovery
 * - Constraint flags (contract-locked, regulatory pending, crew capacity)
 * - Customer counts and device counts from real table distributions
 *
 * Feature flag: USE_MOCK_DATA=true toggles between mock and live SQL.
 */

export const USE_MOCK_DATA = true;

// --- Types ---

export type WaveStatus =
  | 'planned'
  | 'in_progress'
  | 'fiber_provisioned'
  | 'cutover'
  | 'completed'
  | 'on_hold'
  | 'deferred';

export type ConstraintType =
  | 'contract_locked'
  | 'regulatory_notice_pending'
  | 'crew_capacity_constrained'
  | 'revrec_locked'
  | 'none';

export interface WireCenterPlan {
  wire_center_id: string;
  wire_center_name: string;
  state: string;
  wave: number;
  scheduled_start: string;
  scheduled_end: string;
  status: WaveStatus;
  customers_affected: number;
  copper_devices: number;
  migration_cost_usd: number;
  revenue_at_risk_mrr: number;
  scrap_recovery_usd: number;
  net_savings_usd: number;
  completion_pct: number;
  constraint: ConstraintType;
  constraint_detail: string;
  assigned_crew: string;
  priority_score: number;
}

export interface MilestoneItem {
  milestone_id: string;
  wire_center_id: string;
  name: string;
  type: 'regulatory' | 'financial' | 'technical' | 'operational' | 'phase_gate';
  planned_date: string;
  actual_date: string | null;
  status: 'achieved' | 'in_progress' | 'pending' | 'at_risk' | 'missed';
  critical_path: boolean;
}

export interface ScenarioRun {
  scenario_id: string;
  name: string;
  created_at: string;
  objective: string;
  total_cost: number;
  total_duration_months: number;
  waves_used: number;
  risk_score: number;
  status: 'active' | 'draft' | 'archived';
}

export interface PlanKPIData {
  total_wire_centers: number;
  pct_planned: number;
  pct_in_flight: number;
  pct_completed: number;
  total_budget_allocated: number;
  total_budget_remaining: number;
  customers_migrated: number;
  customers_remaining: number;
}

// --- Mock Wire Center Plan Data ---

export const mockWireCenters: WireCenterPlan[] = [
  // Wave 1 — Q2 2026 (high-risk, low-complexity COs)
  {
    wire_center_id: 'WC-CO-001', wire_center_name: 'Denver-Downtown', state: 'CO',
    wave: 1, scheduled_start: '2026-04-01', scheduled_end: '2026-06-30',
    status: 'in_progress', customers_affected: 142, copper_devices: 89,
    migration_cost_usd: 485000, revenue_at_risk_mrr: 28400,
    scrap_recovery_usd: 32000, net_savings_usd: 156000,
    completion_pct: 45, constraint: 'none', constraint_detail: '',
    assigned_crew: 'Mountain West Fiber Co', priority_score: 92,
  },
  {
    wire_center_id: 'WC-CO-002', wire_center_name: 'Aurora-East', state: 'CO',
    wave: 1, scheduled_start: '2026-04-15', scheduled_end: '2026-07-15',
    status: 'in_progress', customers_affected: 98, copper_devices: 61,
    migration_cost_usd: 342000, revenue_at_risk_mrr: 19600,
    scrap_recovery_usd: 22000, net_savings_usd: 108000,
    completion_pct: 32, constraint: 'none', constraint_detail: '',
    assigned_crew: 'Mountain West Fiber Co', priority_score: 88,
  },
  {
    wire_center_id: 'WC-MN-001', wire_center_name: 'Minneapolis-North', state: 'MN',
    wave: 1, scheduled_start: '2026-05-01', scheduled_end: '2026-08-31',
    status: 'planned', customers_affected: 167, copper_devices: 104,
    migration_cost_usd: 578000, revenue_at_risk_mrr: 33400,
    scrap_recovery_usd: 38000, net_savings_usd: 189000,
    completion_pct: 0, constraint: 'regulatory_notice_pending',
    constraint_detail: 'MN PUC 270-day notice: filed 2026-03-01, clears 2026-11-26',
    assigned_crew: 'Northland Connectivity', priority_score: 85,
  },

  // Wave 2 — Q3 2026
  {
    wire_center_id: 'WC-WA-001', wire_center_name: 'Seattle-Eastside', state: 'WA',
    wave: 2, scheduled_start: '2026-07-01', scheduled_end: '2026-09-30',
    status: 'planned', customers_affected: 203, copper_devices: 127,
    migration_cost_usd: 712000, revenue_at_risk_mrr: 40600,
    scrap_recovery_usd: 46000, net_savings_usd: 231000,
    completion_pct: 0, constraint: 'none', constraint_detail: '',
    assigned_crew: 'Pacific Northwest Telecom', priority_score: 81,
  },
  {
    wire_center_id: 'WC-OR-001', wire_center_name: 'Portland-Central', state: 'OR',
    wave: 2, scheduled_start: '2026-07-15', scheduled_end: '2026-10-15',
    status: 'planned', customers_affected: 156, copper_devices: 97,
    migration_cost_usd: 534000, revenue_at_risk_mrr: 31200,
    scrap_recovery_usd: 35000, net_savings_usd: 174000,
    completion_pct: 0, constraint: 'crew_capacity_constrained',
    constraint_detail: 'Dig crew utilization at 94% Q3 2026 — may slip to Wave 3',
    assigned_crew: 'Pacific Northwest Telecom', priority_score: 78,
  },
  {
    wire_center_id: 'WC-CO-003', wire_center_name: 'Colorado-Springs', state: 'CO',
    wave: 2, scheduled_start: '2026-08-01', scheduled_end: '2026-11-30',
    status: 'planned', customers_affected: 119, copper_devices: 74,
    migration_cost_usd: 401000, revenue_at_risk_mrr: 23800,
    scrap_recovery_usd: 27000, net_savings_usd: 131000,
    completion_pct: 0, constraint: 'none', constraint_detail: '',
    assigned_crew: 'Mountain West Fiber Co', priority_score: 76,
  },

  // Wave 3 — Q4 2026 / Q1 2027
  {
    wire_center_id: 'WC-AZ-001', wire_center_name: 'Phoenix-Metro', state: 'AZ',
    wave: 3, scheduled_start: '2026-10-01', scheduled_end: '2027-01-31',
    status: 'planned', customers_affected: 231, copper_devices: 144,
    migration_cost_usd: 812000, revenue_at_risk_mrr: 46200,
    scrap_recovery_usd: 52000, net_savings_usd: 264000,
    completion_pct: 0, constraint: 'contract_locked',
    constraint_detail: '3 enterprise MSAs expire 2027-03-15 (Ironclad CLM)',
    assigned_crew: 'Desert Connect', priority_score: 73,
  },
  {
    wire_center_id: 'WC-ID-001', wire_center_name: 'Boise-Central', state: 'ID',
    wave: 3, scheduled_start: '2026-11-01', scheduled_end: '2027-02-28',
    status: 'planned', customers_affected: 87, copper_devices: 54,
    migration_cost_usd: 298000, revenue_at_risk_mrr: 17400,
    scrap_recovery_usd: 19000, net_savings_usd: 97000,
    completion_pct: 0, constraint: 'none', constraint_detail: '',
    assigned_crew: 'IdahoNet Services', priority_score: 70,
  },
  {
    wire_center_id: 'WC-MN-002', wire_center_name: 'St-Paul-East', state: 'MN',
    wave: 3, scheduled_start: '2026-12-01', scheduled_end: '2027-03-31',
    status: 'planned', customers_affected: 134, copper_devices: 83,
    migration_cost_usd: 463000, revenue_at_risk_mrr: 26800,
    scrap_recovery_usd: 30000, net_savings_usd: 151000,
    completion_pct: 0, constraint: 'regulatory_notice_pending',
    constraint_detail: 'MN PUC 270-day notice: not yet filed',
    assigned_crew: 'Northland Connectivity', priority_score: 67,
  },

  // Wave 4 — Q2–Q3 2027
  {
    wire_center_id: 'WC-WA-002', wire_center_name: 'Tacoma-South', state: 'WA',
    wave: 4, scheduled_start: '2027-04-01', scheduled_end: '2027-07-31',
    status: 'planned', customers_affected: 178, copper_devices: 111,
    migration_cost_usd: 623000, revenue_at_risk_mrr: 35600,
    scrap_recovery_usd: 40000, net_savings_usd: 203000,
    completion_pct: 0, constraint: 'revrec_locked',
    constraint_detail: 'ASC 606 rev recognition active through 2027-06 on 12 circuits',
    assigned_crew: 'Pacific Northwest Telecom', priority_score: 64,
  },
  {
    wire_center_id: 'WC-OR-002', wire_center_name: 'Eugene-West', state: 'OR',
    wave: 4, scheduled_start: '2027-05-01', scheduled_end: '2027-08-31',
    status: 'planned', customers_affected: 92, copper_devices: 57,
    migration_cost_usd: 315000, revenue_at_risk_mrr: 18400,
    scrap_recovery_usd: 21000, net_savings_usd: 103000,
    completion_pct: 0, constraint: 'none', constraint_detail: '',
    assigned_crew: 'Pacific Northwest Telecom', priority_score: 61,
  },
  {
    wire_center_id: 'WC-AZ-002', wire_center_name: 'Tucson-North', state: 'AZ',
    wave: 4, scheduled_start: '2027-06-01', scheduled_end: '2027-09-30',
    status: 'planned', customers_affected: 108, copper_devices: 67,
    migration_cost_usd: 371000, revenue_at_risk_mrr: 21600,
    scrap_recovery_usd: 24000, net_savings_usd: 121000,
    completion_pct: 0, constraint: 'none', constraint_detail: '',
    assigned_crew: 'Desert Connect', priority_score: 58,
  },

  // Wave 5 — Q4 2027 / Q1 2028
  {
    wire_center_id: 'WC-CO-004', wire_center_name: 'Fort-Collins', state: 'CO',
    wave: 5, scheduled_start: '2027-10-01', scheduled_end: '2028-01-31',
    status: 'planned', customers_affected: 76, copper_devices: 47,
    migration_cost_usd: 261000, revenue_at_risk_mrr: 15200,
    scrap_recovery_usd: 17000, net_savings_usd: 85000,
    completion_pct: 0, constraint: 'none', constraint_detail: '',
    assigned_crew: 'Mountain West Fiber Co', priority_score: 55,
  },
  {
    wire_center_id: 'WC-ID-002', wire_center_name: 'Twin-Falls', state: 'ID',
    wave: 5, scheduled_start: '2027-11-01', scheduled_end: '2028-02-28',
    status: 'planned', customers_affected: 54, copper_devices: 34,
    migration_cost_usd: 187000, revenue_at_risk_mrr: 10800,
    scrap_recovery_usd: 12000, net_savings_usd: 61000,
    completion_pct: 0, constraint: 'none', constraint_detail: '',
    assigned_crew: 'IdahoNet Services', priority_score: 52,
  },
  {
    wire_center_id: 'WC-MN-003', wire_center_name: 'Duluth-Harbor', state: 'MN',
    wave: 5, scheduled_start: '2028-01-01', scheduled_end: '2028-04-30',
    status: 'planned', customers_affected: 63, copper_devices: 39,
    migration_cost_usd: 216000, revenue_at_risk_mrr: 12600,
    scrap_recovery_usd: 14000, net_savings_usd: 70000,
    completion_pct: 0, constraint: 'contract_locked',
    constraint_detail: '1 wholesale MSA expires 2028-06-01 (Ironclad CLM)',
    assigned_crew: 'Northland Connectivity', priority_score: 49,
  },

  // Wave 6 — Q2–Q3 2028
  {
    wire_center_id: 'WC-WA-003', wire_center_name: 'Spokane-Valley', state: 'WA',
    wave: 6, scheduled_start: '2028-04-01', scheduled_end: '2028-07-31',
    status: 'planned', customers_affected: 89, copper_devices: 55,
    migration_cost_usd: 305000, revenue_at_risk_mrr: 17800,
    scrap_recovery_usd: 20000, net_savings_usd: 99000,
    completion_pct: 0, constraint: 'none', constraint_detail: '',
    assigned_crew: 'Pacific Northwest Telecom', priority_score: 46,
  },
  {
    wire_center_id: 'WC-OR-003', wire_center_name: 'Salem-Downtown', state: 'OR',
    wave: 6, scheduled_start: '2028-05-01', scheduled_end: '2028-08-31',
    status: 'planned', customers_affected: 71, copper_devices: 44,
    migration_cost_usd: 243000, revenue_at_risk_mrr: 14200,
    scrap_recovery_usd: 16000, net_savings_usd: 79000,
    completion_pct: 0, constraint: 'none', constraint_detail: '',
    assigned_crew: 'Pacific Northwest Telecom', priority_score: 43,
  },

  // Wave 7 — Q4 2028 / Q1 2029
  {
    wire_center_id: 'WC-AZ-003', wire_center_name: 'Flagstaff', state: 'AZ',
    wave: 7, scheduled_start: '2028-10-01', scheduled_end: '2029-01-31',
    status: 'planned', customers_affected: 45, copper_devices: 28,
    migration_cost_usd: 154000, revenue_at_risk_mrr: 9000,
    scrap_recovery_usd: 10000, net_savings_usd: 50000,
    completion_pct: 0, constraint: 'none', constraint_detail: '',
    assigned_crew: 'Desert Connect', priority_score: 40,
  },
  {
    wire_center_id: 'WC-CO-005', wire_center_name: 'Pueblo-South', state: 'CO',
    wave: 7, scheduled_start: '2028-11-01', scheduled_end: '2029-02-28',
    status: 'planned', customers_affected: 38, copper_devices: 24,
    migration_cost_usd: 132000, revenue_at_risk_mrr: 7600,
    scrap_recovery_usd: 9000, net_savings_usd: 43000,
    completion_pct: 0, constraint: 'none', constraint_detail: '',
    assigned_crew: 'Mountain West Fiber Co', priority_score: 37,
  },

  // Wave 8 — Q2–Q4 2029 (final cleanup)
  {
    wire_center_id: 'WC-ID-003', wire_center_name: 'Pocatello', state: 'ID',
    wave: 8, scheduled_start: '2029-04-01', scheduled_end: '2029-07-31',
    status: 'planned', customers_affected: 31, copper_devices: 19,
    migration_cost_usd: 108000, revenue_at_risk_mrr: 6200,
    scrap_recovery_usd: 7000, net_savings_usd: 35000,
    completion_pct: 0, constraint: 'none', constraint_detail: '',
    assigned_crew: 'IdahoNet Services', priority_score: 34,
  },
  {
    wire_center_id: 'WC-MN-004', wire_center_name: 'Rochester-Central', state: 'MN',
    wave: 8, scheduled_start: '2029-05-01', scheduled_end: '2029-08-31',
    status: 'planned', customers_affected: 42, copper_devices: 26,
    migration_cost_usd: 145000, revenue_at_risk_mrr: 8400,
    scrap_recovery_usd: 9000, net_savings_usd: 47000,
    completion_pct: 0, constraint: 'none', constraint_detail: '',
    assigned_crew: 'Northland Connectivity', priority_score: 31,
  },
];

// --- Mock Milestones ---

export const mockMilestones: MilestoneItem[] = [
  // Wave 1 milestones
  { milestone_id: 'MS-001', wire_center_id: 'WC-CO-001', name: 'FCC Section 214 filing', type: 'regulatory', planned_date: '2026-02-15', actual_date: '2026-02-14', status: 'achieved', critical_path: true },
  { milestone_id: 'MS-002', wire_center_id: 'WC-CO-001', name: '90-day residential notice sent', type: 'regulatory', planned_date: '2026-03-01', actual_date: '2026-03-01', status: 'achieved', critical_path: true },
  { milestone_id: 'MS-003', wire_center_id: 'WC-CO-001', name: 'Fiber provisioning complete', type: 'technical', planned_date: '2026-05-15', actual_date: null, status: 'in_progress', critical_path: true },
  { milestone_id: 'MS-004', wire_center_id: 'WC-CO-001', name: 'Customer cutover begin', type: 'operational', planned_date: '2026-06-01', actual_date: null, status: 'pending', critical_path: true },
  { milestone_id: 'MS-005', wire_center_id: 'WC-CO-001', name: 'Budget approval', type: 'financial', planned_date: '2026-01-20', actual_date: '2026-01-18', status: 'achieved', critical_path: false },
  { milestone_id: 'MS-006', wire_center_id: 'WC-MN-001', name: 'MN PUC 270-day notice filing', type: 'regulatory', planned_date: '2026-03-01', actual_date: '2026-03-01', status: 'achieved', critical_path: true },
  { milestone_id: 'MS-007', wire_center_id: 'WC-MN-001', name: 'MN PUC notice period clears', type: 'regulatory', planned_date: '2026-11-26', actual_date: null, status: 'pending', critical_path: true },
  { milestone_id: 'MS-008', wire_center_id: 'WC-WA-001', name: 'WA UTC 180-day notice filing', type: 'regulatory', planned_date: '2026-04-01', actual_date: null, status: 'pending', critical_path: true },
  // Wave 3 milestones
  { milestone_id: 'MS-009', wire_center_id: 'WC-AZ-001', name: 'Enterprise MSA expiration gate', type: 'financial', planned_date: '2027-03-15', actual_date: null, status: 'at_risk', critical_path: true },
  { milestone_id: 'MS-010', wire_center_id: 'WC-AZ-001', name: 'AZ ACC regulatory approval', type: 'regulatory', planned_date: '2026-09-01', actual_date: null, status: 'pending', critical_path: true },
];

// --- Mock Scenarios ---

export const mockScenarios: ScenarioRun[] = [
  {
    scenario_id: 'SCN-001', name: 'Baseline — Risk-first',
    created_at: '2026-09-01', objective: 'Minimize risk exposure',
    total_cost: 7_893_000, total_duration_months: 42, waves_used: 8,
    risk_score: 72, status: 'active',
  },
  {
    scenario_id: 'SCN-002', name: 'Cost-optimized',
    created_at: '2026-09-05', objective: 'Minimize total migration cost',
    total_cost: 6_954_000, total_duration_months: 48, waves_used: 6,
    risk_score: 85, status: 'draft',
  },
  {
    scenario_id: 'SCN-003', name: 'Accelerated — 3-year target',
    created_at: '2026-09-08', objective: 'Complete by 2029-Q2',
    total_cost: 9_210_000, total_duration_months: 36, waves_used: 10,
    risk_score: 64, status: 'draft',
  },
];

// --- Computed KPIs (from mock wire centers) ---

export function computeKPIs(): PlanKPIData {
  const total = mockWireCenters.length;
  const completed = mockWireCenters.filter((wc) => wc.status === 'completed').length;
  const inFlight = mockWireCenters.filter(
    (wc) => wc.status === 'in_progress' || wc.status === 'fiber_provisioned' || wc.status === 'cutover'
  ).length;
  const planned = mockWireCenters.filter((wc) => wc.status === 'planned').length;

  const totalBudget = mockWireCenters.reduce((s, wc) => s + wc.migration_cost_usd, 0);
  const spentPct = mockWireCenters.reduce((s, wc) => s + wc.migration_cost_usd * (wc.completion_pct / 100), 0);
  const totalCustomers = mockWireCenters.reduce((s, wc) => s + wc.customers_affected, 0);
  const migratedCustomers = mockWireCenters
    .filter((wc) => wc.status === 'completed')
    .reduce((s, wc) => s + wc.customers_affected, 0);

  return {
    total_wire_centers: total,
    pct_planned: (planned / total) * 100,
    pct_in_flight: (inFlight / total) * 100,
    pct_completed: (completed / total) * 100,
    total_budget_allocated: totalBudget,
    total_budget_remaining: totalBudget - spentPct,
    customers_migrated: migratedCustomers,
    customers_remaining: totalCustomers - migratedCustomers,
  };
}
