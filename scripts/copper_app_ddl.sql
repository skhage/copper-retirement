-- copper_app Lakebase schema DDL (ACC-QA-DEF-LAKEBASE-SYNC-SILENT-1107 part 1).
-- Generated 2026-11-07 by @devops from information_schema of the reference Lakebase project copper-task-board
-- (branch production, schema copper_app): 26 tables, 479 columns, 21 primary keys, 34 secondary indexes, 9 CHECK constraints.
-- Validated in a rolled-back transaction: 479/479 columns identical (name, position, type, nullability), 21 PKs,
-- 34/34 indexdefs identical, 9 CHECKs; applied twice without error. 1 FK intentionally omitted (see end of file).
-- Idempotent (IF NOT EXISTS) and NON-DESTRUCTIVE. Apply on a fresh partner Lakebase before lakebase_sync_job:
--   psql "host=<LAKEBASE_HOST> dbname=databricks_postgres sslmode=require" -f scripts/copper_app_ddl.sql
-- Sequence-backed integer ids are SERIAL. Tables hold app data; synthetic rows are labeled via is_synthetic where present.
-- telco_project=copper-retirement

CREATE SCHEMA IF NOT EXISTS copper_app;

CREATE TABLE IF NOT EXISTS copper_app."app_kpis" (
    "app_name" TEXT,
    "kpi_name" TEXT,
    "kpi_value" DOUBLE PRECISION,
    "kpi_label" TEXT,
    "kpi_unit" TEXT,
    "computed_at" TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY ("app_name", "kpi_name")
);

CREATE TABLE IF NOT EXISTS copper_app."commodity_forecast" (
    "forecast_month" TEXT,
    "region" TEXT,
    "copper_lme_forecast_usd_ton" DOUBLE PRECISION,
    "copper_comex_forecast_usd_lb" DOUBLE PRECISION,
    "fiber_cable_forecast_usd_km" DOUBLE PRECISION,
    "labor_cost_index_forecast" DOUBLE PRECISION,
    "material_cost_index_forecast" DOUBLE PRECISION,
    "model_version" TEXT,
    "forecast_generated_date" TEXT,
    PRIMARY KEY ("forecast_month", "region")
);

CREATE TABLE IF NOT EXISTS copper_app."commodity_forecast_versions" (
    "version_id" SERIAL,
    "forecast_date" TIMESTAMPTZ DEFAULT now(),
    "model_version" TEXT NOT NULL,
    "model_type" TEXT NOT NULL,
    "horizon_months" INTEGER NOT NULL,
    "forecast_snapshot" JSONB NOT NULL,
    "rmse" DOUBLE PRECISION,
    "mape" DOUBLE PRECISION,
    "training_data_end_date" DATE,
    "mlflow_run_id" TEXT,
    "notes" TEXT,
    PRIMARY KEY ("version_id")
);

CREATE TABLE IF NOT EXISTS copper_app."commodity_prices" (
    "price_date" DATE,
    "region" TEXT,
    "copper_lme_price_usd_ton" DOUBLE PRECISION,
    "copper_comex_price_usd_lb" DOUBLE PRECISION,
    "fiber_cable_price_usd_km" DOUBLE PRECISION,
    "labor_cost_index" DOUBLE PRECISION,
    "material_cost_index" DOUBLE PRECISION,
    PRIMARY KEY ("price_date", "region")
);

CREATE TABLE IF NOT EXISTS copper_app."contractor_scorecard" (
    "contractor_performance_id" BIGINT,
    "bp_agreement_id" BIGINT,
    "party_id" BIGINT,
    "contractor_name" TEXT,
    "contractor_type" TEXT,
    "certification_status" TEXT,
    "safety_score" NUMERIC(4,1),
    "osha_recordable_rate" NUMERIC(5,2),
    "incident_count" INTEGER,
    "at_fault_incident_count" INTEGER,
    "avg_resolution_time_hours" NUMERIC(6,1),
    "work_order_completion_rate" NUMERIC(5,2),
    "sla_compliance_pct" NUMERIC(5,2),
    "active_project_count" INTEGER,
    "crew_size" INTEGER,
    "primary_state" TEXT,
    "geographic_coverage_states" TEXT,
    "overall_rating" NUMERIC(3,1),
    "updated_at" TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY ("contractor_performance_id")
);

CREATE TABLE IF NOT EXISTS copper_app."device_risk_map" (
    "physical_device_id" BIGINT,
    "device_type" TEXT NOT NULL,
    "device_status" TEXT,
    "serial_number" TEXT,
    "latitude" DOUBLE PRECISION,
    "longitude" DOUBLE PRECISION,
    "state_code" TEXT,
    "wire_center_id" TEXT,
    "wire_center_name" TEXT,
    "risk_tier" TEXT,
    "risk_tier_predicted" TEXT,
    "composite_risk_score" DOUBLE PRECISION,
    "prob_critical" DOUBLE PRECISION,
    "prob_high" DOUBLE PRECISION,
    "prob_medium" DOUBLE PRECISION,
    "prob_low" DOUBLE PRECISION,
    "champion_prediction" TEXT,
    "champion_confidence" DOUBLE PRECISION,
    "models_agree" BOOLEAN,
    "h3_res8" TEXT,
    "h3_res9" TEXT,
    "updated_at" TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY ("physical_device_id")
);

CREATE TABLE IF NOT EXISTS copper_app."dig_incidents" (
    "incident_id" BIGINT,
    "work_id" BIGINT,
    "bp_agreement_id" BIGINT,
    "state" TEXT NOT NULL,
    "latitude" NUMERIC(9,6),
    "longitude" NUMERIC(9,6),
    "incident_date" DATE,
    "incident_timestamp" TIMESTAMPTZ,
    "severity" TEXT,
    "cable_type" TEXT,
    "cable_damage_type" TEXT,
    "root_cause" TEXT,
    "contractor_at_fault" BOOLEAN,
    "one_call_ticket_submitted" BOOLEAN,
    "resolution_time_hours" NUMERIC(6,1),
    "reroute_required" BOOLEAN,
    "service_interruption" BOOLEAN,
    "affected_pair_count" INTEGER,
    "repair_cost_amount" NUMERIC(10,2),
    "depth_of_cover_inches" NUMERIC(5,1),
    "triage_status" TEXT DEFAULT 'open',
    "triage_priority" INTEGER,
    "assigned_crew_id" TEXT,
    "updated_at" TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY ("incident_id")
);

CREATE TABLE IF NOT EXISTS copper_app."executive_summary" (
    "state_code" TEXT,
    "total_copper_devices" INTEGER,
    "active_devices" INTEGER,
    "critical_risk_count" INTEGER,
    "high_risk_count" INTEGER,
    "wire_center_count" INTEGER,
    "fiber_ready_devices" INTEGER,
    "fiber_ready_pct" DOUBLE PRECISION,
    "total_affected_services" INTEGER,
    "total_affected_customers" INTEGER,
    "voice_services_at_risk" INTEGER,
    "broadband_services_at_risk" INTEGER,
    "total_dig_incidents" INTEGER,
    "regulatory_violations" INTEGER,
    "total_repair_cost" DOUBLE PRECISION,
    "avg_resolution_hours" DOUBLE PRECISION,
    "available_contractors" INTEGER,
    "avg_contractor_rating" DOUBLE PRECISION,
    "total_crew_capacity" INTEGER,
    "preferred_contractors" INTEGER,
    "program_health_status" TEXT,
    "updated_at" TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY ("state_code")
);

CREATE TABLE IF NOT EXISTS copper_app."gold_contractor_assignment_plan" (
    "wave" TEXT,
    "state_code" TEXT,
    "contractor_id" BIGINT,
    "contractor_name" TEXT,
    "contractor_type" TEXT,
    "primary_state" TEXT,
    "dispatch_status" TEXT,
    "crew_size" BIGINT,
    "safety_score" DOUBLE PRECISION,
    "overall_rating" DOUBLE PRECISION,
    "sla_compliance_pct" DOUBLE PRECISION,
    "composite_score" DOUBLE PRECISION,
    "allocated_crew_days" BIGINT,
    "estimated_cost_usd" DOUBLE PRECISION,
    "wire_centers_in_wave" BIGINT,
    "devices_in_wave" BIGINT,
    "optimizer_version" TEXT,
    "assignment_date" TEXT
);

CREATE TABLE IF NOT EXISTS copper_app."gold_copper_recovery_schedule" (
    "wire_center_id" TEXT,
    "wire_center_name" TEXT,
    "state_code" TEXT,
    "assigned_wave" TEXT,
    "wave_year" BIGINT,
    "wave_quarter" BIGINT,
    "wave_start_date" TEXT,
    "fiber_ready" BOOLEAN,
    "puc_filing_required" BOOLEAN,
    "copper_device_count" BIGINT,
    "estimated_crew_days" BIGINT,
    "retirement_readiness_score" DOUBLE PRECISION,
    "retirement_priority_rank" BIGINT,
    "affected_customer_count" BIGINT,
    "annual_revenue_at_risk" DOUBLE PRECISION,
    "salvage_device_count" BIGINT,
    "total_device_weight_kg" DOUBLE PRECISION,
    "estimated_copper_weight_kg" DOUBLE PRECISION,
    "estimated_copper_weight_tons" DOUBLE PRECISION,
    "wave_lme_price_usd_ton" DOUBLE PRECISION,
    "wave_comex_price_usd_lb" DOUBLE PRECISION,
    "wave_labor_cost_index" DOUBLE PRECISION,
    "wave_material_cost_index" DOUBLE PRECISION,
    "gross_salvage_revenue_usd" DOUBLE PRECISION,
    "estimated_decommission_cost_usd" DOUBLE PRECISION,
    "net_salvage_value_usd" DOUBLE PRECISION,
    "salvage_timing_signal" TEXT,
    "generated_at" TIMESTAMP
);

CREATE TABLE IF NOT EXISTS copper_app."gold_reroute_options" (
    "physical_device_id" BIGINT,
    "device_type" TEXT,
    "device_status" TEXT,
    "state_code" TEXT,
    "city" TEXT,
    "addr_latitude" NUMERIC(18,2),
    "addr_longitude" NUMERIC(18,2),
    "addr_h3_res8" BIGINT,
    "wire_center_id" TEXT,
    "wire_center_name" TEXT,
    "clli_code" TEXT,
    "wire_center_fiber_ready" BOOLEAN,
    "computed_risk_tier" TEXT,
    "alarm_count" BIGINT,
    "critical_alarm_rate" NUMERIC(38,16),
    "test_fail_rate" NUMERIC(38,16),
    "annual_retire_priority" INTEGER,
    "puc_filing_required" BOOLEAN,
    "section_214_required" BOOLEAN,
    "affected_service_count" BIGINT,
    "service_roles" TEXT,
    "topology_graph_ids" TEXT,
    "graph_types" TEXT,
    "technology_layers" TEXT,
    "reroute_option_rank" INTEGER,
    "reroute_resource_id" BIGINT,
    "fiber_technology" TEXT,
    "fiber_resource_type" TEXT,
    "fiber_category" TEXT,
    "fiber_status" TEXT,
    "fiber_network_domain" TEXT,
    "fiber_site_name" TEXT,
    "fiber_site_type" TEXT,
    "fiber_state" TEXT,
    "fiber_latitude" NUMERIC(18,2),
    "fiber_longitude" NUMERIC(18,2),
    "fiber_h3_res8" BIGINT,
    "fiber_total_capacity" NUMERIC(20,2),
    "fiber_used_capacity" NUMERIC(20,2),
    "fiber_available_capacity" NUMERIC(20,2),
    "fiber_reserved_capacity" NUMERIC(20,2),
    "fiber_expansion_capacity" NUMERIC(20,2),
    "fiber_utilization_pct" NUMERIC(20,2),
    "fiber_capacity_health" TEXT,
    "fiber_migration_readiness" TEXT,
    "fiber_contention_ratio" NUMERIC(20,2),
    "fiber_is_shared" BOOLEAN,
    "reroute_feasibility_score" NUMERIC(29,2),
    "approx_distance_km" DOUBLE PRECISION,
    "reroute_readiness" TEXT,
    "_computed_at" TIMESTAMP
);

CREATE TABLE IF NOT EXISTS copper_app."gold_wave_schedule" (
    "wire_center_id" TEXT,
    "wire_center_name" TEXT,
    "state_code" TEXT,
    "assigned_wave" TEXT,
    "wave_year" BIGINT,
    "wave_quarter" BIGINT,
    "wave_start_date" TEXT,
    "fiber_ready" BOOLEAN,
    "puc_filing_required" BOOLEAN,
    "copper_device_count" BIGINT,
    "critical_risk_devices" BIGINT,
    "high_risk_devices" BIGINT,
    "retirement_readiness_score" DOUBLE PRECISION,
    "retirement_priority_rank" BIGINT,
    "risk_urgency_weight" DOUBLE PRECISION,
    "estimated_crew_days" BIGINT,
    "earliest_eligible_wave" TEXT,
    "affected_customer_count" BIGINT,
    "annual_revenue_at_risk" DOUBLE PRECISION,
    "optimizer_version" TEXT,
    "solved_date" TEXT
);

CREATE TABLE IF NOT EXISTS copper_app."incident_actions" (
    "action_id" SERIAL,
    "incident_id" TEXT NOT NULL,
    "action_timestamp" TIMESTAMPTZ DEFAULT now(),
    "action_type" TEXT NOT NULL,
    "agent_name" TEXT,
    "recommendation" JSONB,
    "human_decision" TEXT,
    "human_notes" TEXT,
    "confidence_score" DOUBLE PRECISION,
    "mlflow_trace_id" TEXT,
    PRIMARY KEY ("action_id")
);

CREATE TABLE IF NOT EXISTS copper_app."jurisdiction_requirements" (
    "jurisdiction_id" BIGINT,
    "state_code" TEXT NOT NULL,
    "puc_name" TEXT,
    "puc_short_name" TEXT,
    "governor_notice_days" INTEGER,
    "puc_notice_days" INTEGER,
    "residential_direct_notice_days" INTEGER,
    "tribal_notice_days" INTEGER,
    "section_214_required" BOOLEAN,
    "filing_type" TEXT,
    "e911_coordination_required" BOOLEAN,
    "backup_power_disclosure_required" BOOLEAN,
    "backup_power_minimum_hours" INTEGER,
    "public_notice_required" BOOLEAN,
    "updated_at" TIMESTAMPTZ DEFAULT now(),
    "dig_ticket_lead_time_days" NUMERIC,
    "dig_ticket_lead_time_unit" TEXT,
    "tolerance_zone_inches" NUMERIC,
    "positive_response_required" TEXT,
    "locate_validity_days" NUMERIC,
    "white_lining_required" TEXT,
    "emergency_dig_provision" TEXT,
    "lead_cable_state_rule" TEXT,
    "section_214_applicability" TEXT,
    "data_source_ids" TEXT,
    "verification_coverage_pct" NUMERIC,
    "last_synced_from_uc" TIMESTAMPTZ,
    PRIMARY KEY ("jurisdiction_id")
);

CREATE TABLE IF NOT EXISTS copper_app."jurisdiction_requirements_cited" (
    "requirement_key" TEXT,
    "jurisdiction_code" TEXT NOT NULL,
    "jurisdiction_name" TEXT,
    "jurisdiction_level" TEXT,
    "requirement_type" TEXT NOT NULL,
    "requirement_summary" TEXT,
    "value_numeric" DOUBLE PRECISION,
    "value_unit" TEXT,
    "verification_status" TEXT NOT NULL,
    "source_id" TEXT NOT NULL,
    "citation" TEXT,
    "official_url" TEXT NOT NULL,
    "register_verification_status" TEXT,
    "notes" TEXT,
    "is_synthetic" BOOLEAN DEFAULT false NOT NULL,
    "built_by" TEXT,
    "built_at" TIMESTAMPTZ,
    "synced_at" TIMESTAMPTZ DEFAULT now(),
    "citation_url" TEXT,
    "citation_url_verified_on" DATE,
    PRIMARY KEY ("requirement_key")
);

CREATE TABLE IF NOT EXISTS copper_app."plan_edit_audit_log" (
    "audit_id" SERIAL,
    "edit_timestamp" TIMESTAMPTZ DEFAULT now(),
    "edited_by" TEXT NOT NULL,
    "entity_type" TEXT NOT NULL,
    "entity_id" TEXT NOT NULL,
    "field_changed" TEXT NOT NULL,
    "old_value" TEXT,
    "new_value" TEXT,
    "edit_source" TEXT NOT NULL,
    PRIMARY KEY ("audit_id")
);

CREATE TABLE IF NOT EXISTS copper_app."regulatory_checklist_status" (
    "checklist_id" SERIAL,
    "wire_center_id" TEXT NOT NULL,
    "wire_center_name" TEXT,
    "state_code" TEXT NOT NULL,
    "checklist_item" TEXT NOT NULL,
    "item_category" TEXT NOT NULL,
    "description" TEXT,
    "required" BOOLEAN DEFAULT true NOT NULL,
    "required_notice_days" INTEGER,
    "deadline_date" DATE,
    "status" TEXT DEFAULT 'not_started' NOT NULL,
    "assigned_to" TEXT,
    "completed_date" DATE,
    "evidence_reference" TEXT,
    "notes" TEXT,
    "created_at" TIMESTAMPTZ DEFAULT now() NOT NULL,
    "updated_at" TIMESTAMPTZ DEFAULT now() NOT NULL,
    "is_synthetic" BOOLEAN DEFAULT false,
    "source_url" TEXT,
    PRIMARY KEY ("checklist_id")
);

CREATE TABLE IF NOT EXISTS copper_app."regulatory_documents" (
    "document_id" BIGINT,
    "docket_number" TEXT,
    "document_type" TEXT,
    "title" TEXT,
    "issuing_body" TEXT,
    "jurisdiction_state_code" TEXT,
    "issued_date" DATE,
    "effective_date" DATE,
    "document_status" TEXT,
    "regulatory_topic" TEXT,
    "summary_text" TEXT,
    "full_text_excerpt" TEXT,
    "citation_reference" TEXT,
    "related_docket_numbers" TEXT,
    "wire_center_references" TEXT,
    "carrier_name" TEXT,
    "notice_period_days" INTEGER,
    "word_count" INTEGER,
    "page_count" INTEGER,
    "updated_at" TIMESTAMPTZ DEFAULT now(),
    "is_synthetic" BOOLEAN,
    "source_id" TEXT,
    "source_url" TEXT,
    "record_class" TEXT,
    PRIMARY KEY ("document_id")
);

CREATE TABLE IF NOT EXISTS copper_app."retirement_milestones" (
    "milestone_id" BIGINT,
    "wire_center_id" TEXT NOT NULL,
    "name" TEXT,
    "type" TEXT,
    "status" TEXT,
    "priority" TEXT,
    "planned_date" DATE,
    "actual_date" DATE,
    "forecast_date" DATE,
    "completion_percentage" DOUBLE PRECISION,
    "critical_path_flag" BOOLEAN DEFAULT false,
    "regulatory_requirement_flag" BOOLEAN DEFAULT false,
    "risk_level" TEXT,
    "risk_description" TEXT,
    "updated_at" TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY ("milestone_id")
);

CREATE TABLE IF NOT EXISTS copper_app."retirement_plan" (
    "wire_center_id" TEXT,
    "wire_center_name" TEXT,
    "state_code" TEXT NOT NULL,
    "plan_status" TEXT DEFAULT 'planning',
    "retirement_wave" INTEGER,
    "wave_label" TEXT,
    "planned_start_date" DATE,
    "planned_end_date" DATE,
    "actual_start_date" DATE,
    "actual_end_date" DATE,
    "budget_allocated" NUMERIC(14,2),
    "budget_spent" NUMERIC(14,2),
    "revenue_at_risk_mrr" NUMERIC(12,2),
    "customer_count" INTEGER,
    "device_count" INTEGER,
    "critical_device_pct" DOUBLE PRECISION,
    "migration_pct_complete" DOUBLE PRECISION DEFAULT 0,
    "priority" TEXT,
    "risk_level" TEXT,
    "puc_filing_required" BOOLEAN,
    "puc_filing_status" TEXT,
    "section_214_required" BOOLEAN,
    "updated_at" TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY ("wire_center_id")
);

CREATE TABLE IF NOT EXISTS copper_app."revenue_at_risk_summary" (
    "wire_center_id" TEXT,
    "wire_center_name" TEXT,
    "state_code" TEXT,
    "device_type" TEXT,
    "computed_risk_tier" TEXT,
    "revenue_tier" TEXT,
    "action_priority" TEXT,
    "fiber_ready" BOOLEAN,
    "puc_filing_required" BOOLEAN,
    "circuit_count" INTEGER,
    "total_monthly_revenue" DOUBLE PRECISION,
    "total_annual_revenue" DOUBLE PRECISION,
    "avg_monthly_price" DOUBLE PRECISION,
    "updated_at" TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS copper_app."sell_hold_decisions" (
    "decision_id" SERIAL,
    "decision_date" TIMESTAMPTZ DEFAULT now(),
    "decided_by" TEXT NOT NULL,
    "wire_center_id" TEXT,
    "copper_volume_lbs" DOUBLE PRECISION,
    "forecast_price_per_lb" DOUBLE PRECISION,
    "decision" TEXT NOT NULL,
    "rationale" TEXT,
    "executed" BOOLEAN DEFAULT false,
    "executed_date" TIMESTAMPTZ,
    "actual_price_per_lb" DOUBLE PRECISION,
    PRIMARY KEY ("decision_id")
);

CREATE TABLE IF NOT EXISTS copper_app."triage_agent_sessions" (
    "session_id" SERIAL,
    "incident_id" TEXT NOT NULL,
    "session_start" TIMESTAMPTZ DEFAULT now(),
    "session_end" TIMESTAMPTZ,
    "agent_endpoint" TEXT NOT NULL,
    "mlflow_experiment_id" TEXT,
    "mlflow_run_id" TEXT,
    "mlflow_trace_id" TEXT,
    "input_summary" TEXT,
    "output_summary" TEXT,
    "tool_calls_count" INTEGER DEFAULT 0,
    "latency_ms" INTEGER,
    "status" TEXT,
    PRIMARY KEY ("session_id")
);

CREATE TABLE IF NOT EXISTS copper_app."wave_schedule_versions" (
    "version_id" SERIAL,
    "created_at" TIMESTAMPTZ DEFAULT now(),
    "created_by" TEXT DEFAULT 'system' NOT NULL,
    "trigger_type" TEXT NOT NULL,
    "wave_schedule_snapshot" JSONB NOT NULL,
    "risk_model_version" TEXT,
    "optimizer_params" JSONB,
    "notes" TEXT,
    PRIMARY KEY ("version_id")
);

CREATE TABLE IF NOT EXISTS copper_app."wire_center_boundaries" (
    "wire_center_id" TEXT,
    "wire_center_name" TEXT,
    "state_code" TEXT NOT NULL,
    "centroid_lat" DOUBLE PRECISION,
    "centroid_lon" DOUBLE PRECISION,
    "boundary_geojson" TEXT,
    "wire_center_type" TEXT,
    "copper_device_count" INTEGER,
    "estimated_copper_pairs" INTEGER,
    "fiber_ready" BOOLEAN,
    "annual_retire_priority" INTEGER,
    "puc_filing_required" BOOLEAN,
    "clli_code" TEXT,
    "area_sq_km" DOUBLE PRECISION,
    "updated_at" TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY ("wire_center_id")
);

CREATE TABLE IF NOT EXISTS copper_app."wire_center_scorecard" (
    "wire_center_id" TEXT,
    "wire_center_name" TEXT,
    "clli_code" TEXT,
    "state_code" TEXT,
    "fiber_ready" BOOLEAN,
    "puc_filing_required" BOOLEAN,
    "annual_retire_priority" INTEGER,
    "puc_name" TEXT,
    "section_214_required" BOOLEAN,
    "governor_notice_days" INTEGER,
    "puc_notice_days" INTEGER,
    "residential_direct_notice_days" INTEGER,
    "copper_device_count" INTEGER,
    "device_type_count" INTEGER,
    "active_device_count" INTEGER,
    "avg_alarm_count" DOUBLE PRECISION,
    "avg_critical_alarm_rate" DOUBLE PRECISION,
    "avg_sla_breach_rate" DOUBLE PRECISION,
    "critical_risk_devices" INTEGER,
    "high_risk_devices" INTEGER,
    "avg_distance_km" DOUBLE PRECISION,
    "bbox_min_lat" DOUBLE PRECISION,
    "bbox_max_lat" DOUBLE PRECISION,
    "bbox_min_lon" DOUBLE PRECISION,
    "bbox_max_lon" DOUBLE PRECISION,
    "affected_service_count" INTEGER,
    "affected_customer_count" INTEGER,
    "voice_services" INTEGER,
    "broadband_services" INTEGER,
    "fixed_line_services" INTEGER,
    "retirement_readiness_score" DOUBLE PRECISION,
    "retirement_priority_rank" INTEGER,
    "updated_at" TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY ("wire_center_id")
);

-- ---------------------------------------------------------------------------
-- Secondary indexes (ACC-QA-DEF-DDL-INDEXES-FK-1107): 34 non-PK btree indexes, copied verbatim
-- (pg_get_indexdef) from reference copper-task-board/production copper_app on 2026-11-07.
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_cp_region ON copper_app.commodity_prices USING btree (region);
CREATE INDEX IF NOT EXISTS idx_cs_rating ON copper_app.contractor_scorecard USING btree (overall_rating);
CREATE INDEX IF NOT EXISTS idx_cs_state ON copper_app.contractor_scorecard USING btree (primary_state);
CREATE INDEX IF NOT EXISTS idx_drm_h3 ON copper_app.device_risk_map USING btree (h3_res8);
CREATE INDEX IF NOT EXISTS idx_drm_risk ON copper_app.device_risk_map USING btree (risk_tier);
CREATE INDEX IF NOT EXISTS idx_drm_state ON copper_app.device_risk_map USING btree (state_code);
CREATE INDEX IF NOT EXISTS idx_drm_type ON copper_app.device_risk_map USING btree (device_type);
CREATE INDEX IF NOT EXISTS idx_di_date ON copper_app.dig_incidents USING btree (incident_date);
CREATE INDEX IF NOT EXISTS idx_di_severity ON copper_app.dig_incidents USING btree (severity);
CREATE INDEX IF NOT EXISTS idx_di_state ON copper_app.dig_incidents USING btree (state);
CREATE INDEX IF NOT EXISTS idx_di_status ON copper_app.dig_incidents USING btree (triage_status);
CREATE INDEX IF NOT EXISTS idx_gold_contractor_assignment_plan_state_code ON copper_app.gold_contractor_assignment_plan USING btree (state_code);
CREATE INDEX IF NOT EXISTS idx_gold_contractor_assignment_plan_wave ON copper_app.gold_contractor_assignment_plan USING btree (wave);
CREATE INDEX IF NOT EXISTS idx_gold_copper_recovery_schedule_assigned_wave ON copper_app.gold_copper_recovery_schedule USING btree (assigned_wave);
CREATE INDEX IF NOT EXISTS idx_gold_copper_recovery_schedule_wire_center_id ON copper_app.gold_copper_recovery_schedule USING btree (wire_center_id);
CREATE INDEX IF NOT EXISTS idx_gold_reroute_options_physical_device_id ON copper_app.gold_reroute_options USING btree (physical_device_id);
CREATE INDEX IF NOT EXISTS idx_gold_reroute_options_state_code ON copper_app.gold_reroute_options USING btree (state_code);
CREATE INDEX IF NOT EXISTS idx_gold_reroute_options_wire_center_id ON copper_app.gold_reroute_options USING btree (wire_center_id);
CREATE INDEX IF NOT EXISTS idx_gold_wave_schedule_assigned_wave ON copper_app.gold_wave_schedule USING btree (assigned_wave);
CREATE INDEX IF NOT EXISTS idx_gold_wave_schedule_state_code ON copper_app.gold_wave_schedule USING btree (state_code);
CREATE INDEX IF NOT EXISTS idx_gold_wave_schedule_wire_center_id ON copper_app.gold_wave_schedule USING btree (wire_center_id);
CREATE INDEX IF NOT EXISTS idx_jr_state ON copper_app.jurisdiction_requirements USING btree (state_code);
CREATE INDEX IF NOT EXISTS idx_reg_checklist_state ON copper_app.regulatory_checklist_status USING btree (state_code);
CREATE INDEX IF NOT EXISTS idx_reg_checklist_status ON copper_app.regulatory_checklist_status USING btree (status);
CREATE INDEX IF NOT EXISTS idx_reg_checklist_wc ON copper_app.regulatory_checklist_status USING btree (wire_center_id);
CREATE INDEX IF NOT EXISTS idx_rd_jurisdiction ON copper_app.regulatory_documents USING btree (jurisdiction_state_code);
CREATE INDEX IF NOT EXISTS idx_rd_topic ON copper_app.regulatory_documents USING btree (regulatory_topic);
CREATE INDEX IF NOT EXISTS idx_rd_type ON copper_app.regulatory_documents USING btree (document_type);
CREATE INDEX IF NOT EXISTS idx_rm_status ON copper_app.retirement_milestones USING btree (status);
CREATE INDEX IF NOT EXISTS idx_rm_wc ON copper_app.retirement_milestones USING btree (wire_center_id);
CREATE INDEX IF NOT EXISTS idx_rp_state ON copper_app.retirement_plan USING btree (state_code);
CREATE INDEX IF NOT EXISTS idx_rp_status ON copper_app.retirement_plan USING btree (plan_status);
CREATE INDEX IF NOT EXISTS idx_rp_wave ON copper_app.retirement_plan USING btree (retirement_wave);
CREATE INDEX IF NOT EXISTS idx_wcb_state ON copper_app.wire_center_boundaries USING btree (state_code);

-- ---------------------------------------------------------------------------
-- CHECK constraints (9, parity with reference). ADD CONSTRAINT has no IF NOT EXISTS, so each is
-- guarded on pg_constraint to keep this file idempotent.
-- ---------------------------------------------------------------------------
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'commodity_forecast_versions_model_type_check' AND conrelid = 'copper_app.commodity_forecast_versions'::regclass) THEN
    ALTER TABLE copper_app.commodity_forecast_versions ADD CONSTRAINT commodity_forecast_versions_model_type_check CHECK ((model_type = ANY (ARRAY['gbt'::text, 'prophet'::text, 'ensemble'::text])));
  END IF;
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'incident_actions_action_type_check' AND conrelid = 'copper_app.incident_actions'::regclass) THEN
    ALTER TABLE copper_app.incident_actions ADD CONSTRAINT incident_actions_action_type_check CHECK ((action_type = ANY (ARRAY['agent_recommendation'::text, 'human_approve'::text, 'human_reject'::text, 'human_override'::text, 'auto_dispatch'::text])));
  END IF;
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'plan_edit_audit_log_edit_source_check' AND conrelid = 'copper_app.plan_edit_audit_log'::regclass) THEN
    ALTER TABLE copper_app.plan_edit_audit_log ADD CONSTRAINT plan_edit_audit_log_edit_source_check CHECK ((edit_source = ANY (ARRAY['app_ui'::text, 'optimizer'::text, 'agent'::text, 'api'::text])));
  END IF;
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'plan_edit_audit_log_entity_type_check' AND conrelid = 'copper_app.plan_edit_audit_log'::regclass) THEN
    ALTER TABLE copper_app.plan_edit_audit_log ADD CONSTRAINT plan_edit_audit_log_entity_type_check CHECK ((entity_type = ANY (ARRAY['wire_center'::text, 'milestone'::text, 'wave'::text, 'budget'::text])));
  END IF;
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_category' AND conrelid = 'copper_app.regulatory_checklist_status'::regclass) THEN
    ALTER TABLE copper_app.regulatory_checklist_status ADD CONSTRAINT valid_category CHECK ((item_category = ANY (ARRAY['puc_filing'::text, 'fcc_filing'::text, 'customer_notice'::text, 'government_notice'::text, 'coordination'::text, 'disclosure'::text, 'public_notice'::text, 'documentation'::text])));
  END IF;
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_status' AND conrelid = 'copper_app.regulatory_checklist_status'::regclass) THEN
    ALTER TABLE copper_app.regulatory_checklist_status ADD CONSTRAINT valid_status CHECK ((status = ANY (ARRAY['not_started'::text, 'in_progress'::text, 'completed'::text, 'waived'::text, 'blocked'::text, 'not_applicable'::text])));
  END IF;
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'sell_hold_decisions_decision_check' AND conrelid = 'copper_app.sell_hold_decisions'::regclass) THEN
    ALTER TABLE copper_app.sell_hold_decisions ADD CONSTRAINT sell_hold_decisions_decision_check CHECK ((decision = ANY (ARRAY['sell_now'::text, 'hold'::text, 'partial_sell'::text])));
  END IF;
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'triage_agent_sessions_status_check' AND conrelid = 'copper_app.triage_agent_sessions'::regclass) THEN
    ALTER TABLE copper_app.triage_agent_sessions ADD CONSTRAINT triage_agent_sessions_status_check CHECK ((status = ANY (ARRAY['active'::text, 'completed'::text, 'error'::text, 'timeout'::text])));
  END IF;
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'wave_schedule_versions_trigger_type_check' AND conrelid = 'copper_app.wave_schedule_versions'::regclass) THEN
    ALTER TABLE copper_app.wave_schedule_versions ADD CONSTRAINT wave_schedule_versions_trigger_type_check CHECK ((trigger_type = ANY (ARRAY['optimizer'::text, 'manual_edit'::text, 'risk_model_update'::text])));
  END IF;
END $$;

-- ---------------------------------------------------------------------------
-- FOREIGN KEY intentionally OMITTED: reference has retirement_milestones_wire_center_id_fkey
--   FOREIGN KEY (wire_center_id) REFERENCES copper_app.retirement_plan(wire_center_id).
-- Reason: scripts/sync_gold_to_lakebase.py SYNC_SPECS loads retirement_milestones but NOT retirement_plan,
-- so on a fresh partner Lakebase retirement_plan is empty and the FK would make every milestone upsert fail.
-- Add it manually only after retirement_plan is seeded:
--   ALTER TABLE copper_app.retirement_milestones ADD CONSTRAINT retirement_milestones_wire_center_id_fkey
--     FOREIGN KEY (wire_center_id) REFERENCES copper_app.retirement_plan(wire_center_id);
-- ---------------------------------------------------------------------------
