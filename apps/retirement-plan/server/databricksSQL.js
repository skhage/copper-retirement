/**
 * databricksSQL.js
 * Data layer for querying gold_wave_schedule and gold_contractor_assignment_plan
 * via the Databricks SQL Statement Execution API.
 *
 * Auth: Uses DATABRICKS_TOKEN (auto-injected by Databricks Apps runtime).
 * Requires: DATABRICKS_HOST, DATABRICKS_WAREHOUSE_ID env vars.
 */

const DATABRICKS_HOST = process.env.DATABRICKS_HOST;
const WAREHOUSE_ID = process.env.DATABRICKS_WAREHOUSE_ID;

async function executeSQL(statement) {
  if (!DATABRICKS_HOST) throw new Error('DATABRICKS_HOST env var not set');
  if (!WAREHOUSE_ID) throw new Error('DATABRICKS_WAREHOUSE_ID env var not set');

  const token = process.env.DATABRICKS_TOKEN;
  if (!token) throw new Error('DATABRICKS_TOKEN not set');

  const url = `${DATABRICKS_HOST}/api/2.0/sql/statements`;
  const body = {
    warehouse_id: WAREHOUSE_ID,
    statement,
    wait_timeout: '30s',
    on_wait_timeout: 'CANCEL',
    format: 'JSON_ARRAY',
  };

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`SQL API error ${res.status}: ${errText}`);
  }

  const data = await res.json();
  if (data.status?.state === 'FAILED') {
    throw new Error(`SQL failed: ${data.status.error?.message || 'unknown'}`);
  }

  const columns = data.manifest?.schema?.columns || [];
  const rows = data.result?.data_array || [];
  return rows.map((row) => {
    const obj = {};
    columns.forEach((col, i) => { obj[col.name] = row[i]; });
    return obj;
  });
}

/**
 * Fetch all wave schedule data, mapped to the WireCenterPlan format
 * that the Gantt/Table components expect.
 */
export async function fetchWaveSchedule() {
  const rows = await executeSQL(`
    SELECT
      w.wire_center_id,
      w.wire_center_name,
      w.state_code,
      w.assigned_wave,
      w.wave_year,
      w.wave_quarter,
      w.wave_start_date,
      w.fiber_ready,
      w.puc_filing_required,
      w.copper_device_count,
      w.critical_risk_devices,
      w.high_risk_devices,
      w.retirement_readiness_score,
      w.retirement_priority_rank,
      w.risk_urgency_weight,
      w.estimated_crew_days,
      w.earliest_eligible_wave,
      w.affected_customer_count,
      w.annual_revenue_at_risk,
      w.optimizer_version,
      w.solved_date
    FROM cdm_tmforum.copper_retirement.gold_wave_schedule w
    ORDER BY w.wave_year, w.wave_quarter, w.retirement_priority_rank
  `);
  return rows;
}

/**
 * Fetch wave summary aggregated by quarter and state.
 */
export async function fetchWaveSummary() {
  const rows = await executeSQL(`
    SELECT
      assigned_wave,
      wave_year,
      wave_quarter,
      state_code,
      COUNT(*) as wire_centers,
      SUM(copper_device_count) as total_devices,
      SUM(estimated_crew_days) as total_crew_days,
      SUM(affected_customer_count) as total_customers,
      ROUND(SUM(annual_revenue_at_risk), 0) as total_revenue_at_risk,
      ROUND(AVG(retirement_readiness_score), 1) as avg_readiness
    FROM cdm_tmforum.copper_retirement.gold_wave_schedule
    GROUP BY assigned_wave, wave_year, wave_quarter, state_code
    ORDER BY wave_year, wave_quarter, state_code
  `);
  return rows;
}

/**
 * Fetch contractor assignment plan overlay.
 */
export async function fetchContractorAssignments() {
  const rows = await executeSQL(`
    SELECT
      wave,
      state_code,
      contractor_id,
      contractor_name,
      contractor_type,
      primary_state,
      dispatch_status,
      crew_size,
      safety_score,
      overall_rating,
      sla_compliance_pct,
      composite_score,
      allocated_crew_days,
      estimated_cost_usd,
      wire_centers_in_wave,
      devices_in_wave,
      optimizer_version,
      assignment_date
    FROM cdm_tmforum.copper_retirement.gold_contractor_assignment_plan
    ORDER BY wave, state_code, composite_score DESC
  `);
  return rows;
}

/**
 * Compute KPIs from the wave schedule.
 */
export async function fetchPlanKPIs() {
  const rows = await executeSQL(`
    SELECT
      COUNT(*) as total_wire_centers,
      SUM(copper_device_count) as total_devices,
      SUM(affected_customer_count) as total_customers,
      ROUND(SUM(annual_revenue_at_risk), 0) as total_revenue_at_risk,
      SUM(estimated_crew_days) as total_crew_days,
      SUM(CASE WHEN fiber_ready THEN 1 ELSE 0 END) as fiber_ready_count,
      SUM(CASE WHEN puc_filing_required THEN 1 ELSE 0 END) as puc_required_count,
      ROUND(AVG(retirement_readiness_score), 1) as avg_readiness,
      COUNT(DISTINCT assigned_wave) as total_waves,
      COUNT(DISTINCT state_code) as total_states,
      MIN(assigned_wave) as first_wave,
      MAX(assigned_wave) as last_wave,
      SUM(critical_risk_devices) as total_critical_devices,
      SUM(high_risk_devices) as total_high_risk_devices
    FROM cdm_tmforum.copper_retirement.gold_wave_schedule
  `);
  return rows.length > 0 ? rows[0] : null;
}

/**
 * Fetch budget allocation by wave from retirement_plan + gold_wave_schedule.
 */
export async function fetchBudgetByWave() {
  const rows = await executeSQL(`
    SELECT
      rp.wave_label,
      rp.retirement_wave,
      COUNT(*) as wire_centers,
      ROUND(SUM(COALESCE(rp.budget_allocated, 0)), 0) as total_allocated,
      ROUND(SUM(COALESCE(rp.budget_spent, 0)), 0) as total_spent,
      ROUND(SUM(COALESCE(rp.budget_allocated, 0)) - SUM(COALESCE(rp.budget_spent, 0)), 0) as remaining,
      ROUND(SUM(COALESCE(rp.revenue_at_risk_mrr, 0)) * 12, 0) as annual_revenue_at_risk,
      SUM(COALESCE(rp.device_count, 0)) as total_devices,
      SUM(COALESCE(rp.customer_count, 0)) as total_customers,
      ROUND(AVG(COALESCE(rp.migration_pct_complete, 0)), 1) as avg_completion_pct
    FROM copper_app.retirement_plan rp
    GROUP BY rp.wave_label, rp.retirement_wave
    ORDER BY rp.retirement_wave
  `);
  return rows;
}

/**
 * Fetch regulatory checklist items, optionally filtered by wire_center_id.
 */
export async function fetchRegulatoryChecklist(wireCenterId) {
  const whereClause = wireCenterId
    ? `WHERE rc.wire_center_id = '${wireCenterId.replace(/'/g, "''")}'`
    : '';
  const rows = await executeSQL(`
    SELECT
      rc.checklist_id,
      rc.wire_center_id,
      rc.wire_center_name,
      rc.state_code,
      rc.checklist_item,
      rc.item_category,
      rc.description,
      rc.required,
      rc.required_notice_days,
      rc.deadline_date,
      rc.status,
      rc.assigned_to,
      rc.completed_date,
      rc.evidence_reference,
      rc.notes
    FROM copper_app.regulatory_checklist_status rc
    ${whereClause}
    ORDER BY rc.state_code, rc.wire_center_id, rc.item_category, rc.checklist_item
  `);
  return rows;
}

/**
 * Fetch retirement milestones for the CostBenefitPanel.
 */
export async function fetchMilestones(wireCenterId) {
  const whereClause = wireCenterId
    ? `WHERE rm.wire_center_id = '${wireCenterId.replace(/'/g, "''")}'`
    : '';
  const rows = await executeSQL(`
    SELECT
      rm.milestone_id,
      rm.wire_center_id,
      rm.name,
      rm.type,
      rm.status,
      rm.priority,
      rm.planned_date,
      rm.actual_date,
      rm.forecast_date,
      rm.completion_percentage,
      rm.critical_path_flag,
      rm.regulatory_requirement_flag,
      rm.risk_level,
      rm.risk_description
    FROM copper_app.retirement_milestones rm
    ${whereClause}
    ORDER BY rm.planned_date
  `);
  return rows;
}

/**
 * Health check.
 */
export async function healthCheck() {
  try {
    const rows = await executeSQL('SELECT 1 AS ok');
    return rows.length > 0 && rows[0].ok === '1';
  } catch {
    return false;
  }
}
