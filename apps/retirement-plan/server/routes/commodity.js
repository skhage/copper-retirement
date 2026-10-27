/**
 * routes/commodity.js — Commodity & Value tab API (ACC-APP-PORT-COMMODITY).
 * Ported 2026-10-25 from the standalone commodity-dashboard app, whose server only returned Math.random() mock data.
 * The port replaces every mock with existing UC tables (nothing new created). Mounted at /api/commodity by server/server.js.
 *
 * Data (reused):
 *   ${FQ}.copper_commodity_price_official   REAL monthly IMF PCOPPUSDM via FRED (source_url per row)
 *   ${FQ}.gold_commodity_price_forecast     monthly forecaster output; synthetic flag read from the table COMMENT so the
 *                                           label flips by itself once DEC-COMMODITY-REAL-RETRAIN lands
 *   ${FQ}.roi_calculator_assumptions        low/base/high ROI inputs with source_url (PARTNER-PLAYBOOK §3, ACC-DA-ROI-CALC)
 *   ${FQ}.v_partner_value_wire_center       copper lbs (NIST Handbook 100 x SYNTHETIC plant), working lines, costs per WC
 *   ${FQ}.gold_contractor_scorecard         SYNTHETIC contractor workforce scorecard (footprint states)
 * User input goes through Statement API named parameters only.
 */
import express from 'express';
import { executeSQL } from '../databricksSQL.js';

const CATALOG = process.env.CATALOG || 'cdm_tmforum';
const SCHEMA = process.env.SCHEMA || 'copper_retirement';
const FQ = `${CATALOG}.${SCHEMA}`;
const FOOTPRINT = (process.env.FOOTPRINT_STATES || 'CO,MN,WA,OR,ID,AZ').split(',').map((s) => s.trim().toUpperCase()).filter((s) => /^[A-Z]{2}$/.test(s));
const FOOT_SQL = `(${FOOTPRINT.map((s) => `'${s}'`).join(',')})`; // whitelisted 2-letter codes only

const stateParam = (v) => (v && /^[A-Za-z]{2}$/.test(v) ? v.toUpperCase() : 'ALL');
const num = (v) => (v == null || v === '' ? null : Number(v));
const int = (v) => (v == null || v === '' ? 0 : parseInt(v, 10) || 0);
const bool = (v) => v === true || v === 'true';

async function fetchPrices(months) {
  const rows = await executeSQL(`
    SELECT CAST(price_month AS STRING) AS month, copper_price_usd_lb AS usd_lb, copper_price_usd_ton AS usd_ton,
      price_source, source_url, CAST(is_synthetic AS STRING) AS is_synthetic
    FROM ${FQ}.copper_commodity_price_official
    ORDER BY price_month DESC LIMIT :months`, [{ name: 'months', value: String(months), type: 'INT' }]);
  return rows.reverse().map((r) => ({
    month: r.month, usd_lb: num(r.usd_lb), usd_ton: num(r.usd_ton), source: r.price_source, source_url: r.source_url,
    is_synthetic: bool(r.is_synthetic),
  }));
}

async function fetchForecast() {
  const [meta = {}] = await executeSQL(`
    SELECT comment FROM ${CATALOG}.information_schema.tables
    WHERE table_schema = :schema AND table_name = 'gold_commodity_price_forecast'`, [{ name: 'schema', value: SCHEMA }]);
  const comment = meta.comment || '';
  // Synthetic unless the owning table says otherwise (charter: synthetic data must be labeled).
  // Project convention: comments start with 'SYNTHETIC DATA', 'DERIVED FROM SYNTHETIC', 'MIXED' or 'REAL'.
  const synthetic = !comment || /^\s*(SYNTHETIC|DERIVED FROM SYNTHETIC|MIXED)/i.test(comment);
  const rows = await executeSQL(`
    SELECT forecast_month AS month, ROUND(AVG(copper_lme_forecast_usd_ton), 1) AS usd_ton,
      ROUND(AVG(copper_lme_forecast_usd_ton) / 2204.62262, 4) AS usd_lb,
      MAX(model_version) AS model_version, MAX(forecast_generated_date) AS generated
    FROM ${FQ}.gold_commodity_price_forecast GROUP BY forecast_month ORDER BY forecast_month`);
  return {
    synthetic, table_comment: comment,
    model_version: rows[0]?.model_version || null, generated: rows[0]?.generated || null,
    points: rows.map((r) => ({ month: r.month, usd_lb: num(r.usd_lb), usd_ton: num(r.usd_ton) })),
  };
}

async function fetchAssumptions() {
  const rows = await executeSQL(`
    SELECT param_code, param_group, cable_gauge_awg, low_value, base_value, high_value, unit, source_url,
      CAST(is_synthetic AS STRING) AS is_synthetic, comment, CAST(updated_at AS STRING) AS updated_at
    FROM ${FQ}.roi_calculator_assumptions ORDER BY param_group, param_code, cable_gauge_awg`);
  return rows.map((r) => ({
    code: r.param_code, group: r.param_group, awg: r.cable_gauge_awg == null ? null : int(r.cable_gauge_awg),
    low: num(r.low_value), base: num(r.base_value), high: num(r.high_value), unit: r.unit,
    // Only http(s) values are citations; tokens like PARTNER_DISCOVERY_INPUT are labels, never rendered as links.
    source_url: /^https?:\/\//.test(r.source_url || '') ? r.source_url : null,
    source_label: /^https?:\/\//.test(r.source_url || '') ? null : r.source_url,
    is_synthetic: bool(r.is_synthetic), comment: r.comment, updated_at: r.updated_at,
  }));
}

async function fetchValue(state) {
  const p = [{ name: 'state', value: state }];
  const [t = {}] = await executeSQL(`
    SELECT COUNT(*) AS wire_centers, SUM(copper_lbs_estimated) AS copper_lbs, SUM(working_copper_lines) AS working_lines,
      SUM(customer_migration_cost_usd) AS migration_cost, SUM(decommission_cost_usd) AS decommission_cost,
      SUM(fiber_build_cost_usd) AS fiber_build_cost, SUM(customers_impacted) AS customers_impacted,
      SUM(customers_migrated) AS customers_migrated, SUM(is_retired) AS retired_wcs
    FROM ${FQ}.v_partner_value_wire_center
    WHERE state_code IN ${FOOT_SQL} AND (:state = 'ALL' OR state_code = :state)`, p);
  const waves = await executeSQL(`
    SELECT assigned_wave AS wave, COUNT(*) AS wcs, SUM(copper_lbs_estimated) AS copper_lbs,
      SUM(working_copper_lines) AS lines, SUM(customers_impacted) AS customers
    FROM ${FQ}.v_partner_value_wire_center
    WHERE state_code IN ${FOOT_SQL} AND (:state = 'ALL' OR state_code = :state)
    GROUP BY assigned_wave ORDER BY assigned_wave`, p);
  const wcs = await executeSQL(`
    SELECT wire_center_id, wire_center_name, state_code, assigned_wave, copper_lbs_estimated, working_copper_lines,
      CAST(fiber_ready AS STRING) AS fiber_ready, customers_impacted
    FROM ${FQ}.v_partner_value_wire_center
    WHERE state_code IN ${FOOT_SQL} AND (:state = 'ALL' OR state_code = :state)
    ORDER BY copper_lbs_estimated DESC LIMIT 15`, p);
  return {
    totals: {
      wire_centers: int(t.wire_centers), copper_lbs: num(t.copper_lbs) ?? 0, working_lines: int(t.working_lines),
      migration_cost: num(t.migration_cost) ?? 0, decommission_cost: num(t.decommission_cost) ?? 0,
      fiber_build_cost: num(t.fiber_build_cost) ?? 0, customers_impacted: int(t.customers_impacted),
      customers_migrated: int(t.customers_migrated), retired_wcs: int(t.retired_wcs),
    },
    waves: waves.map((r) => ({ wave: r.wave, wcs: int(r.wcs), copper_lbs: num(r.copper_lbs) ?? 0, lines: int(r.lines), customers: int(r.customers) })),
    wire_centers: wcs.map((r) => ({
      id: r.wire_center_id, name: r.wire_center_name, state: r.state_code, wave: r.assigned_wave,
      copper_lbs: num(r.copper_lbs_estimated) ?? 0, lines: int(r.working_copper_lines), fiber_ready: r.fiber_ready === 'true',
      customers: int(r.customers_impacted),
    })),
  };
}

async function fetchContractors(state) {
  const rows = await executeSQL(`
    SELECT contractor_name, contractor_type, primary_state, CAST(safety_score AS DOUBLE) AS safety,
      CAST(overall_rating AS DOUBLE) AS rating, CAST(actual_sla_compliance_pct AS DOUBLE) AS sla,
      actual_incident_count, CAST(insurance_expired AS STRING) AS insurance_expired, CAST(cert_risk AS STRING) AS cert_risk,
      dispatch_status
    FROM ${FQ}.gold_contractor_scorecard
    WHERE primary_state IN ${FOOT_SQL} AND (:state = 'ALL' OR primary_state = :state)
    ORDER BY overall_rating DESC, safety_score DESC LIMIT 10`, [{ name: 'state', value: state }]);
  return rows.map((r) => ({
    name: r.contractor_name, type: r.contractor_type, state: r.primary_state, safety: num(r.safety), rating: num(r.rating),
    sla: num(r.sla), incidents: int(r.actual_incident_count), insurance_expired: bool(r.insurance_expired),
    cert_risk: bool(r.cert_risk), dispatch: r.dispatch_status,
  }));
}

// ---------- router ----------
const router = express.Router();
const wrap = (fn) => (req, res) => fn(req, res).catch((err) => {
  console.error(`[accelerator:commodity] ${req.method} ${req.path}:`, err.message);
  const msg = String(err.message || '');
  const status = err.status || (/PERMISSION_DENIED|INSUFFICIENT_PERMISSIONS|does not have .*privilege/i.test(msg) ? 403 : 500);
  res.status(status).json({ error: status === 403 && !msg.startsWith('Data access pending') ? `Data access pending: ${msg}` : msg });
});

router.get('/prices', wrap(async (req, res) => {
  const months = Math.min(Math.max(parseInt(req.query.months, 10) || 60, 12), 600);
  const data = await fetchPrices(months);
  res.json({ success: true, synthetic: false, count: data.length, data });
}));
router.get('/forecast', wrap(async (_req, res) => {
  const data = await fetchForecast();
  res.json({ success: true, synthetic: data.synthetic, count: data.points.length, data });
}));
router.get('/assumptions', wrap(async (_req, res) => {
  const data = await fetchAssumptions();
  res.json({ success: true, count: data.length, data });
}));
router.get('/value', wrap(async (req, res) => {
  const data = await fetchValue(stateParam(req.query.state));
  res.json({ success: true, synthetic: true, data });
}));
router.get('/contractors', wrap(async (req, res) => {
  const data = await fetchContractors(stateParam(req.query.state));
  res.json({ success: true, synthetic: true, count: data.length, data });
}));
router.get('/filters', (_req, res) => res.json({ success: true, data: { footprint: FOOTPRINT } }));

export default router;
