/**
 * triageApi.ts
 * Client-side API service for the Dig-Safe Triage Console.
 * Calls the Express server endpoints that wrap UC triage functions:
 *   - incident_lookup  → GET /api/triage/incident/:id
 *   - proximity_search → POST /api/triage/nearby
 *   - reroute_suggest  → GET /api/triage/reroute/:id
 *
 * V2 (2026-09-20): Live data from UC functions via SQL Statement API.
 */

// --- Types matching UC function return schemas ---

export interface IncidentDetail {
  incident_id: string;
  state: string;
  incident_date: string;
  incident_latitude: string;
  incident_longitude: string;
  severity: string;
  cable_type: string;
  cable_damage_type: string;
  root_cause: string;
  contractor_at_fault: string | boolean;
  one_call_ticket_submitted: string | boolean;
  resolution_time_hours: string | null;
  reroute_required: string | boolean;
  service_interruption: string | boolean;
  affected_pair_count: string;
  repair_cost_amount: string;
  recommended_action: string;
  triage_priority: string;
  nearest_device_id: string;
  nearest_device_type: string;
  nearest_device_distance_km: string;
  nearby_copper_device_count: string;
  impacted_service_count: string;
  impacted_customer_count: string;
  impacted_service_types: string;
  wire_center_id: string;
  wire_center_name: string;
}

export interface NearbyIncident {
  incident_id: string;
  state: string;
  incident_date: string;
  severity: string;
  cable_type: string;
  root_cause: string;
  service_interruption: string | boolean;
  reroute_required: string | boolean;
  recommended_action: string;
  triage_priority: string;
  incident_latitude: string;
  incident_longitude: string;
  distance_from_search_km: string;
  nearest_device_id: string;
  nearest_device_type: string;
  nearest_device_distance_km: string;
  nearby_copper_device_count: string;
  impacted_service_count: string;
  wire_center_id: string;
}

export interface RerouteSuggestion {
  incident_id: string;
  incident_state: string;
  incident_severity: string;
  triage_priority: string;
  reroute_required: string | boolean;
  service_interruption: string | boolean;
  recommended_action: string;
  affected_pair_count: string;
  incident_latitude: string;
  incident_longitude: string;
  nearest_device_id: string;
  nearest_device_type: string;
  nearest_device_distance_km: string;
  wire_center_id: string;
  wire_center_name: string;
  wire_center_fiber_ready: string | boolean;
  impacted_service_count: string;
  impacted_customer_count: string;
  impacted_service_types: string;
  reroute_option: string;
  reroute_rationale: string;
}

export interface ChatResponse {
  response: string;
  actions: Array<{
    action_id: string;
    type: string;
    description: string;
    priority: string;
    affected_customers: number;
    estimated_time_hours: number;
    status: string;
  }>;
  confidence: number;
  sources: string[];
  live_data?: boolean;
  wire_center?: string | null;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded';
  sql_connected: boolean;
  timestamp: string;
  env: {
    host_set: boolean;
    warehouse_set: boolean;
    token_set: boolean;
  };
}

// --- API client ---

const BASE = '';

async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: res.statusText }));
    throw new ApiError(res.status, body.error || body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/** Error carrying the HTTP status so the UI can state the real data state (ACC-DES-DEF-TRIAGE-STATES). */
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

/** Map an API failure to an honest, user-facing message. Never reports a permission or network error as 'not found'. */
export function describeApiError(err: unknown, notFoundText = 'Not found'): string {
  const status = err instanceof ApiError ? err.status : 0;
  const msg = err instanceof Error ? err.message : String(err);
  if (status === 403) return msg.startsWith('Data access pending') ? msg : `Data access pending: the app service principal lacks SELECT on the source table (${msg})`;
  if (status === 404) return notFoundText;
  if (status === 400) return msg;
  return 'Could not reach data service';
}

/**
 * Lookup enriched incident details by ID.
 * Calls UC: cdm_tmforum.copper_retirement.incident_lookup
 */
export async function fetchIncidentDetail(incidentId: number): Promise<IncidentDetail> {
  const { data } = await apiFetch<{ success: boolean; data: IncidentDetail }>(
    `/api/triage/incident/${incidentId}`
  );
  return data;
}

/**
 * Search for nearby incidents within a radius.
 * Calls UC: cdm_tmforum.copper_retirement.proximity_search
 */
export async function fetchNearbyIncidents(
  latitude: number,
  longitude: number,
  radiusKm = 25
): Promise<NearbyIncident[]> {
  const { data } = await apiFetch<{ success: boolean; count: number; data: NearbyIncident[] }>(
    '/api/triage/nearby',
    {
      method: 'POST',
      body: JSON.stringify({ latitude, longitude, radius_km: radiusKm }),
    }
  );
  return data;
}

/**
 * Get reroute suggestion for an incident.
 * Calls UC: cdm_tmforum.copper_retirement.reroute_suggest
 */
export async function fetchRerouteSuggestion(incidentId: number): Promise<RerouteSuggestion> {
  const { data } = await apiFetch<{ success: boolean; data: RerouteSuggestion }>(
    `/api/triage/reroute/${incidentId}`
  );
  return data;
}

/**
 * Send message to triage agent chat (uses live UC data when available).
 */
export async function sendChatMessage(incidentId: string, message: string): Promise<ChatResponse> {
  return apiFetch<ChatResponse>('/api/triage/chat', {
    method: 'POST',
    body: JSON.stringify({ incidentId, message }),
  });
}

/**
 * Fetch incident list from live silver_dig_incident_enriched table.
 * Returns incidents in the same shape as the client Incident type.
 */
export async function fetchIncidents(limit = 100): Promise<Array<Record<string, unknown>>> {
  const { data } = await apiFetch<{ success: boolean; count: number; data: Array<Record<string, unknown>> }>(
    `/api/triage/incidents?limit=${limit}`
  );
  return data;
}

/**
 * Fetch KPI aggregates from the live table.
 */
export interface LiveTriageKPIs {
  as_of: string | null;
  window_days: number;
  synthetic: boolean;
  source: string;
  open_incidents: number;
  avg_resolution_hours: number;
  incidents_this_week: number;
  reroutes_pending: number;
  window_incidents: number;
  active_contractors: number;
  critical_incidents: number;
}

/** KPIs are an as-of replay anchored to the latest incident in the (synthetic) table; see server/routes/triage.js. */
export async function fetchKPIs(asOf?: string): Promise<LiveTriageKPIs> {
  const qs = asOf && /^\d{4}-\d{2}-\d{2}$/.test(asOf) ? `?as_of=${asOf}` : '';
  const { data } = await apiFetch<{ success: boolean; data: LiveTriageKPIs }>(`/api/triage/kpis${qs}`);
  return data;
}

/**
 * Health check — verifies backend SQL connectivity.
 */
export async function checkHealth(): Promise<HealthStatus> {
  return apiFetch<HealthStatus>('/api/triage/health');
}
