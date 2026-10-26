/**
 * planApi.ts
 * Client-side API service for the Retirement Plan Tracker.
 * Calls Express server endpoints that query gold_wave_schedule
 * and gold_contractor_assignment_plan via Databricks SQL.
 *
 * V2 (2026-09-20): Live data from gold tables.
 */
import type { WireCenterPlan, PlanKPIData } from '../mock/mockData';

// --- Types for API responses ---

export interface WaveSummaryRow {
  assigned_wave: string;
  wave_year: string;
  wave_quarter: string;
  state_code: string;
  wire_centers: string;
  total_devices: string;
  total_crew_days: string;
  total_customers: string;
  total_revenue_at_risk: string;
  avg_readiness: string;
}

export interface ContractorAssignment {
  wave: string;
  state_code: string;
  contractor_id: string;
  contractor_name: string;
  contractor_type: string;
  primary_state: string;
  dispatch_status: string;
  crew_size: string;
  safety_score: string;
  overall_rating: string;
  sla_compliance_pct: string;
  composite_score: string;
  allocated_crew_days: string;
  estimated_cost_usd: string;
  wire_centers_in_wave: string;
  devices_in_wave: string;
}

export interface LiveKPIs {
  total_wire_centers: string;
  total_devices: string;
  total_customers: string;
  total_revenue_at_risk: string;
  total_crew_days: string;
  fiber_ready_count: string;
  puc_required_count: string;
  avg_readiness: string;
  total_waves: string;
  total_states: string;
  first_wave: string;
  last_wave: string;
  total_critical_devices: string;
  total_high_risk_devices: string;
}

// --- API client ---

async function apiFetch<T>(url: string): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(body.error || `HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Fetch wave schedule data mapped to WireCenterPlan format.
 * Falls back to null on error (caller should use mock data).
 */
export async function fetchLiveWaves(): Promise<WireCenterPlan[] | null> {
  try {
    const { data } = await apiFetch<{ success: boolean; data: WireCenterPlan[] }>(
      '/api/plan/waves'
    );
    return data;
  } catch (err) {
    console.warn('[planApi] Failed to fetch live waves:', err);
    return null;
  }
}

/**
 * Fetch wave summary (regional rollup by quarter/state).
 */
export async function fetchLiveWaveSummary(): Promise<WaveSummaryRow[] | null> {
  try {
    const { data } = await apiFetch<{ success: boolean; data: WaveSummaryRow[] }>(
      '/api/plan/waves/summary'
    );
    return data;
  } catch (err) {
    console.warn('[planApi] Failed to fetch wave summary:', err);
    return null;
  }
}

/**
 * Fetch contractor assignment plan.
 */
export async function fetchLiveContractors(): Promise<ContractorAssignment[] | null> {
  try {
    const { data } = await apiFetch<{ success: boolean; data: ContractorAssignment[] }>(
      '/api/plan/contractors'
    );
    return data;
  } catch (err) {
    console.warn('[planApi] Failed to fetch contractors:', err);
    return null;
  }
}

/**
 * Fetch computed KPIs from gold_wave_schedule.
 */
export async function fetchLiveKPIs(): Promise<LiveKPIs | null> {
  try {
    const { data } = await apiFetch<{ success: boolean; data: LiveKPIs }>(
      '/api/plan/kpis'
    );
    return data;
  } catch (err) {
    console.warn('[planApi] Failed to fetch KPIs:', err);
    return null;
  }
}

// --- Budget data ---

export interface BudgetRow {
  wave_label: string;
  retirement_wave: string;
  wire_centers: string;
  total_allocated: string;
  total_spent: string;
  remaining: string;
  annual_revenue_at_risk: string;
  total_devices: string;
  total_customers: string;
  avg_completion_pct: string;
}

export async function fetchLiveBudget(): Promise<BudgetRow[] | null> {
  try {
    const { data } = await apiFetch<{ success: boolean; data: BudgetRow[] }>(
      '/api/plan/budget'
    );
    return data;
  } catch (err) {
    console.warn('[planApi] Failed to fetch budget:', err);
    return null;
  }
}

// --- Regulatory checklist ---

export interface RegulatoryItem {
  checklist_id: string;
  wire_center_id: string;
  wire_center_name: string;
  state_code: string;
  checklist_item: string;
  item_category: string;
  description: string;
  required: string;
  required_notice_days: string;
  deadline_date: string;
  status: string;
  assigned_to: string;
  completed_date: string;
  evidence_reference: string;
  notes: string;
  // ACC-APP-PLAN-LAKEBASE-READS: cited source fields from UC jurisdiction_requirements_cited
  jurisdiction_code?: string;
  citation?: string | null;
  official_url?: string | null;
  citation_url?: string | null;
  verification_status?: string | null;
  last_verified?: string | null;
}

export async function fetchLiveRegulatory(wireCenterId?: string): Promise<RegulatoryItem[] | null> {
  try {
    const url = wireCenterId
      ? `/api/plan/regulatory?wire_center_id=${encodeURIComponent(wireCenterId)}`
      : '/api/plan/regulatory';
    const { data } = await apiFetch<{ success: boolean; data: RegulatoryItem[] }>(url);
    return data;
  } catch (err) {
    console.warn('[planApi] Failed to fetch regulatory:', err);
    return null;
  }
}

// --- Milestones ---

export interface MilestoneRow {
  milestone_id: string;
  wire_center_id: string;
  name: string;
  type: string;
  status: string;
  priority: string;
  planned_date: string;
  actual_date: string;
  forecast_date: string;
  completion_percentage: string;
  critical_path_flag: string;
  regulatory_requirement_flag: string;
  risk_level: string;
  risk_description: string;
}

export async function fetchLiveMilestones(wireCenterId?: string): Promise<MilestoneRow[] | null> {
  try {
    const url = wireCenterId
      ? `/api/plan/milestones?wire_center_id=${encodeURIComponent(wireCenterId)}`
      : '/api/plan/milestones';
    const { data } = await apiFetch<{ success: boolean; data: MilestoneRow[] }>(url);
    return data;
  } catch (err) {
    console.warn('[planApi] Failed to fetch milestones:', err);
    return null;
  }
}
