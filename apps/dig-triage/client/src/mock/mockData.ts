/**
 * mockData.ts
 * Mock data for the Dig-Safe Triage Console.
 * Used when real data is unavailable (P0-DATAGEN-DIGSAFE-EXECUTE not yet run,
 * P6-TRIAGE agent not yet deployed).
 *
 * Incident locations use LEGACY_STATES from SPEC_dig_safe_incident.md:
 * CO (35%), MN (20%), WA (15%), OR (12%), ID (10%), AZ (8%)
 *
 * All data is SYNTHETIC — for demo scaffolding only.
 */

// --- Feature flag: set to false to use live SQL queries ---
export const USE_MOCK_DATA = true;

// --- Types ---
export type Severity = 'critical' | 'major' | 'minor' | 'informational';
export type CableType = 'aerial' | 'buried_direct' | 'underground_conduit';
export type IncidentStatus = 'open' | 'in_progress' | 'resolved' | 'closed';
export type ActionDecision = 'pending_approval' | 'approved' | 'rejected';

export interface Incident {
  incident_id: string;
  incident_date: string;
  incident_timestamp: string;
  severity: Severity;
  cable_type: CableType;
  cable_damage_type: string;
  root_cause: string;
  state: string;
  latitude: number;
  longitude: number;
  resolution_time_hours: number | null;
  reroute_required: boolean;
  service_interruption: boolean;
  affected_pair_count: number;
  repair_cost: number;
  contractor_at_fault: boolean;
  one_call_ticket_submitted: boolean;
  status: IncidentStatus;
  work_id: number | null;
  contractor_name: string;
}

export interface AgentResponse {
  message: string;
  actions: AgentAction[];
  confidence: number;
  sources: string[];
}

export interface AgentAction {
  action_id: string;
  type: string;
  description: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  affected_customers: number;
  estimated_time_hours: number;
  status: ActionDecision;
}

export interface ActionLogEntry {
  action_id: string;
  incident_id: string;
  action_type: string;
  description: string;
  decision: ActionDecision;
  reviewer: string;
  timestamp: string;
}

export interface TriageKPIs {
  open_incidents: number;
  avg_resolution_hours: number;
  incidents_this_week: number;
  reroutes_pending: number;
  active_contractors: number;
  critical_incidents: number;
}

// --- Severity color mapping ---
export const SEVERITY_COLORS: Record<Severity, string> = {
  critical: '#EB1600',      // Databricks red
  major: '#FF8C00',         // Orange
  minor: '#FFD700',         // Gold/yellow
  informational: '#40d1f5', // Databricks cyan
};

export const STATUS_COLORS: Record<IncidentStatus, string> = {
  open: '#EB1600',
  in_progress: '#FF8C00',
  resolved: '#00A972',
  closed: '#8B8B8B',
};

export const SEVERITY_LEVELS: Severity[] = ['critical', 'major', 'minor', 'informational'];

// --- Mock incidents across LEGACY_STATES (CO, MN, WA, OR, ID, AZ) ---
// Coordinates match SPEC_dig_safe_incident.md per-state bounding boxes
const MOCK_INCIDENTS: Incident[] = [
  // Colorado (35% weight)
  {
    incident_id: 'INC-200001', incident_date: '2026-09-10', incident_timestamp: '2026-09-10T14:23:00Z',
    severity: 'critical', cable_type: 'buried_direct', cable_damage_type: 'cut',
    root_cause: 'excavation', state: 'CO', latitude: 39.7392, longitude: -104.9903,
    resolution_time_hours: null, reroute_required: true, service_interruption: true,
    affected_pair_count: 48, repair_cost: 32500, contractor_at_fault: true,
    one_call_ticket_submitted: false, status: 'open', work_id: 10523,
    contractor_name: 'Rocky Mountain Utilities LLC',
  },
  {
    incident_id: 'INC-200002', incident_date: '2026-09-10', incident_timestamp: '2026-09-10T09:45:00Z',
    severity: 'major', cable_type: 'underground_conduit', cable_damage_type: 'crush',
    root_cause: 'boring', state: 'CO', latitude: 39.8561, longitude: -104.6737,
    resolution_time_hours: 6.5, reroute_required: true, service_interruption: true,
    affected_pair_count: 24, repair_cost: 18200, contractor_at_fault: false,
    one_call_ticket_submitted: true, status: 'in_progress', work_id: 11204,
    contractor_name: 'Front Range Fiber Co',
  },
  {
    incident_id: 'INC-200003', incident_date: '2026-09-09', incident_timestamp: '2026-09-09T16:10:00Z',
    severity: 'minor', cable_type: 'aerial', cable_damage_type: 'abrasion',
    root_cause: 'vehicle_strike', state: 'CO', latitude: 40.0150, longitude: -105.2705,
    resolution_time_hours: 2.0, reroute_required: false, service_interruption: false,
    affected_pair_count: 6, repair_cost: 2800, contractor_at_fault: false,
    one_call_ticket_submitted: true, status: 'resolved', work_id: 10891,
    contractor_name: 'N/A (vehicle accident)',
  },
  {
    incident_id: 'INC-200004', incident_date: '2026-09-09', incident_timestamp: '2026-09-09T11:30:00Z',
    severity: 'critical', cable_type: 'buried_direct', cable_damage_type: 'cut',
    root_cause: 'trenching', state: 'CO', latitude: 38.8339, longitude: -104.8214,
    resolution_time_hours: null, reroute_required: true, service_interruption: true,
    affected_pair_count: 96, repair_cost: 58000, contractor_at_fault: true,
    one_call_ticket_submitted: false, status: 'open', work_id: null,
    contractor_name: 'Peak Excavation Inc',
  },
  // Minnesota (20% weight)
  {
    incident_id: 'INC-200005', incident_date: '2026-09-10', incident_timestamp: '2026-09-10T08:15:00Z',
    severity: 'major', cable_type: 'buried_direct', cable_damage_type: 'nick',
    root_cause: 'plowing', state: 'MN', latitude: 44.9778, longitude: -93.2650,
    resolution_time_hours: 4.0, reroute_required: false, service_interruption: true,
    affected_pair_count: 12, repair_cost: 8500, contractor_at_fault: true,
    one_call_ticket_submitted: true, status: 'in_progress', work_id: 10672,
    contractor_name: 'Northland Contractors',
  },
  {
    incident_id: 'INC-200006', incident_date: '2026-09-08', incident_timestamp: '2026-09-08T13:20:00Z',
    severity: 'minor', cable_type: 'underground_conduit', cable_damage_type: 'moisture_ingress',
    root_cause: 'natural_event', state: 'MN', latitude: 44.8485, longitude: -93.4720,
    resolution_time_hours: 12.0, reroute_required: false, service_interruption: false,
    affected_pair_count: 8, repair_cost: 4200, contractor_at_fault: false,
    one_call_ticket_submitted: true, status: 'resolved', work_id: 10445,
    contractor_name: 'Twin Cities Underground',
  },
  // Washington (15% weight)
  {
    incident_id: 'INC-200007', incident_date: '2026-09-11', incident_timestamp: '2026-09-11T07:05:00Z',
    severity: 'critical', cable_type: 'buried_direct', cable_damage_type: 'cut',
    root_cause: 'excavation', state: 'WA', latitude: 47.6062, longitude: -122.3321,
    resolution_time_hours: null, reroute_required: true, service_interruption: true,
    affected_pair_count: 72, repair_cost: 45000, contractor_at_fault: true,
    one_call_ticket_submitted: false, status: 'open', work_id: null,
    contractor_name: 'Puget Sound Excavation',
  },
  {
    incident_id: 'INC-200008', incident_date: '2026-09-10', incident_timestamp: '2026-09-10T15:40:00Z',
    severity: 'minor', cable_type: 'aerial', cable_damage_type: 'displacement',
    root_cause: 'natural_event', state: 'WA', latitude: 47.2529, longitude: -122.4443,
    resolution_time_hours: 1.5, reroute_required: false, service_interruption: false,
    affected_pair_count: 4, repair_cost: 1200, contractor_at_fault: false,
    one_call_ticket_submitted: true, status: 'resolved', work_id: 11098,
    contractor_name: 'N/A (storm damage)',
  },
  // Oregon (12% weight)
  {
    incident_id: 'INC-200009', incident_date: '2026-09-10', incident_timestamp: '2026-09-10T10:55:00Z',
    severity: 'major', cable_type: 'buried_direct', cable_damage_type: 'nick',
    root_cause: 'hand_dig', state: 'OR', latitude: 45.5152, longitude: -122.6784,
    resolution_time_hours: 8.0, reroute_required: true, service_interruption: true,
    affected_pair_count: 18, repair_cost: 12400, contractor_at_fault: true,
    one_call_ticket_submitted: true, status: 'in_progress', work_id: 10988,
    contractor_name: 'Willamette Utility Services',
  },
  // Idaho (10% weight)
  {
    incident_id: 'INC-200010', incident_date: '2026-09-09', incident_timestamp: '2026-09-09T14:30:00Z',
    severity: 'informational', cable_type: 'underground_conduit', cable_damage_type: 'abrasion',
    root_cause: 'utility_conflict', state: 'ID', latitude: 43.6150, longitude: -116.2023,
    resolution_time_hours: 0.5, reroute_required: false, service_interruption: false,
    affected_pair_count: 2, repair_cost: 800, contractor_at_fault: false,
    one_call_ticket_submitted: true, status: 'closed', work_id: 10756,
    contractor_name: 'Gem State Utilities',
  },
  // Arizona (8% weight)
  {
    incident_id: 'INC-200011', incident_date: '2026-09-11', incident_timestamp: '2026-09-11T06:20:00Z',
    severity: 'major', cable_type: 'buried_direct', cable_damage_type: 'crush',
    root_cause: 'boring', state: 'AZ', latitude: 33.4484, longitude: -112.0740,
    resolution_time_hours: null, reroute_required: false, service_interruption: true,
    affected_pair_count: 30, repair_cost: 21000, contractor_at_fault: true,
    one_call_ticket_submitted: true, status: 'open', work_id: null,
    contractor_name: 'Sonoran Excavation LLC',
  },
  {
    incident_id: 'INC-200012', incident_date: '2026-09-07', incident_timestamp: '2026-09-07T12:00:00Z',
    severity: 'minor', cable_type: 'aerial', cable_damage_type: 'displacement',
    root_cause: 'vehicle_strike', state: 'AZ', latitude: 33.5722, longitude: -112.0880,
    resolution_time_hours: 3.0, reroute_required: false, service_interruption: false,
    affected_pair_count: 4, repair_cost: 1800, contractor_at_fault: false,
    one_call_ticket_submitted: true, status: 'resolved', work_id: 10334,
    contractor_name: 'N/A (vehicle accident)',
  },
];

// --- Mock agent responses ---
const MOCK_AGENT_RESPONSES: Record<string, AgentResponse> = {
  'INC-200001': {
    message: 'CRITICAL: Major copper cable cut on 16th Street, Denver. 48 pairs severed, ' +
      '47 residential customers affected. No 811 ticket filed — potential one-call violation. ' +
      'Recommending immediate reroute via alternate conduit B-7 (estimated 2.5h). ' +
      'Dispatch emergency crew and notify affected customers via SMS.',
    actions: [
      { action_id: 'act_001', type: 'reroute', description: 'Reroute traffic via alternate conduit path B-7', priority: 'critical', affected_customers: 47, estimated_time_hours: 2.5, status: 'pending_approval' },
      { action_id: 'act_002', type: 'dispatch', description: 'Dispatch emergency splice crew from CO-Denver-Central', priority: 'critical', affected_customers: 47, estimated_time_hours: 4.0, status: 'pending_approval' },
      { action_id: 'act_003', type: 'notify', description: 'Send SMS notification to 47 affected residential customers', priority: 'high', affected_customers: 47, estimated_time_hours: 0.25, status: 'pending_approval' },
      { action_id: 'act_004', type: 'regulatory', description: 'File one-call violation report — contractor failed 811 notification', priority: 'medium', affected_customers: 0, estimated_time_hours: 1.0, status: 'pending_approval' },
    ],
    confidence: 0.92,
    sources: ['network_route topology', 'device_service_allocation', 'alarm history', 'geographic_address proximity'],
  },
  'INC-200004': {
    message: 'CRITICAL: Large-scale cable cut in Colorado Springs. 96 pairs affected — ' +
      'estimated 142 customers impacted across 3 wire centers. No 811 filed. ' +
      'This is one of the largest incidents this quarter. Recommending full emergency response: ' +
      'dual splice crews, temporary POTS bypass for critical accounts, and regulatory escalation.',
    actions: [
      { action_id: 'act_005', type: 'reroute', description: 'Activate POTS bypass for 8 critical accounts (medical, 911)', priority: 'critical', affected_customers: 8, estimated_time_hours: 1.0, status: 'pending_approval' },
      { action_id: 'act_006', type: 'dispatch', description: 'Dispatch dual splice crews from CO-Springs and CO-Pueblo', priority: 'critical', affected_customers: 142, estimated_time_hours: 8.0, status: 'pending_approval' },
      { action_id: 'act_007', type: 'notify', description: 'Notify 142 affected customers (SMS + IVR callback)', priority: 'high', affected_customers: 142, estimated_time_hours: 0.5, status: 'pending_approval' },
    ],
    confidence: 0.88,
    sources: ['copper_loop_plant pairs', 'device_service_allocation', 'customer_facing_service', 'alarm correlation'],
  },
  'INC-200007': {
    message: 'CRITICAL: Excavation damage in downtown Seattle. 72 pairs cut — ' +
      'major service disruption to Capitol Hill area. No 811 ticket. ' +
      'High priority: multiple business accounts affected. Recommending immediate ' +
      'reroute and emergency restoration.',
    actions: [
      { action_id: 'act_008', type: 'reroute', description: 'Reroute 12 business accounts via fiber overlay path', priority: 'critical', affected_customers: 12, estimated_time_hours: 1.5, status: 'pending_approval' },
      { action_id: 'act_009', type: 'dispatch', description: 'Dispatch emergency crew from CO-Seattle-Central', priority: 'critical', affected_customers: 89, estimated_time_hours: 6.0, status: 'pending_approval' },
    ],
    confidence: 0.85,
    sources: ['network_route topology', 'service_capacity GPON', 'alarm real-time feed'],
  },
  default: {
    message: 'Analyzing incident... Standard triage recommendation: verify cable location ' +
      'against plant records, assess customer impact via device-service allocation, ' +
      'and dispatch nearest available crew.',
    actions: [
      { action_id: 'act_default', type: 'assess', description: 'Run standard damage assessment protocol', priority: 'medium', affected_customers: 0, estimated_time_hours: 1.0, status: 'pending_approval' },
    ],
    confidence: 0.70,
    sources: ['standard_triage_protocol'],
  },
};

// --- Mock action log ---
const MOCK_ACTION_LOG: ActionLogEntry[] = [
  {
    action_id: 'act_hist_001', incident_id: 'INC-200003', action_type: 'dispatch',
    description: 'Dispatched aerial repair crew to Boulder, CO',
    decision: 'approved', reviewer: 'J. Martinez (Shift Supervisor)',
    timestamp: '2026-09-09T16:25:00Z',
  },
  {
    action_id: 'act_hist_002', incident_id: 'INC-200006', action_type: 'assess',
    description: 'Standard moisture ingress assessment for conduit segment',
    decision: 'approved', reviewer: 'K. Johnson (NOC Lead)',
    timestamp: '2026-09-08T13:45:00Z',
  },
  {
    action_id: 'act_hist_003', incident_id: 'INC-200008', action_type: 'reroute',
    description: 'Reroute via alternate aerial span — rejected, damage minor',
    decision: 'rejected', reviewer: 'S. Kim (Shift Supervisor)',
    timestamp: '2026-09-10T15:55:00Z',
  },
  {
    action_id: 'act_hist_004', incident_id: 'INC-200010', action_type: 'regulatory',
    description: 'File utility conflict report with Idaho PUC',
    decision: 'approved', reviewer: 'M. Chen (Compliance)',
    timestamp: '2026-09-09T15:00:00Z',
  },
];

// --- Mock KPIs (based on real table counts + mock incidents) ---
const MOCK_KPIS: TriageKPIs = {
  open_incidents: 4,                // INC-200001, 200004, 200007, 200011
  avg_resolution_hours: 4.7,        // avg of resolved incidents
  incidents_this_week: 8,           // mock: incidents in last 7 days
  reroutes_pending: 3,              // INC-200001, 200004, 200007
  active_contractors: 1254,         // real: bp_agreement WHERE status='active'
  critical_incidents: 3,            // INC-200001, 200004, 200007
};

// --- Getters ---

export function getMockIncidents(filters?: {
  severity?: string;
  state?: string;
  status?: string;
}): Incident[] {
  let incidents = [...MOCK_INCIDENTS];
  if (filters?.severity && filters.severity !== 'all') {
    incidents = incidents.filter((i) => i.severity === filters.severity);
  }
  if (filters?.state && filters.state !== 'all') {
    incidents = incidents.filter((i) => i.state === filters.state);
  }
  if (filters?.status && filters.status !== 'all') {
    incidents = incidents.filter((i) => i.status === filters.status);
  }
  return incidents;
}

export function getMockIncidentById(id: string): Incident | undefined {
  return MOCK_INCIDENTS.find((i) => i.incident_id === id);
}

export function getMockAgentResponse(incidentId: string): AgentResponse {
  return MOCK_AGENT_RESPONSES[incidentId] || MOCK_AGENT_RESPONSES['default'];
}

export function getMockKPIs(): TriageKPIs {
  return { ...MOCK_KPIS };
}

export function getMockActionLog(): ActionLogEntry[] {
  return [...MOCK_ACTION_LOG];
}

export function getMockStates(): string[] {
  return ['CO', 'MN', 'WA', 'OR', 'ID', 'AZ'];
}
