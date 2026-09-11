-- triage_kpis.sql
-- Summary KPIs for the dig-safe triage console
-- Combines dig_safe_incident (when available) with existing work/alarm tables

-- Until dig_safe_incident table lands, KPIs from existing tables:
SELECT
  -- Work order KPIs (available NOW)
  (
    SELECT COUNT(*)
    FROM cdm_tmforum.tmf_enterprise.work
    WHERE type IN ('repair', 'emergency')
      AND status IN ('dispatched', 'in_progress')
  ) AS open_work_orders,

  (
    SELECT COUNT(*)
    FROM cdm_tmforum.tmf_enterprise.work
    WHERE type IN ('repair', 'emergency')
  ) AS total_repair_emergency,

  -- Copper alarm KPIs (available NOW)
  (
    SELECT COUNT(DISTINCT a.alarm_id)
    FROM cdm_tmforum.tmf_resource.alarm a
    JOIN cdm_tmforum.tmf_enterprise.physical_device pd
      ON a.physical_resource_id = pd.physical_device_id
    WHERE pd.device_type IN ('cpe', 'ont', 'olt', 'patch_panel')
      AND a.perceived_severity = 'critical'
  ) AS critical_copper_alarms,

  (
    SELECT COUNT(DISTINCT bp_agreement_id)
    FROM cdm_tmforum.tmf_businesspartner.bp_agreement
    WHERE status = 'active'
  ) AS active_contractors,

  -- Placeholder KPIs (populated once dig_safe_incident exists)
  0 AS open_incidents,
  0.0 AS avg_resolution_hours,
  0 AS reroutes_pending
