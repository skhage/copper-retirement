# UC Pages — Full Column Reference

**Generated:** 2026-09-14
**Schema:** `cdm_tmforum.copper_retirement`
**Purpose:** Complete column-level detail for UC Pages creation via Catalog Explorer UI.

---

## `bronze_copper_devices` (MATERIALIZED_VIEW)

> Bronze layer: copper-relevant physical devices filtered from TMF physical_device

**16 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `physical_device_id` | LONG | Unique identifier for the physical device from tmf_enterprise.physical_device. Primary key. FK to co |
| 2 | `device_type` | STRING | Type of copper network equipment: cpe (Customer Premises Equipment), ont (Optical Network Terminal), |
| 3 | `device_status` | STRING | Operational status of the device (e.g. active, decommissioned, maintenance). Sourced from physical_d |
| 4 | `serial_number` | STRING | Manufacturer-assigned serial number uniquely identifying the physical unit. |
| 5 | `firmware_version` | STRING | Current firmware version running on the device. Used for obsolescence risk assessment. |
| 6 | `manufacture_date` | STRING | Date the device was manufactured. Sourced from physical_device.commissioned_date. Older devices carr |
| 7 | `installation_date` | STRING | Date the device was installed in the field. Combined with manufacture_date to compute device age for |
| 8 | `geographic_address_id` | LONG | FK to tmf_shared.geographic_address. Links device to its physical location for geospatial analysis a |
| 9 | `h3_res8` | LONG | H3 resolution-8 hexagonal index of the device location from physical_device. Used for geospatial clu |
| 10 | `state_code` | STRING | US state abbreviation (CO, MN, WA, OR, ID, AZ — Lakelink legacy copper states) from geographic_addre |
| 11 | `city` | STRING | City name from geographic_address.locality. Used for local planning and grouping. |
| 12 | `addr_latitude` | DECIMAL | WGS-84 latitude of the device address. Confirmed valid US bounds. From geographic_address. |
| 13 | `addr_longitude` | DECIMAL | WGS-84 longitude of the device address. Confirmed valid US bounds. From geographic_address. |
| 14 | `addr_h3_res8` | LONG | H3 resolution-8 index computed from the address coordinates. May differ slightly from device-level h |
| 15 | `addr_h3_res9` | LONG | H3 resolution-9 index computed from the address coordinates. Finer-grained hex for micro-level spati |
| 16 | `_pipeline_ingested_at` | TIMESTAMP | DLP pipeline processing timestamp. Set to current_timestamp() at materialization time for data linea |

## `bronze_copper_services` (MATERIALIZED_VIEW)

> Bronze layer: copper-candidate customer-facing services

**12 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `customer_facing_service_id` | LONG | Unique identifier for the customer-facing service from tmf_service.customer_facing_service. PK. FK u |
| 2 | `service_type` | STRING | Type of copper-carried service: voice, fixed_line, or broadband. Clustered column. Determines impact |
| 3 | `service_status` | STRING | Current operational status of the service (e.g. active, suspended, terminated). Sourced from CFS.sta |
| 4 | `customer_id` | LONG | FK to tmf_customer.customer. Links the service to the subscribing customer for impact analysis. |
| 5 | `geographic_address_id` | LONG | FK to tmf_shared.geographic_address. Service delivery location used for geospatial correlation with  |
| 6 | `start_date` | STRING | Date the service was activated for the customer. Used to calculate service tenure. |
| 7 | `end_date` | STRING | Date the service was terminated or is scheduled to end. NULL for active services. |
| 8 | `h3_res8` | LONG | H3 resolution-8 hexagonal index of the service location. Used for spatial joins with device data. |
| 9 | `customer_name` | STRING | Customer display name from tmf_customer.customer.name. Denormalized for dashboard display. |
| 10 | `customer_segment` | STRING | Customer segment classification (e.g. residential, enterprise, government) from customer.segment_cla |
| 11 | `customer_type` | STRING | Customer account type from customer.type. Distinguishes individual vs business accounts. |
| 12 | `_pipeline_ingested_at` | TIMESTAMP | DLP pipeline processing timestamp for data lineage tracking. |

## `bronze_dig_safe_incidents` (MATERIALIZED_VIEW)

> Bronze layer: dig-safe incident registry with contractor enrichment

**28 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `incident_id` | LONG | Unique identifier for the dig-safe incident from dig_safe_incident source table. |
| 2 | `work_id` | LONG | FK to tmf_enterprise.work. Links the incident to the associated work order for context. |
| 3 | `bp_agreement_id` | LONG | FK to contractor_performance and tmf_businesspartner.bp_agreement. Identifies the contractor respons |
| 4 | `geographic_address_id` | LONG | FK to tmf_shared.geographic_address. Location of the incident for geospatial analysis. |
| 5 | `network_route_id` | LONG | FK to tmf_shared.network_route. Identifies the affected cable route segment. |
| 6 | `state` | STRING | US state abbreviation where the incident occurred (CO, MN, WA, OR, ID, AZ). Clustered column. |
| 7 | `latitude` | DECIMAL | WGS-84 latitude of the incident location for map plotting. |
| 8 | `longitude` | DECIMAL | WGS-84 longitude of the incident location for map plotting. |
| 9 | `incident_date` | DATE | Calendar date of the dig-safe incident. Used for trend analysis and contractor scoring windows. |
| 10 | `incident_timestamp` | TIMESTAMP | Precise timestamp of the incident for time-series analysis and SLA measurement. |
| 11 | `severity` | STRING | Incident severity level (e.g. minor, moderate, major, critical). Clustered column. Drives cost and p |
| 12 | `cable_type` | STRING | Type of cable damaged: copper, fiber, coax, etc. Filters relevant to copper retirement analysis. |
| 13 | `cable_damage_type` | STRING | Nature of the damage: cut, nick, crush, exposure, etc. Informs repair strategy and cost estimation. |
| 14 | `root_cause` | STRING | Root cause category of the incident (e.g. unmarked_utility, excavation_error, mapping_error). Feeds  |
| 15 | `contractor_at_fault` | BOOLEAN | TRUE if the contractor was determined to be at fault for the incident. Feeds violation flagging and  |
| 16 | `one_call_ticket_submitted` | BOOLEAN | TRUE if a One-Call/811 ticket was properly filed before excavation. FALSE triggers regulatory violat |
| 17 | `resolution_time_hours` | DECIMAL | Hours from incident occurrence to full resolution. Key SLA metric for contractor performance. |
| 18 | `reroute_required` | BOOLEAN | TRUE if the damage required traffic rerouting through alternate paths. Indicates higher-severity dis |
| 19 | `service_interruption` | BOOLEAN | TRUE if the incident caused customer-facing service interruption. Critical metric for impact assessm |
| 20 | `affected_pair_count` | INT | Number of copper cable pairs affected by the damage. Proxy for service impact scale. |
| 21 | `repair_cost_amount` | DECIMAL | Dollar cost of repairing the damage. Aggregated by contractor and state for financial reporting. |
| 22 | `depth_of_cover_inches` | DECIMAL | Depth of cover at the damage point in inches. Below-code depths indicate higher future risk. |
| 23 | `contractor_name` | STRING | Name of the contractor from contractor_performance table. Denormalized for reporting. |
| 24 | `contractor_type` | STRING | Type of contractor (e.g. general, utility_locator, boring). From contractor_performance. |
| 25 | `contractor_safety_score` | DECIMAL | Contractors pre-incident safety score (0-100) from contractor_performance. Context for at-fault asse |
| 26 | `contractor_overall_rating` | DECIMAL | Contractors pre-incident overall performance rating from contractor_performance. |
| 27 | `is_regulatory_violation` | BOOLEAN | Computed flag: TRUE when contractor_at_fault=TRUE AND one_call_ticket_submitted=FALSE. Indicates non |
| 28 | `_pipeline_ingested_at` | TIMESTAMP | DLP pipeline processing timestamp for data lineage tracking. |

## `contractor_performance` (MANAGED)

> Contractor performance baseline data — safety scores, project history, and operational metrics for fiber deployment contractors. Source for gold_contractor_scorecard DLP enrichment.

**27 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `contractor_performance_id` | LONG | PK. Unique identifier for this contractor performance record. |
| 2 | `bp_agreement_id` | LONG | FK to tmf_businesspartner.bp_agreement. Links to the governing business partner contract. |
| 3 | `party_id` | LONG | FK to tmf_enterprise.work via party_id. Used for work order metric joins. |
| 4 | `contractor_name` | STRING | Legal name of the contractor company. |
| 5 | `contractor_type` | STRING | Contractor specialization category (e.g. general, utility_locator, boring, splicing). |
| 6 | `certification_status` | STRING | Current certification status (certified, expired_certification, revoked). Determines dispatch eligib |
| 7 | `safety_score` | DECIMAL | Composite safety score (0-100). Threshold of 80 required for preferred dispatch status. |
| 8 | `osha_recordable_rate` | DECIMAL | OSHA Total Recordable Incident Rate. Lower is better. |
| 9 | `incident_count` | INT | Self-reported incident count. Compare with actual_incident_count from dig-safe data. |
| 10 | `at_fault_incident_count` | INT | Self-reported at-fault incident count. |
| 11 | `avg_resolution_time_hours` | DECIMAL | Self-reported average incident resolution time in hours. |
| 12 | `work_order_completion_rate` | DECIMAL | Self-reported work order completion rate (0-1). |
| 13 | `sla_compliance_pct` | DECIMAL | Self-reported SLA compliance percentage. Compare with actual_sla_compliance_pct in gold scorecard. |
| 14 | `active_project_count` | INT | Number of currently active copper retirement projects for this contractor. |
| 15 | `total_project_value` | DECIMAL | Aggregate dollar value of all assigned projects. |
| 16 | `crew_size` | INT | Number of field crew members available. Feeds state-level capacity planning. |
| 17 | `equipment_count` | INT | Count of major equipment units owned by the contractor. |
| 18 | `years_in_business` | INT | Contractor longevity in years. Reliability indicator. |
| 19 | `geographic_coverage_states` | STRING | Comma-separated US state codes where the contractor can operate. |
| 20 | `geographic_coverage_h3` | STRING | H3 hex cells representing the contractor geographic service area. |
| 21 | `primary_state` | STRING | US state where the contractor is primarily based. |
| 22 | `bonded_amount` | DECIMAL | Dollar amount of the contractor surety bond. |
| 23 | `insurance_expiry_date` | DATE | Date contractor insurance coverage expires. Past-due blocks dispatch. |
| 24 | `last_audit_date` | DATE | Date of the most recent compliance/safety audit. |
| 25 | `overall_rating` | DECIMAL | Composite performance rating (1.0-5.0). Threshold of 4.0 with safety >= 80 for preferred status. |
| 26 | `source` | STRING | Data provenance tag indicating the source system for this record. |
| 27 | `created_timestamp` | TIMESTAMP | Row creation timestamp for audit trail. |

## `copper_commodity_price` (MANAGED)

> Synthetic copper/fiber commodity price history (2020-2026) with regional labor cost breakdowns for Beat 4 commodity dashboard. Regions: CO, MN, WA, OR, ID, AZ (legacy copper states). Copper prices follow realistic LME/COMEX trends including COVID crash, 2021 super-cycle, and 2022-2026 stabilization. Generated by @data-engineer.

**7 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `price_date` | DATE | Trading date (business days only) |
| 2 | `region` | STRING | Legacy copper state (CO/MN/WA/OR/ID/AZ) |
| 3 | `copper_lme_price_usd_ton` | DOUBLE | London Metal Exchange copper price in USD per metric ton |
| 4 | `copper_comex_price_usd_lb` | DOUBLE | COMEX copper futures price in USD per pound |
| 5 | `fiber_cable_price_usd_km` | DOUBLE | Fiber optic cable installed cost in USD per kilometer |
| 6 | `labor_cost_index` | DOUBLE | Regional labor cost index (base 100 = Jan 2020 national average) |
| 7 | `material_cost_index` | DOUBLE | Material cost index tracking copper-correlated construction materials |

## `copper_customers_impacted` (METRIC_VIEW)

> Customer impact metrics for the Lakelink Fiber copper retirement program — tracks how many customers, services, and business segments are affected by planned copper decommissioning. Each row represents a device-to-service allocation, so customers with multiple services appear in multiple rows.

**19 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `State` | STRING | US state code where the impacted copper device is deployed |
| 2 | `Device Type` | STRING | Type of copper network equipment affecting the customer |
| 3 | `Risk Tier` | STRING | Risk tier of the copper device impacting this customer — Critical devices require immediate migratio |
| 4 | `Service Type` | STRING | Type of customer-facing service at risk: Voice (POTS/VoIP), Fixed Line (dedicated circuits), Broadba |
| 5 | `Customer Segment` | STRING | Business segment of the impacted customer |
| 6 | `Impact Category` | STRING | Category of service disruption the customer would face if the copper device is retired without migra |
| 7 | `Service Status` | STRING | Current lifecycle status of the customer-facing service |
| 8 | `Wire Center` | STRING | Wire center (central office) serving this customer allocation |
| 9 | `Criticality Level` | STRING | Criticality level of the device-service allocation — how important this specific service link is |
| 10 | `Customers Impacted` | LONG | Unique customers impacted by copper retirement — the primary customer impact headline metric |
| 11 | `Services at Risk` | LONG | Unique customer-facing services that depend on copper infrastructure and face disruption risk |
| 12 | `Devices Impacting Customers` | LONG | Unique copper devices that have customer service allocations — devices with direct customer impact |
| 13 | `Total Allocations` | LONG | Total device-to-service allocations — one device can serve multiple services |
| 14 | `Voice Services at Risk` | LONG | Voice services (POTS/VoIP) at risk from copper retirement — often subject to regulatory notice requi |
| 15 | `Broadband Services at Risk` | LONG | Broadband services at risk from copper retirement |
| 16 | `Fixed Line Services at Risk` | LONG | Fixed line (dedicated circuit) services at risk from copper retirement |
| 17 | `Residential Customers` | LONG | Residential customers impacted — subject to FCC 90-day direct notice requirement (FCC 26-19) |
| 18 | `Enterprise Customers` | LONG | Enterprise customers impacted by copper retirement — typically higher revenue per customer |
| 19 | `Critical Impact Customers` | LONG | Customers served by critical-risk copper devices requiring immediate migration attention |

## `copper_ebitda_impact_achieved` (METRIC_VIEW)

> EBITDA and revenue impact metrics for the Lakelink Fiber copper retirement program — quantifies annual revenue at risk, operating cost savings from decommissioning, and net financial impact by geography, risk tier, and action priority. Each row represents one copper circuit with its associated revenue and cost data.

**22 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `State` | STRING | US state code where the copper circuit is deployed |
| 2 | `Device Type` | STRING | Type of copper equipment serving this circuit |
| 3 | `Risk Tier` | STRING | Computed risk tier from plant health metrics — drives retirement prioritization and EBITDA timing |
| 4 | `ML Risk Tier` | STRING | ML model predicted risk tier (V5 model) — more granular than computed tier, includes medium and high |
| 5 | `Revenue Tier` | STRING | Revenue classification of the circuit: High Value (top revenue circuits), Medium Value, Standard |
| 6 | `Action Priority` | STRING | Recommended action priority for retirement: Immediate Action (critical risk + high value), High Prio |
| 7 | `Fiber Ready` | STRING | Whether the wire center has fiber infrastructure ready — fiber-ready circuits can migrate faster wit |
| 8 | `Technology Domain` | STRING | Network technology domain of the circuit (e.g., copper_dsl, copper_pots, 5g_nr, gpon) |
| 9 | `Circuit Lifecycle` | STRING | Current lifecycle stage of the circuit — Active circuits generate revenue; Retired circuits represen |
| 10 | `PUC Filing Required` | STRING | Whether state Public Utility Commission filing is required before retirement — affects timeline and  |
| 11 | `Total Annual Revenue at Risk` | DOUBLE | Total annualized revenue from copper circuits at risk of retirement — the headline financial exposur |
| 12 | `Total Monthly Revenue at Risk` | DOUBLE | Monthly recurring revenue from copper circuits — the run-rate financial exposure |
| 13 | `Total Billed Amount` | DOUBLE | Total billed operating cost for copper circuits — represents cost savings potential when circuits ar |
| 14 | `Total Circuits` | LONG | Total number of copper circuits in the revenue-at-risk analysis |
| 15 | `Avg Revenue per Circuit` | DOUBLE | Average annual revenue per copper circuit — used to estimate per-unit EBITDA impact of retirement |
| 16 | `High Value Circuits` | LONG | Circuits classified as high-value — these require careful migration to retain revenue |
| 17 | `High Value Revenue` | DOUBLE | Annual revenue from high-value circuits — the most important revenue to retain during migration |
| 18 | `Immediate Action Revenue` | DOUBLE | Revenue from circuits requiring immediate retirement action — the most urgent financial exposure |
| 19 | `Critical Risk Revenue` | DOUBLE | Revenue from critical-risk circuits — highest probability of service degradation |
| 20 | `Avg ML Composite Risk Score` | DOUBLE | Average ML composite risk score across circuits — higher values indicate greater retirement urgency |
| 21 | `Fiber Ready Revenue` | DOUBLE | Revenue from circuits in fiber-ready wire centers — can be migrated with minimal capex |
| 22 | `PUC Filing Revenue` | DOUBLE | Revenue from circuits requiring PUC regulatory filing — these have longer retirement timelines |

## `copper_loop_plant` (MANAGED)

> Physical copper cable pair inventory — gauge, length, splice points, test results, and moisture status per cable pair. Grain: one row per copper pair.

**22 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `copper_pair_id` | LONG | PK. Unique identifier for this copper cable pair. |
| 2 | `cable_segment_id` | STRING | Identifier for the cable segment containing this pair. Groups pairs in the same physical cable. |
| 3 | `physical_device_id` | LONG | FK to tmf_enterprise.physical_device. The device this copper pair connects to. |
| 4 | `geographic_address_id` | LONG | FK to tmf_shared.geographic_address. Physical location of this copper pair endpoint. |
| 5 | `cable_gauge_awg` | INT | American Wire Gauge of the copper conductor. Common values: 19, 22, 24, 26. Lower gauge = thicker wi |
| 6 | `pair_count_in_cable` | INT | Total number of copper pairs in the parent cable. Typical: 25, 50, 100, 200, 400, 600. |
| 7 | `pair_number` | INT | Sequential pair number within the cable (1 to pair_count_in_cable). |
| 8 | `segment_length_ft` | DOUBLE | Length of this cable segment in feet. Individual segment of the loop. |
| 9 | `loop_length_ft` | DOUBLE | Total copper loop length from CO to customer in feet. Longer loops = more signal attenuation. |
| 10 | `splice_point_count` | INT | Number of splices in this pair run. More splices = more failure points and signal degradation. |
| 11 | `pedestal_id` | STRING | Identifier of the serving pedestal (outdoor distribution point) for this pair. |
| 12 | `terminal_id` | STRING | Identifier of the terminal block where this pair terminates. |
| 13 | `cable_type` | STRING | Cable construction type (e.g. aerial, buried, underground). Affects retirement method and cost. |
| 14 | `cable_vintage_year` | INT | Year the cable was manufactured/installed. Older vintage = higher degradation risk. |
| 15 | `insulation_type` | STRING | Cable insulation material (e.g. paper_pulp, PIC_plastic, gel_filled). Paper pulp is oldest and most  |
| 16 | `pair_status` | STRING | Current operational status of this copper pair (e.g. working, spare, defective, test_failed). |
| 17 | `last_test_date` | DATE | Date of the most recent line test on this pair. |
| 18 | `test_result_db_loss` | DOUBLE | Most recent test result: decibel loss. Higher dB loss = worse signal quality. |
| 19 | `resistance_ohms_per_kft` | DOUBLE | DC loop resistance in ohms per 1000 feet. Higher resistance indicates corrosion or damage. |
| 20 | `moisture_detected` | BOOLEAN | TRUE if moisture was detected in the cable sheath during testing. Major degradation indicator. |
| 21 | `source` | STRING | Data provenance tag for this record. |
| 22 | `created_timestamp` | TIMESTAMP | Row creation timestamp. |

## `copper_plant_wire_center_jurisdiction` (MANAGED)

> Denormalized copper plant view joining cable pairs, physical devices, wire center boundaries, and state PUC jurisdiction requirements. Primary lookup table for DLP silver layer.

**51 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `copper_pair_id` | LONG | FK to copper_loop_plant. The copper cable pair at this location. |
| 2 | `cable_segment_id` | STRING | Cable segment ID grouping pairs in the same physical cable. |
| 3 | `physical_device_id` | LONG | FK to physical_device. The copper device at this address. Key join for DLP silver layer. |
| 4 | `geographic_address_id` | LONG | FK to geographic_address. Physical location of the copper pair endpoint. |
| 5 | `state_code` | STRING | US state abbreviation from geographic_address. |
| 6 | `addr_lat` | DECIMAL | WGS-84 latitude of the address. |
| 7 | `addr_lon` | DECIMAL | WGS-84 longitude of the address. |
| 8 | `addr_h3_res8` | LONG | H3 resolution-8 hex index computed from address coordinates. |
| 9 | `addr_h3_res9` | LONG | H3 resolution-9 hex index computed from address coordinates. |
| 10 | `wire_center_id` | STRING | ID of the serving wire center. Joined from wire_center_boundary via H3 spatial proximity. |
| 11 | `wire_center_name` | STRING | Human-readable name of the serving wire center. |
| 12 | `clli_code` | STRING | CLLI code of the wire center. Standard telecom facility identifier. |
| 13 | `wire_center_type` | STRING | Wire center facility type (e.g. central_office, remote_terminal). |
| 14 | `fiber_ready` | BOOLEAN | TRUE if the wire center has fiber infrastructure ready for migration. |
| 15 | `backup_power` | BOOLEAN | TRUE if the wire center has backup power generation capability. |
| 16 | `annual_retire_priority` | INT | Planned retirement year priority rank (1=soonest). |
| 17 | `puc_filing_required` | BOOLEAN | TRUE if PUC filing is required before retirement in this jurisdiction. |
| 18 | `wc_copper_device_count` | INT | Total copper devices served by this wire center. |
| 19 | `wc_estimated_copper_pairs` | INT | Estimated total copper pairs served by this wire center. |
| 20 | `wc_area_sq_km` | DOUBLE | Service area of the wire center in square kilometers. |
| 21 | `wc_centroid_lat` | DOUBLE | Latitude of the wire center geographic centroid. |
| 22 | `wc_centroid_lon` | DOUBLE | Longitude of the wire center geographic centroid. |
| 23 | `wc_h3_res7` | STRING | H3 resolution-7 hex of the wire center centroid. Coarser grain for regional analysis. |
| 24 | `distance_to_wire_center_km` | DOUBLE | Straight-line distance from the copper pair address to its wire center in km. |
| 25 | `cable_gauge_awg` | INT | AWG of the copper conductor. Lower = thicker = better signal. |
| 26 | `pair_count_in_cable` | INT | Total pairs in the parent cable. |
| 27 | `segment_length_ft` | DOUBLE | Length of this cable segment in feet. |
| 28 | `loop_length_ft` | DOUBLE | Total copper loop length from CO to customer in feet. |
| 29 | `splice_point_count` | INT | Number of splices in this pair run. |
| 30 | `cable_type` | STRING | Cable construction type (aerial, buried, underground). |
| 31 | `cable_vintage_year` | INT | Year the cable was installed. |
| 32 | `insulation_type` | STRING | Cable insulation material (paper_pulp, PIC_plastic, gel_filled). |
| 33 | `pair_status` | STRING | Operational status of this copper pair. |
| 34 | `last_test_date` | DATE | Date of the most recent line test. |
| 35 | `test_result_db_loss` | DOUBLE | Most recent test result: decibel loss. |
| 36 | `resistance_ohms_per_kft` | DOUBLE | DC loop resistance in ohms per 1000 feet. |
| 37 | `moisture_detected` | BOOLEAN | TRUE if moisture detected in the cable sheath. |
| 38 | `jurisdiction_id` | LONG | FK to state_puc_jurisdiction_requirements. PUC regulatory jurisdiction. |
| 39 | `puc_name` | STRING | Full name of the state Public Utilities Commission. |
| 40 | `puc_short_name` | STRING | Abbreviated PUC name for dashboards. |
| 41 | `governor_notice_days` | LONG | Required advance notice days to the governor before copper retirement. |
| 42 | `puc_notice_days` | LONG | Required advance notice days to the PUC. |
| 43 | `residential_direct_notice_days` | LONG | Required advance direct notice days to residential customers. |
| 44 | `tribal_notice_days` | LONG | Required advance notice days to tribal authorities. |
| 45 | `section_214_required` | BOOLEAN | TRUE if FCC Section 214 discontinuance authorization required. |
| 46 | `filing_type` | STRING | Type of regulatory filing required (e.g. full, streamlined, notification). |
| 47 | `e911_coordination_required` | BOOLEAN | TRUE if E911 service coordination is required before copper retirement. |
| 48 | `backup_power_disclosure_required` | BOOLEAN | TRUE if backup power compliance disclosure is required. |
| 49 | `backup_power_minimum_hours` | LONG | Minimum backup power hours required by regulation. |
| 50 | `public_notice_required` | BOOLEAN | TRUE if a public notice must be published before retirement. |
| 51 | `created_timestamp` | TIMESTAMP | Row creation timestamp. |

## `copper_retirement_project_status` (METRIC_VIEW)

> Copper retirement project status KPIs — tracks device inventory, retirement progress, risk distribution, and fiber readiness across the Lakelink Fiber network. Source of truth for executive status reporting on the copper decommissioning program.

**18 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `State` | STRING | US state code where the copper device is deployed |
| 2 | `Device Type` | STRING | Type of copper network equipment: CPE (Customer Premises Equipment), OLT (Optical Line Terminal), ON |
| 3 | `Risk Tier` | STRING | Computed risk tier for copper retirement prioritization based on alarm rates, SLA breaches, and serv |
| 4 | `Device Status` | STRING | Current operational status of the device: Installed (in-field, working), Active (in service), Faulty |
| 5 | `Fiber Ready` | STRING | Whether the wire center serving this device has fiber infrastructure ready for migration |
| 6 | `Wire Center` | STRING | Wire center (central office) serving this copper device |
| 7 | `City` | STRING | City where the copper device is located |
| 8 | `Total Copper Devices` | LONG | Total count of copper network devices in the retirement program |
| 9 | `Active Devices` | LONG | Devices currently installed or active in the network — these require migration before retirement |
| 10 | `Faulty Devices` | LONG | Devices flagged as faulty — highest urgency for retirement or replacement |
| 11 | `Critical Risk Devices` | LONG | Devices in the critical risk tier requiring immediate retirement action |
| 12 | `Fiber Ready Devices` | LONG | Copper devices in wire centers where fiber infrastructure is already deployed — ready for migration |
| 13 | `Fiber Ready Pct` | DECIMAL | Percentage of copper devices located in fiber-ready wire centers |
| 14 | `Critical Risk Pct` | DECIMAL | Percentage of devices in the critical risk tier |
| 15 | `Avg Alarm Count` | DOUBLE | Average number of alarms per copper device — higher values indicate degrading plant health |
| 16 | `Total Problem Count` | LONG | Total reported problems across all copper devices |
| 17 | `Avg SLA Breach Rate` | DECIMAL | Average SLA breach rate across copper devices — key quality indicator for retirement urgency |
| 18 | `Unique Wire Centers` | LONG | Number of distinct wire centers with copper devices — indicates geographic spread of retirement prog |

## `copper_risk_predictions` (MANAGED)

> ML model predictions for copper device risk tier classification. Contains predicted probabilities for each risk tier (low/medium/high/critical) per device.

**13 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `physical_device_id` | LONG | FK to physical_device. The device being scored. |
| 2 | `device_type` | STRING | Copper device type: cpe, ont, olt, or patch_panel. |
| 3 | `device_status` | STRING | Operational status of the device. |
| 4 | `risk_tier` | STRING | Ground truth risk tier label from copper_risk_target. |
| 5 | `predicted_risk_tier` | STRING | ML model-predicted risk tier (low/medium/high/critical). |
| 6 | `prob_low` | DOUBLE | Predicted probability for low risk tier (0.0-1.0). |
| 7 | `prob_medium` | DOUBLE | Predicted probability for medium risk tier (0.0-1.0). |
| 8 | `prob_high` | DOUBLE | Predicted probability for high risk tier (0.0-1.0). |
| 9 | `prob_critical` | DOUBLE | Predicted probability for critical risk tier (0.0-1.0). |
| 10 | `max_confidence` | DOUBLE | Maximum of prob_low/medium/high/critical. Model confidence in its prediction. |
| 11 | `model_version` | LONG | Model version number that produced this prediction. |
| 12 | `model_run_id` | STRING | MLflow run ID of the model that produced this prediction. Lineage link. |
| 13 | `scored_at` | TIMESTAMP | Timestamp when this prediction was generated. |

## `copper_risk_scores` (MANAGED)

> Champion-vs-challenger model comparison for copper device risk scoring. Shows both models'' predictions and whether they agree.

**9 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `physical_device_id` | LONG | FK to physical_device. The device being scored. |
| 2 | `device_type` | STRING | Copper device type. |
| 3 | `device_status` | STRING | Operational status of the device. |
| 4 | `risk_tier` | STRING | Ground truth risk tier from copper_risk_target. |
| 5 | `champion_prediction` | STRING | Risk tier predicted by the champion (production) model. |
| 6 | `champion_confidence` | DOUBLE | Champion model confidence in its prediction (0.0-1.0). |
| 7 | `challenger_prediction` | STRING | Risk tier predicted by the challenger model. |
| 8 | `challenger_confidence` | FLOAT | Challenger model confidence in its prediction (0.0-1.0). |
| 9 | `models_agree` | BOOLEAN | TRUE if champion and challenger predict the same risk tier. Disagreement flags for review. |

## `copper_risk_target` (MANAGED)

> ML training/scoring target table — risk feature engineering per physical device. Contains alarm rates, SLA breach rates, test results, and composite risk scores.

**20 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `physical_device_id` | LONG | PK. FK to physical_device. The copper device being scored for risk. |
| 2 | `device_type` | STRING | Copper device type: cpe, ont, olt, or patch_panel. |
| 3 | `device_status` | STRING | Operational status of the device. |
| 4 | `alarm_count` | LONG | Total alarms recorded for this device across all severity levels. |
| 5 | `critical_alarm_rate` | DECIMAL | Fraction of alarms classified as critical (0.0-1.0). Key risk input. |
| 6 | `service_affecting_rate` | DECIMAL | Fraction of alarms that impacted customer service (0.0-1.0). |
| 7 | `sla_breach_count` | LONG | Number of SLA breaches associated with this device. |
| 8 | `sla_breach_rate` | DECIMAL | Fraction of service events that breached SLA (0.0-1.0). |
| 9 | `test_fail_rate` | DECIMAL | Fraction of loopback/BERT tests that failed (0.0-1.0). Measures physical line condition. |
| 10 | `problem_count` | LONG | Total service problems attributed to this device. |
| 11 | `recurring_problem_rate` | DECIMAL | Fraction of problems that recurred after resolution (0.0-1.0). |
| 12 | `alarm_count_prank` | DOUBLE | Percentile rank of alarm_count across all devices (0.0-1.0). ML feature. |
| 13 | `critical_alarm_prank` | DOUBLE | Percentile rank of critical_alarm_rate. ML feature. |
| 14 | `svc_affecting_prank` | DOUBLE | Percentile rank of service_affecting_rate. ML feature. |
| 15 | `sla_breach_prank` | DOUBLE | Percentile rank of sla_breach_rate. ML feature. |
| 16 | `test_fail_prank` | DOUBLE | Percentile rank of test_fail_rate. ML feature. |
| 17 | `problem_count_prank` | DOUBLE | Percentile rank of problem_count. ML feature. |
| 18 | `recurring_prob_prank` | DOUBLE | Percentile rank of recurring_problem_rate. ML feature. |
| 19 | `composite_risk_score` | DOUBLE | Weighted composite of all percentile ranks (0.0-1.0). Higher = higher risk. Primary ML target. |
| 20 | `risk_tier` | STRING | Derived risk classification based on composite_risk_score: critical, high, medium, low. ML label. |

## `dig_safe_incident` (MANAGED)

> Source table for dig-safe excavation incidents. Each row = one incident with damage details, contractor accountability, and repair costs.

**24 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `incident_id` | LONG | PK. Unique identifier for this dig-safe incident. |
| 2 | `work_id` | LONG | FK to tmf_enterprise.work. Associated work order. |
| 3 | `bp_agreement_id` | LONG | FK to bp_agreement. Contractor responsible for the dig activity. |
| 4 | `geographic_address_id` | LONG | FK to geographic_address. Incident location. |
| 5 | `network_route_id` | LONG | FK to network_route. Affected cable route. |
| 6 | `state` | STRING | US state abbreviation where the incident occurred. |
| 7 | `latitude` | DECIMAL | WGS-84 latitude of the incident for map plotting. |
| 8 | `longitude` | DECIMAL | WGS-84 longitude of the incident for map plotting. |
| 9 | `incident_date` | DATE | Calendar date of the incident. |
| 10 | `incident_timestamp` | TIMESTAMP | Precise timestamp of the incident. |
| 11 | `severity` | STRING | Severity level (minor, moderate, major, critical). |
| 12 | `cable_type` | STRING | Type of cable damaged (copper, fiber, coax). |
| 13 | `cable_damage_type` | STRING | Nature of the damage (cut, nick, crush, exposure). |
| 14 | `root_cause` | STRING | Root cause category (unmarked_utility, excavation_error, mapping_error). |
| 15 | `contractor_at_fault` | BOOLEAN | TRUE if contractor determined at fault. |
| 16 | `one_call_ticket_submitted` | BOOLEAN | TRUE if One-Call/811 ticket was properly filed before excavation. |
| 17 | `resolution_time_hours` | DECIMAL | Hours from incident to resolution. SLA metric. |
| 18 | `reroute_required` | BOOLEAN | TRUE if traffic rerouting was needed. |
| 19 | `service_interruption` | BOOLEAN | TRUE if customer-facing service was interrupted. |
| 20 | `affected_pair_count` | INT | Number of cable pairs affected. |
| 21 | `repair_cost_amount` | DECIMAL | Dollar cost of repair. |
| 22 | `depth_of_cover_inches` | DECIMAL | Depth of cover at damage point in inches. |
| 23 | `source` | STRING | Data provenance tag. |
| 24 | `created_timestamp` | TIMESTAMP | Row creation timestamp. |

## `fcc_bdc_provider_coverage` (MANAGED)

> Synthetic FCC Broadband Data Collection (BDC) provider coverage. Each row = one provider technology offering at one BSL. Shows copper vs fiber availability per location for migration planning.

**21 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `bdc_record_id` | INT | PK. Unique record ID within the BDC filing. |
| 2 | `location_id` | LONG | FK to fcc_fabric_location. The BSL this coverage record applies to. |
| 3 | `provider_name` | STRING | Name of the broadband provider (e.g. Lakelink Fiber, competitor names). |
| 4 | `provider_id` | STRING | FCC-assigned provider identifier (FRN or similar). |
| 5 | `technology` | STRING | Broadband technology description (e.g. Copper Wire, Optical Carrier/Fiber, Cable Modem). |
| 6 | `technology_code` | INT | FCC technology code (10=DSL/copper, 50=fiber, 40=cable, etc.). |
| 7 | `max_download_mbps` | INT | Maximum advertised download speed in Mbps. |
| 8 | `max_upload_mbps` | INT | Maximum advertised upload speed in Mbps. |
| 9 | `latency_ms` | INT | Reported latency in milliseconds. |
| 10 | `is_copper_service` | BOOLEAN | TRUE if the service is delivered over copper infrastructure. |
| 11 | `is_fiber_service` | BOOLEAN | TRUE if the service is delivered over fiber infrastructure. |
| 12 | `state` | STRING | US state abbreviation. |
| 13 | `h3_res8` | LONG | H3 resolution-8 hex index for spatial joins. |
| 14 | `in_legacy_copper_territory` | BOOLEAN | TRUE if this BSL is in Lakelink legacy copper territory. |
| 15 | `bsl_type` | STRING | Building type from the fabric location. |
| 16 | `unit_count` | INT | Number of units at the location. |
| 17 | `bdc_filing_date` | DATE | Date of the BDC filing this data comes from. |
| 18 | `bdc_filing_period` | STRING | Filing period (e.g. 2024-H2, 2025-H1). Tracks regulatory reporting cycles. |
| 19 | `coverage_category` | STRING | Derived category: copper_only, fiber_available, both, neither. Key for migration targeting. |
| 20 | `is_synthetic` | BOOLEAN | TRUE if this is synthetic data. |
| 21 | `created_timestamp` | TIMESTAMP | Row creation timestamp. |

## `fcc_fabric_location` (MANAGED)

> Synthetic FCC Broadband Serviceable Location (BSL) Fabric — aligned with tmf_shared.geographic_address. Each row = one BSL with FCC location_id, address, coords, building type, Census Block FIPS.

**20 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `location_id` | LONG | PK. FCC Broadband Serviceable Location (BSL) identifier. Unique per physical address. |
| 2 | `address_primary` | STRING | Primary street address of the BSL. |
| 3 | `address_secondary` | STRING | Secondary address info (apt, suite, unit). |
| 4 | `city` | STRING | City name. |
| 5 | `state` | STRING | US state abbreviation (CO, MN, WA, OR, ID, AZ). |
| 6 | `zip_code` | STRING | Full ZIP code (ZIP+4 format). |
| 7 | `zip5` | STRING | 5-digit ZIP code for aggregation. |
| 8 | `latitude` | DECIMAL | WGS-84 latitude of the location. |
| 9 | `longitude` | DECIMAL | WGS-84 longitude of the location. |
| 10 | `h3_res8` | LONG | H3 resolution-8 hex index for spatial joins with copper device data. |
| 11 | `h3_res9` | LONG | H3 resolution-9 hex index for fine-grained spatial analysis. |
| 12 | `bsl_type` | STRING | Building type classification (e.g. residential, business, community_anchor). |
| 13 | `unit_count` | INT | Number of addressable units (apartments, suites) at this location. |
| 14 | `census_block_fips` | STRING | 15-digit Census Block FIPS code. Links to Census demographic data. |
| 15 | `in_legacy_copper_territory` | BOOLEAN | TRUE if this BSL falls within Lakelink legacy copper service territory. |
| 16 | `is_broadband_serviceable` | BOOLEAN | TRUE if the location can receive broadband service (meets FCC definition). |
| 17 | `fabric_vintage_date` | DATE | Date of the FCC Fabric data release used. |
| 18 | `fabric_release` | STRING | FCC Fabric release version identifier. |
| 19 | `is_synthetic` | BOOLEAN | TRUE if this is synthetic data generated for the copper retirement demo. |
| 20 | `created_timestamp` | TIMESTAMP | Row creation timestamp. |

## `fcc_regulatory_document` (MANAGED)

**24 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `regulatory_document_id` | LONG | PK. Unique identifier for this regulatory document record. |
| 2 | `document_id` | LONG | FK to tmf_shared.document. Links to the base document entity. |
| 3 | `docket_number` | STRING | Regulatory docket/proceeding number (e.g. FCC 26-19, Docket No. 2025-001). |
| 4 | `document_type` | STRING | Type of document (order, notice, comment, filing, rule). |
| 5 | `title` | STRING | Full title of the regulatory document. |
| 6 | `issuing_body` | STRING | Authority that issued the document (FCC, state PUC name). |
| 7 | `jurisdiction_state_code` | STRING | State code for state-level documents. NULL for federal (FCC) documents. |
| 8 | `issued_date` | DATE | Date the document was issued or published. |
| 9 | `effective_date` | DATE | Date the rule or order becomes effective. |
| 10 | `document_status` | STRING | Status of the document (active, superseded, proposed, withdrawn). |
| 11 | `regulatory_topic` | STRING | Topic classification (copper_retirement, section_214, backup_power, e911, notice_requirements). |
| 12 | `summary_text` | STRING | Executive summary of the document content. |
| 13 | `full_text_excerpt` | STRING | Extended text excerpt of the document for Vector Search embedding. |
| 14 | `citation_reference` | STRING | Standard citation format for referencing this document. |
| 15 | `related_docket_numbers` | STRING | Comma-separated list of related docket numbers. |
| 16 | `wire_center_references` | STRING | Wire center IDs referenced in the document, if any. |
| 17 | `carrier_name` | STRING | Carrier named in the document (e.g. Lakelink Fiber). |
| 18 | `notice_period_days` | INT | Notice period requirement specified in the document, if applicable. |
| 19 | `file_format` | STRING | File format of the source document (PDF, DOCX, TXT). |
| 20 | `storage_uri` | STRING | URI to the stored document file (Volume path or cloud storage). |
| 21 | `word_count` | INT | Approximate word count of the document. |
| 22 | `page_count` | INT | Approximate page count of the document. |
| 23 | `is_synthetic` | BOOLEAN | TRUE if this is synthetic data. |
| 24 | `created_timestamp` | TIMESTAMP | Row creation timestamp. |

## `feature_device_billing_dispute` (MANAGED)

> ML feature: billing dispute rate per physical device. Join: billing_dispute → CFS (customer_id) → physical_device (geographic_address_id). Dispute amounts weighted by 1/CFS_per_customer to avoid fanout inflation. Created by @data-engineer 2026-09-13.

**10 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `physical_device_id` | LONG | FK to physical_device. The copper device linked to billing disputes via geographic_address. |
| 2 | `dispute_count` | LONG | Total billing disputes associated with customers at this device address. |
| 3 | `dispute_count_weighted` | DECIMAL | Dispute count weighted by 1/CFS_per_customer to avoid fanout inflation when multiple services share  |
| 4 | `dispute_amount_weighted` | DECIMAL | Dollar amount of disputes weighted by 1/CFS_per_customer. |
| 5 | `escalated_dispute_count` | LONG | Number of disputes that were escalated to management or regulatory bodies. |
| 6 | `sla_breach_dispute_count` | LONG | Number of disputes related to SLA breaches. |
| 7 | `regulatory_dispute_count` | LONG | Number of disputes filed with or involving regulatory agencies. |
| 8 | `earliest_dispute` | DATE | Date of the earliest billing dispute for this device. |
| 9 | `latest_dispute` | DATE | Date of the most recent billing dispute for this device. |
| 10 | `months_since_last_dispute` | DOUBLE | Months elapsed since the most recent dispute. Recency feature for ML. |

## `feature_device_complaint_rate` (MANAGED)

> ML feature: complaint rate per physical device. Join: customer_problem → CFS → physical_device via geographic_address. Created by @data-engineer 2026-09-13.

**11 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `physical_device_id` | LONG | FK to physical_device. The copper device linked to complaints via geographic_address. |
| 2 | `complaint_count` | LONG | Total customer complaints associated with this device location. |
| 3 | `complaint_rate_per_month` | DOUBLE | Average monthly complaint rate over the observation window. |
| 4 | `escalated_complaint_count` | LONG | Number of complaints escalated to management. |
| 5 | `high_severity_count` | LONG | Number of high-severity complaints. |
| 6 | `sla_breach_count` | LONG | Number of complaints involving SLA breaches. |
| 7 | `first_contact_resolution_count` | LONG | Number of complaints resolved on first contact. |
| 8 | `avg_resolution_hours` | DECIMAL | Mean time to resolve complaints in hours. |
| 9 | `earliest_complaint` | DATE | Date of the first complaint for this device. |
| 10 | `latest_complaint` | DATE | Date of the most recent complaint for this device. |
| 11 | `months_since_last_complaint` | DOUBLE | Months since last complaint. Recency feature for ML. |

## `feature_device_contract_flag` (MANAGED)

> ML feature: contract constraint status per copper device. Flags active contracts that block device retirement.

**13 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `physical_device_id` | LONG | FK to physical_device. The copper device being assessed for contract constraints. |
| 2 | `device_type` | STRING | Copper device type for filtering. |
| 3 | `has_active_contract` | BOOLEAN | TRUE if any customer served by this device has an active contract blocking retirement. |
| 4 | `contract_expiry_days_remaining` | INT | Days until the nearest active contract expires. Negative = already expired. |
| 5 | `most_recent_contract_expiry` | STRING | Expiration date of the most recently expiring active contract. |
| 6 | `has_contract_history` | BOOLEAN | TRUE if any contract (active or expired) exists for customers at this device. |
| 7 | `total_contracts` | LONG | Total number of contracts (all statuses) linked to this device. |
| 8 | `active_contract_count` | LONG | Number of currently active contracts blocking retirement. |
| 9 | `expired_contract_count` | LONG | Number of expired contracts. |
| 10 | `linked_customer_count` | LONG | Number of distinct customers served by this device. |
| 11 | `customers_with_active_contract` | LONG | Number of customers with active contracts. |
| 12 | `migration_constraint_status` | STRING | Derived constraint classification: blocked (active contracts), expiring_soon, clear, or no_data. |
| 13 | `_feature_computed_at` | TIMESTAMP | Timestamp when this feature was computed. |

## `feature_device_firmware_age` (MANAGED)

> ML feature: firmware vintage and obsolescence risk per copper device. Sources: installed_software (temporal fields, upgrade/vuln status) + physical_device (installation_date). For devices with multiple SW records, worst-case aggregation is used.

**26 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `physical_device_id` | LONG | FK to physical_device. The copper device being assessed. |
| 2 | `device_type` | STRING | Copper device type. |
| 3 | `firmware_version` | STRING | Current firmware version from physical_device. |
| 4 | `software_version` | STRING | Software version from installed_software table. |
| 5 | `installation_date` | STRING | Device installation date for age calculation. |
| 6 | `device_age_days` | INT | Age of the device in days since installation. |
| 7 | `device_age_years` | DECIMAL | Age of the device in years since installation. |
| 8 | `earliest_eol_date` | DATE | Earliest end-of-life date across all installed software components. |
| 9 | `earliest_support_expiry` | DATE | Earliest vendor support expiry date. |
| 10 | `oldest_last_patch_date` | DATE | Oldest last-patch date across SW components. Longer unpatched = higher risk. |
| 11 | `newest_last_patch_date` | DATE | Most recent patch date across SW components. |
| 12 | `installed_software_count` | LONG | Number of distinct software components on this device. |
| 13 | `days_since_last_patch` | INT | Days since the most recent patch was applied. |
| 14 | `days_past_eol` | INT | Days past end-of-life. Positive = past EOL. Negative = before EOL. |
| 15 | `days_past_support_expiry` | INT | Days past support expiry. Positive = unsupported. |
| 16 | `is_past_eol` | BOOLEAN | TRUE if any software component is past end-of-life. |
| 17 | `is_support_expired` | BOOLEAN | TRUE if vendor support has expired for any component. |
| 18 | `has_vulnerabilities` | INT | Count of software components with known vulnerabilities (0 or 1+ as int flag). |
| 19 | `has_unscanned_sw` | INT | Count of software components not yet scanned for vulnerabilities. |
| 20 | `has_upgrade_ineligible` | INT | Count of components ineligible for upgrade. Hardware limitation indicator. |
| 21 | `has_upgrade_blocked` | INT | Count of components where upgrade is blocked (dependency or compatibility issue). |
| 22 | `primary_upgrade_status` | STRING | Dominant upgrade status across components (e.g. eligible, ineligible, blocked). |
| 23 | `primary_vuln_status` | STRING | Dominant vulnerability status (e.g. clean, vulnerable, unscanned). |
| 24 | `firmware_obsolescence_score` | DOUBLE | Composite obsolescence score (0.0-1.0). Higher = more obsolete. ML feature. |
| 25 | `has_software_data` | BOOLEAN | TRUE if installed_software data exists for this device. FALSE = imputed defaults used. |
| 26 | `_feature_computed_at` | TIMESTAMP | Timestamp when this feature was computed. |

## `feature_device_service_usage` (MANAGED)

> ML feature: service usage patterns per physical device. Direct join via physical_device_id. Includes volume, amount, recency, and trend features. Created by @data-engineer 2026-09-13.

**10 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `physical_device_id` | LONG | FK to physical_device. The copper device linked to service usage data. |
| 2 | `active_months` | LONG | Number of months with usage activity. Measures service tenure. |
| 3 | `avg_monthly_usage` | DECIMAL | Average monthly usage amount in billing units. |
| 4 | `avg_monthly_revenue` | DECIMAL | Average monthly revenue generated by services on this device. |
| 5 | `avg_monthly_volume_bytes` | DOUBLE | Average monthly data volume in bytes. |
| 6 | `total_usage_records` | LONG | Total count of usage records for this device. |
| 7 | `first_usage_month` | TIMESTAMP | Timestamp of the first usage record. |
| 8 | `last_usage_month` | TIMESTAMP | Timestamp of the most recent usage record. |
| 9 | `months_since_last_usage` | DOUBLE | Months since last usage activity. Zero-usage devices may be candidates for faster retirement. |
| 10 | `usage_trend_pct` | DECIMAL | Month-over-month usage trend percentage. Negative = declining usage. |

## `gold_circuit_revenue_at_risk` (MANAGED)

> Gold layer: per-circuit revenue at risk from copper retirement (materialized from DLP SQL)

**47 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `circuit_id` | LONG | MDM crosswalk to tmf_resource.logical_resource.logical_resource_id (the circuit). NULL for synthetic |
| 2 | `source_line_item_id` | STRING | Join key to salesforce_source.contract_line_item.Id. May reference a line_item_id that does not exis |
| 3 | `source_contract_id` | STRING | Crosswalk to salesforce_source.contract.Id for evidence drill-down. NULL for synthetic MISSING_SALES |
| 4 | `monthly_unit_price` | DOUBLE | Actual ERP-billed monthly unit price for the circuit (source of truth for the billed side of the rec |
| 5 | `total_billed_amount` | DOUBLE | Actual ERP-billed monthly total for the circuit. |
| 6 | `estimated_annual_revenue` | DOUBLE | Estimated annual revenue generated by this circuit in USD. Core financial metric for copper retireme |
| 7 | `logical_resource_id` | LONG | FK to tmf_resource.logical_resource. The logical circuit resource. |
| 8 | `circuit_resource_type` | STRING | Type of logical resource (e.g. dsl_line, voip_trunk, leased_line). |
| 9 | `technology_domain` | STRING | Technology domain of the circuit (copper, hybrid, coax). |
| 10 | `bandwidth_mbps` | DECIMAL | Provisioned bandwidth of the circuit in Mbps. |
| 11 | `circuit_operational_state` | STRING | Current operational state of the circuit. |
| 12 | `circuit_lifecycle_status` | STRING | Lifecycle status (active, planned, decommissioning). |
| 13 | `physical_device_id` | LONG | FK to physical_device. The copper device serving this circuit. |
| 14 | `device_type` | STRING | Copper device type. |
| 15 | `device_status` | STRING | Device operational status. |
| 16 | `serial_number` | STRING | Device serial number. |
| 17 | `firmware_version` | STRING | Device firmware version. |
| 18 | `installation_date` | STRING | Device installation date. |
| 19 | `state_code` | STRING | US state abbreviation. |
| 20 | `city` | STRING | City of the device/circuit location. |
| 21 | `latitude` | DECIMAL | WGS-84 latitude. |
| 22 | `longitude` | DECIMAL | WGS-84 longitude. |
| 23 | `h3_res8` | LONG | H3 resolution-8 hex index. |
| 24 | `h3_res9` | LONG | H3 resolution-9 hex index. |
| 25 | `computed_risk_tier` | STRING | Device risk tier (critical/high/medium/low). |
| 26 | `alarm_count` | LONG | Device alarm count. |
| 27 | `critical_alarm_rate` | DECIMAL | Device critical alarm rate. |
| 28 | `sla_breach_rate` | DECIMAL | Device SLA breach rate. |
| 29 | `problem_count` | LONG | Device problem count. |
| 30 | `wire_center_id` | STRING | Serving wire center ID. |
| 31 | `wire_center_name` | STRING | Wire center name. |
| 32 | `clli_code` | STRING | Wire center CLLI code. |
| 33 | `fiber_ready` | BOOLEAN | TRUE if wire center is fiber-ready. |
| 34 | `annual_retire_priority` | INT | Wire center retirement priority rank. |
| 35 | `puc_filing_required` | BOOLEAN | TRUE if PUC filing required. |
| 36 | `puc_name` | STRING | State PUC name. |
| 37 | `governor_notice_days` | LONG | Required governor notice days. |
| 38 | `puc_notice_days` | LONG | Required PUC notice days. |
| 39 | `residential_direct_notice_days` | LONG | Required residential notice days. |
| 40 | `section_214_required` | BOOLEAN | TRUE if Section 214 required. |
| 41 | `revenue_tier` | STRING | Revenue classification: high (>$10K), medium ($5-10K), low (<$5K). Drives financial prioritization. |
| 42 | `action_priority` | STRING | Derived action priority combining risk tier and revenue tier. Determines retirement sequencing. |
| 43 | `_pipeline_aggregated_at` | TIMESTAMP | Pipeline processing timestamp. |
| 44 | `ml_risk_tier` | STRING | ML model predicted risk tier (low/medium/high/critical) from V5 model |
| 45 | `ml_prob_critical` | DOUBLE | ML model probability for critical tier |
| 46 | `ml_prob_high` | DOUBLE | ML model probability for high tier |
| 47 | `ml_composite_risk_score` | DOUBLE | ML model composite risk score |

## `gold_commodity_price_forecast` (MANAGED)

> Forecasted copper/fiber commodity prices, labor costs, and material cost indices by region. Used in Beat 4 commodity dashboard.

**9 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `forecast_month` | STRING | Year-month of the forecast period (YYYY-MM format). |
| 2 | `region` | STRING | Geographic region for this forecast (CO, MN, WA, OR, ID, AZ). |
| 3 | `copper_lme_forecast_usd_ton` | DOUBLE | Forecasted LME copper price in USD per metric ton. |
| 4 | `copper_comex_forecast_usd_lb` | DOUBLE | Forecasted COMEX copper price in USD per pound. |
| 5 | `fiber_cable_forecast_usd_km` | DOUBLE | Forecasted fiber optic cable cost in USD per kilometer. |
| 6 | `labor_cost_index_forecast` | DOUBLE | Forecasted regional labor cost index (base 100). Drives contractor cost estimates. |
| 7 | `material_cost_index_forecast` | DOUBLE | Forecasted material cost index (base 100). Includes conduit, splice closures, etc. |
| 8 | `model_version` | STRING | Version identifier of the forecasting model. |
| 9 | `forecast_generated_date` | STRING | Date the forecast was generated. |

## `gold_contractor_scorecard` (MATERIALIZED_VIEW)

> Gold layer: contractor scorecard with actual incident and work order metrics

**34 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `contractor_performance_id` | LONG | PK from contractor_performance source table. Unique identifier per contractor record. |
| 2 | `bp_agreement_id` | LONG | FK to tmf_businesspartner.bp_agreement. Links to the business partner agreement governing this contr |
| 3 | `party_id` | LONG | FK to tmf_enterprise.work via party_id. Used to join work order metrics for this contractor. |
| 4 | `contractor_name` | STRING | Legal name of the contractor company. Primary display field. |
| 5 | `contractor_type` | STRING | Contractor specialization: general, utility_locator, boring, splicing, etc. |
| 6 | `certification_status` | STRING | Current certification status (e.g. certified, expired_certification, revoked). Revoked = ineligible  |
| 7 | `safety_score` | DECIMAL | Composite safety score (0-100). Score >= 80 required for preferred dispatch status. |
| 8 | `osha_recordable_rate` | DECIMAL | OSHA Total Recordable Incident Rate. Lower is better. Industry benchmark comparison metric. |
| 9 | `overall_rating` | DECIMAL | Overall performance rating (1.0-5.0). Rating >= 4.0 with safety >= 80 qualifies for preferred dispat |
| 10 | `crew_size` | INT | Number of field crew members available from this contractor. Feeds state-level capacity planning. |
| 11 | `equipment_count` | INT | Count of major equipment units (boring rigs, trenchers, etc.) owned by the contractor. |
| 12 | `years_in_business` | INT | Contractors total years of operation. Longevity factor for reliability assessment. |
| 13 | `primary_state` | STRING | US state where the contractor is primarily based. Clustered column for geographic dispatch. |
| 14 | `geographic_coverage_states` | STRING | Comma-separated list of states the contractor can serve. Determines cross-state dispatch eligibility |
| 15 | `bonded_amount` | DECIMAL | Dollar amount of the contractors surety bond. Higher bonding indicates greater financial capacity. |
| 16 | `insurance_expiry_date` | DATE | Date the contractors insurance coverage expires. Past-due triggers suspended dispatch status. |
| 17 | `last_audit_date` | DATE | Date of the most recent safety/compliance audit of this contractor. |
| 18 | `sla_compliance_pct` | DECIMAL | Self-reported SLA compliance percentage from contractor_performance source. Compare with actual_sla_ |
| 19 | `active_project_count` | INT | Number of currently active copper retirement projects assigned to this contractor. |
| 20 | `total_project_value` | DECIMAL | Total dollar value of all projects assigned to this contractor. |
| 21 | `actual_incident_count` | LONG | Count of dig-safe incidents linked to this contractor from bronze_dig_safe_incidents. Actual field d |
| 22 | `actual_at_fault_count` | LONG | Count of incidents where this contractor was determined to be at fault. Feeds risk flags. |
| 23 | `violation_count` | LONG | Count of regulatory violations (at-fault without One-Call ticket). Triggers has_violations flag. |
| 24 | `total_incident_cost` | DECIMAL | Total dollar cost of all incidents attributed to this contractor. Financial exposure metric. |
| 25 | `avg_actual_resolution_hours` | DECIMAL | Mean resolution time across all incidents for this contractor. NULL if no incidents. |
| 26 | `last_incident_date` | DATE | Date of the most recent dig-safe incident involving this contractor. NULL if incident-free. |
| 27 | `total_work_orders` | LONG | Total work orders assigned to this contractor from tmf_enterprise.work. Measures workload volume. |
| 28 | `completed_work_orders` | LONG | Count of work orders with completed status. Completion rate = completed / total. |
| 29 | `actual_sla_compliance_pct` | DECIMAL | Computed SLA compliance: (sla_met_orders / total_work_orders) * 100. Based on actual work order data |
| 30 | `insurance_expired` | BOOLEAN | Risk flag: TRUE if insurance_expiry_date is before today. Triggers dispatch suspension. |
| 31 | `cert_risk` | BOOLEAN | Risk flag: TRUE if certification_status is expired_certification or revoked. |
| 32 | `has_violations` | BOOLEAN | Risk flag: TRUE if this contractor has any regulatory violations from dig-safe incidents. |
| 33 | `dispatch_status` | STRING | Eligibility for dispatch: preferred (rating>=4, safety>=80), eligible (rating>=3), probationary, res |
| 34 | `_pipeline_aggregated_at` | TIMESTAMP | DLP pipeline processing timestamp for this gold-layer aggregation. |

## `gold_device_risk_predictions` (MANAGED)

> Gold layer risk predictions from the V5 ML model. Per-device risk tier, class probabilities, and composite risk score for executive reporting.

**13 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `physical_device_id` | LONG | FK to physical_device. The device being scored. PK. |
| 2 | `device_type` | STRING | Copper device type. |
| 3 | `device_status` | STRING | Device operational status. |
| 4 | `risk_tier_actual` | STRING | Ground truth risk tier from copper_risk_target. |
| 5 | `risk_tier_predicted` | STRING | V5 ML model-predicted risk tier (low/medium/high/critical). Used in gold_retirement_executive_summar |
| 6 | `prob_low` | DOUBLE | Predicted probability for low risk tier. |
| 7 | `prob_medium` | DOUBLE | Predicted probability for medium risk tier. |
| 8 | `prob_high` | DOUBLE | Predicted probability for high risk tier. |
| 9 | `prob_critical` | DOUBLE | Predicted probability for critical risk tier. |
| 10 | `composite_risk_score` | DOUBLE | Weighted composite risk score (0.0-1.0). Higher = higher risk. |
| 11 | `model_version` | STRING | V5 model version identifier. |
| 12 | `feature_set` | STRING | Feature set identifier used for this prediction. |
| 13 | `scored_date` | STRING | Date the prediction was scored. |

## `gold_ebitda_forecast` (MANAGED)

**15 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `state_code` | STRING | US state code (2-letter) where circuits are deployed |
| 2 | `device_type` | STRING | Copper equipment type: CPE, OLT, ONT, or Patch Panel |
| 3 | `risk_tier` | STRING | ML model predicted risk tier (V5): critical, high, medium, low |
| 4 | `fiber_ready` | BOOLEAN | Whether the wire center has fiber infrastructure ready for migration |
| 5 | `scenario` | STRING | Forecast scenario: base (planned timeline), optimistic (1Q earlier), pessimistic (1Q later) |
| 6 | `quarter` | STRING | Projected retirement quarter in YYYY-QN format |
| 7 | `forecast_revenue_at_risk` | DOUBLE | Quarterly revenue at risk from circuits being retired in this quarter (annual / 4 * retire %) |
| 8 | `forecast_annual_revenue_exposure` | DOUBLE | Full annual revenue exposure for circuits retiring in this quarter |
| 9 | `forecast_cost_savings` | DOUBLE | Quarterly operating cost savings from decommissioning copper plant |
| 10 | `forecast_capex` | DECIMAL | One-time capital expenditure for fiber replacement in this quarter |
| 11 | `forecast_net_benefit` | DOUBLE | Net quarterly benefit: cost savings minus amortized capex (5yr / 20Q) |
| 12 | `forecast_ebitda_impact` | DOUBLE | Total quarterly EBITDA impact: savings + 15% avoided maintenance - amortized capex |
| 13 | `circuit_count` | LONG | Number of circuits projected to retire in this state/device/risk/quarter combination |
| 14 | `avg_risk_score` | DOUBLE | Average ML composite risk score for circuits in this group |
| 15 | `forecast_generated_at` | TIMESTAMP | Timestamp when this forecast was generated |

## `gold_retirement_executive_summary` (MATERIALIZED_VIEW)

> Gold layer: per-state executive summary of copper retirement program

**22 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `state_code` | STRING | US state abbreviation. One row per state. Primary grouping dimension for executive reporting. |
| 2 | `total_copper_devices` | LONG | Total copper devices (all types, all statuses) in this state. Inventory size metric. |
| 3 | `active_devices` | LONG | Copper devices currently in active operational status. Subset of total_copper_devices. |
| 4 | `critical_risk_count` | LONG | Devices classified as critical risk by the V5 ML model (gold_device_risk_predictions). Highest prior |
| 5 | `high_risk_count` | LONG | Devices classified as high risk by the V5 ML model. Second-highest priority tier. |
| 6 | `wire_center_count` | LONG | Distinct wire centers with copper devices in this state. Measures geographic spread of the retiremen |
| 7 | `fiber_ready_devices` | LONG | Copper devices at wire centers where fiber infrastructure is already deployed. Migration-ready subse |
| 8 | `fiber_ready_pct` | DECIMAL | Percentage of copper devices at fiber-ready wire centers. Computed: fiber_ready_devices / total_copp |
| 9 | `total_affected_services` | LONG | Distinct customer-facing services (voice, broadband, fixed_line) impacted by copper retirement in th |
| 10 | `total_affected_customers` | LONG | Distinct customers impacted by copper retirement in this state. Key metric for migration campaign si |
| 11 | `voice_services_at_risk` | LONG | Count of voice services on copper infrastructure. Voice retirement requires E911/CLEC coordination. |
| 12 | `broadband_services_at_risk` | LONG | Count of broadband services on copper infrastructure. Broadband migration is typically fiber upgrade |
| 13 | `total_dig_incidents` | LONG | Total dig-safe incidents in this state from bronze_dig_safe_incidents. Indicates active construction |
| 14 | `regulatory_violations` | LONG | Count of regulatory violations (contractor at-fault without One-Call ticket) in this state. |
| 15 | `total_repair_cost` | DECIMAL | Aggregate dollar cost of all dig-safe incident repairs in this state. |
| 16 | `avg_resolution_hours` | DECIMAL | Mean incident resolution time in hours across all dig-safe incidents in this state. |
| 17 | `available_contractors` | LONG | Number of contractors based in this state from gold_contractor_scorecard. Workforce capacity indicat |
| 18 | `avg_contractor_rating` | DECIMAL | Mean overall rating of contractors in this state. Quality indicator for dispatch planning. |
| 19 | `total_crew_capacity` | LONG | Sum of all contractor crew sizes in this state. Total available workforce for copper retirement work |
| 20 | `preferred_contractors` | LONG | Count of contractors with preferred dispatch status (rating>=4, safety>=80) in this state. |
| 21 | `program_health_status` | STRING | Traffic light indicator: red (>50% critical+high risk devices), amber (>30%), green (<30%). Executiv |
| 22 | `_pipeline_aggregated_at` | TIMESTAMP | DLP pipeline processing timestamp for this gold-layer aggregation. |

## `gold_wire_center_scorecard` (MATERIALIZED_VIEW)

> Gold layer: per-wire-center retirement readiness scorecard

**33 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `wire_center_id` | STRING | Unique identifier for the wire center. Primary grouping dimension. One row per wire center. |
| 2 | `wire_center_name` | STRING | Human-readable name of the wire center facility. |
| 3 | `clli_code` | STRING | CLLI (Common Language Location Identifier) code. Standard telecom facility identifier used for inter |
| 4 | `state_code` | STRING | US state abbreviation. Clustered column for geographic filtering. |
| 5 | `fiber_ready` | BOOLEAN | TRUE if the wire center has fiber infrastructure deployed and ready for customer migration. |
| 6 | `puc_filing_required` | BOOLEAN | TRUE if state PUC regulatory filing is required before copper retirement at this wire center. |
| 7 | `annual_retire_priority` | INT | Planned annual retirement priority rank (1=highest priority, retire soonest). Drives the retirement  |
| 8 | `puc_name` | STRING | Full name of the state Public Utilities Commission with regulatory jurisdiction. |
| 9 | `section_214_required` | BOOLEAN | TRUE if FCC Section 214 discontinuance authorization is required for this wire centers jurisdiction. |
| 10 | `governor_notice_days` | LONG | Minimum days of advance notice to the state governor required by regulation. |
| 11 | `puc_notice_days` | LONG | Minimum days of advance notice to the PUC required before copper discontinuance. |
| 12 | `residential_direct_notice_days` | LONG | Minimum days of advance direct notice to affected residential customers required by FCC/state rules. |
| 13 | `copper_device_count` | LONG | Total copper devices (cpe + ont + olt + patch_panel) served by this wire center. |
| 14 | `device_type_count` | LONG | Count of distinct device types present at this wire center (max 4). |
| 15 | `active_device_count` | LONG | Number of copper devices currently in active operational status. |
| 16 | `avg_alarm_count` | DOUBLE | Mean alarm count across all copper devices at this wire center. Higher values indicate degraded plan |
| 17 | `avg_critical_alarm_rate` | DECIMAL | Mean critical alarm rate across devices. Rate > 0.2 contributes to retirement_readiness_score. |
| 18 | `avg_sla_breach_rate` | DECIMAL | Mean SLA breach rate across devices. Indicator of customer-impacting service degradation. |
| 19 | `critical_risk_devices` | LONG | Count of devices classified as critical risk tier. More than 3 earns maximum risk points in readines |
| 20 | `high_risk_devices` | LONG | Count of devices classified as high risk tier. |
| 21 | `avg_distance_km` | DOUBLE | Mean straight-line distance from devices to the wire center in km. Proxy for average copper loop len |
| 22 | `bbox_min_lat` | DECIMAL | Minimum latitude of all device locations at this wire center. Used for map bounding box. |
| 23 | `bbox_max_lat` | DECIMAL | Maximum latitude of all device locations at this wire center. Used for map bounding box. |
| 24 | `bbox_min_lon` | DECIMAL | Minimum longitude of all device locations at this wire center. Used for map bounding box. |
| 25 | `bbox_max_lon` | DECIMAL | Maximum longitude of all device locations at this wire center. Used for map bounding box. |
| 26 | `affected_service_count` | LONG | Count of distinct customer-facing services impacted if this wire center retires copper. From silver_ |
| 27 | `affected_customer_count` | LONG | Count of distinct customers impacted if this wire center retires copper. Key metric for migration pl |
| 28 | `voice_services` | LONG | Count of voice services at risk. Voice requires E911 compliance before retirement. |
| 29 | `broadband_services` | LONG | Count of broadband services at risk of disruption from copper retirement. |
| 30 | `fixed_line_services` | LONG | Count of fixed-line services at risk of disruption from copper retirement. |
| 31 | `retirement_readiness_score` | DECIMAL | Composite 0-100 score: fiber_ready(30) + risk_severity(20) + alarm_rate(20) + priority(15) + custome |
| 32 | `retirement_priority_rank` | INT | Dense rank ordering wire centers by retirement urgency: priority ASC, critical_risk DESC, alarm_rate |
| 33 | `_pipeline_aggregated_at` | TIMESTAMP | DLP pipeline processing timestamp for this gold-layer aggregation. |

## `reg_rag_eval_dataset` (MANAGED)

> Regulatory RAG evaluation dataset for Beat 4 copper retirement. 35 Q&A pairs covering FCC rules, state notice requirements, filing deadlines, backup power, E911, cross-state comparisons, and scenario questions. Created by @ml-engineer for mlflow.genai.evaluate(). v1 2026-09-14.

**11 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `eval_id` | INT | PK. Sequential ID for this evaluation question. |
| 2 | `question` | STRING | Natural language question about copper retirement regulations. |
| 3 | `expected_response` | STRING | Ground truth expected response for evaluation scoring. |
| 4 | `category` | STRING | Question category (fcc_rules, state_requirements, filing_deadlines, backup_power, e911, cross_state, |
| 5 | `states_covered` | STRING | Comma-separated state codes relevant to this question. |
| 6 | `difficulty` | STRING | Question difficulty level (easy, medium, hard). |
| 7 | `source_tables` | STRING | Tables used to construct the expected response. |
| 8 | `created_by` | STRING | Agent role that created this evaluation question. |
| 9 | `created_timestamp` | TIMESTAMP | Creation timestamp. |
| 10 | `project` | STRING | Project tag (copper-retirement). |
| 11 | `eval_version` | STRING | Version of the evaluation dataset (e.g. v1). |

## `regulatory_doc_chunks` (MANAGED)

> Copper retirement project: FCC regulatory document chunks for Vector Search embedding. Created by @ml-engineer.

**19 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `chunk_id` | STRING | PK. Unique identifier for this document chunk. Format: {doc_id}_{chunk_index}. |
| 2 | `regulatory_document_id` | LONG | FK to fcc_regulatory_document. The parent document this chunk belongs to. |
| 3 | `chunk_index` | INT | Zero-based index of this chunk within the parent document. |
| 4 | `total_chunks` | INT | Total number of chunks the parent document was split into. |
| 5 | `docket_number` | STRING | Docket number from the parent document for filtering. |
| 6 | `document_type` | STRING | Document type from the parent (order, notice, comment, filing, rule). |
| 7 | `title` | STRING | Title of the parent document. Denormalized for retrieval display. |
| 8 | `issuing_body` | STRING | Authority that issued the document (FCC, state PUC). |
| 9 | `jurisdiction_state_code` | STRING | State code for state-level documents. NULL for federal. |
| 10 | `issued_date` | STRING | Date the parent document was issued. |
| 11 | `document_status` | STRING | Status of the parent document (active, superseded, proposed). |
| 12 | `regulatory_topic` | STRING | Topic classification from the parent document. |
| 13 | `citation_reference` | STRING | Citation reference from the parent document. |
| 14 | `carrier_name` | STRING | Carrier named in the document. |
| 15 | `notice_period_days` | INT | Notice period from the document, if applicable. |
| 16 | `embedding_text` | STRING | Text content of this chunk prepared for Vector Search embedding. |
| 17 | `chunk_char_length` | INT | Character length of the embedding_text. |
| 18 | `source_text_length` | INT | Character length of the full source document text. |
| 19 | `embedding` | ARRAY | Pre-computed embedding vector (GTE-large, 1024-dim). Array of doubles. |

## `regulatory_doc_chunks_vs_index` (FOREIGN)

> Managed Vector Index with Delta Sync

**18 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `chunk_id` | STRING |  |
| 2 | `regulatory_document_id` | LONG |  |
| 3 | `chunk_index` | INT |  |
| 4 | `total_chunks` | INT |  |
| 5 | `docket_number` | STRING |  |
| 6 | `document_type` | STRING |  |
| 7 | `title` | STRING |  |
| 8 | `issuing_body` | STRING |  |
| 9 | `jurisdiction_state_code` | STRING |  |
| 10 | `issued_date` | STRING |  |
| 11 | `document_status` | STRING |  |
| 12 | `regulatory_topic` | STRING |  |
| 13 | `citation_reference` | STRING |  |
| 14 | `carrier_name` | STRING |  |
| 15 | `notice_period_days` | INT |  |
| 16 | `embedding_text` | STRING |  |
| 17 | `chunk_char_length` | INT |  |
| 18 | `__db_embedding_text_vector` | ARRAY |  |

## `regulatory_doc_vs_index` (FOREIGN)

> Managed Vector Index with Delta Sync

**12 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `chunk_id` | STRING |  |
| 2 | `docket_number` | STRING |  |
| 3 | `document_type` | STRING |  |
| 4 | `title` | STRING |  |
| 5 | `issuing_body` | STRING |  |
| 6 | `jurisdiction_state_code` | STRING |  |
| 7 | `regulatory_topic` | STRING |  |
| 8 | `citation_reference` | STRING |  |
| 9 | `carrier_name` | STRING |  |
| 10 | `notice_period_days` | INT |  |
| 11 | `embedding_text` | STRING |  |
| 12 | `__db_embedding_text_vector` | ARRAY |  |

## `retirement_milestones` (MANAGED)

> Copper retirement project milestones per wire center. Tracks planned vs actual dates, completion status, and regulatory gating flags.

**14 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `milestone_id` | LONG | PK. Unique identifier for this milestone. |
| 2 | `wire_center_id` | STRING | FK to wire_center_boundary. The wire center this milestone applies to. |
| 3 | `name` | STRING | Descriptive name of the milestone (e.g. PUC Filing Submitted, Fiber Install Complete). |
| 4 | `type` | STRING | Milestone type classification (regulatory, construction, notification, migration, decommission). |
| 5 | `status` | STRING | Current status (not_started, in_progress, completed, delayed, blocked). |
| 6 | `priority` | STRING | Priority level (critical, high, medium, low). |
| 7 | `planned_date` | DATE | Original planned completion date. |
| 8 | `actual_date` | DATE | Actual completion date. NULL if not yet completed. |
| 9 | `forecast_date` | DATE | Current forecasted completion date. May differ from planned_date due to delays. |
| 10 | `completion_percentage` | DOUBLE | Progress percentage (0-100). 100 = fully complete. |
| 11 | `critical_path_flag` | BOOLEAN | TRUE if this milestone is on the critical path for wire center retirement. |
| 12 | `regulatory_requirement_flag` | BOOLEAN | TRUE if this is a regulatory gating milestone that cannot be skipped. |
| 13 | `risk_level` | STRING | Risk level for this milestone (high, medium, low). |
| 14 | `risk_description` | STRING | Description of risks that may delay or block this milestone. |

## `risk_model_inference_payload` (MANAGED)

**12 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `databricks_request_id` | STRING | Unique ID for the serving endpoint inference request. Missing comment — only uncommented column in t |
| 2 | `request_date` | DATE | The UTC date on which the model serving request was received. |
| 3 | `client_request_id` | STRING | The user-provided request identifier that can be specified in the model serving request body. |
| 4 | `request_time` | TIMESTAMP | The timestamp at which the request is received. |
| 5 | `status_code` | INT | The HTTP status code that was returned from the model. |
| 6 | `sampling_fraction` | DOUBLE | The sampling fraction used in the event that the request was down-sampled. This value is between 0 a |
| 7 | `execution_duration_ms` | LONG | The time in milliseconds for which the model performed inference. This does not include overhead net |
| 8 | `request` | STRING | The raw request JSON body that was sent to the model serving endpoint. |
| 9 | `response` | STRING | The raw response JSON body that was returned by the model serving endpoint. |
| 10 | `logging_error_codes` | ARRAY | The errors that occurred when the data could not be logged. Error codes include MAX_REQUEST_SIZE_EXC |
| 11 | `served_entity_id` | STRING | The unique ID of the served entity. |
| 12 | `requester` | STRING | The ID of the user or service principal whose permissions are used for the invocation request of the |

## `silver_contract_constraints` (MANAGED)

> Silver layer: contract constraints on copper retirement (materialized from DLP SQL)

**23 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `contract_number` | STRING | CLM contract number (matches Salesforce ContractNumber). |
| 2 | `record_type` | STRING | MSA / Order Form / Amendment. |
| 3 | `contract_status` | STRING | Status of the contract (active, expired, terminated). Active contracts may block retirement. |
| 4 | `effective_date` | DATE | Date the contract became effective. |
| 5 | `expiration_date` | DATE | Date the contract expires. |
| 6 | `attachment_path` | STRING | UC Volume path to the rendered PDF. |
| 7 | `salesforce_account_id` | STRING | Salesforce 18-char record Id (keyPrefix 001). |
| 8 | `account_name` | STRING | Account name; sourced from the golden customer name. |
| 9 | `customer_id` | LONG | Golden customer_id in cdm_tmforum.tmf_customer.customer. |
| 10 | `customer_facing_service_id` | LONG | FK to CFS. The service bound by this contract. |
| 11 | `service_type` | STRING | Type of copper-carried service (voice, fixed_line, broadband). |
| 12 | `service_status` | STRING | Operational status of the service. |
| 13 | `geographic_address_id` | LONG | FK to geographic_address. Service/device location. |
| 14 | `service_h3_res8` | LONG | H3 resolution-8 hex of the service location. |
| 15 | `physical_device_id` | LONG | FK to physical_device. Copper device serving this contract. |
| 16 | `device_type` | STRING | Copper device type. |
| 17 | `device_status` | STRING | Device operational status. |
| 18 | `days_until_expiry` | INT | Days until contract expires. Negative = already expired. |
| 19 | `days_since_effective` | INT | Days since contract became effective. Measures contract age. |
| 20 | `constraint_status` | STRING | Derived status: blocked (active, >90 days), expiring_soon (active, <90 days), clear (expired/termina |
| 21 | `eligible_for_retirement` | BOOLEAN | TRUE if the device can be retired without violating this contract. |
| 22 | `earliest_retirement_date` | DATE | Earliest date this device can be retired given contract obligations. |
| 23 | `_pipeline_processed_at` | TIMESTAMP | Pipeline processing timestamp. |

## `silver_copper_plant_enriched` (MATERIALIZED_VIEW)

> Silver layer: copper devices enriched with alarm, performance, and risk features

**37 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `physical_device_id` | LONG | Unique identifier for the copper device. PK. Carried from bronze_copper_devices. |
| 2 | `device_type` | STRING | Copper device type: cpe, ont, olt, or patch_panel. Clustered column. |
| 3 | `device_status` | STRING | Operational status of the device. Carried from bronze layer. |
| 4 | `serial_number` | STRING | Manufacturer serial number of the device. |
| 5 | `firmware_version` | STRING | Current firmware version. Older versions indicate higher obsolescence risk. |
| 6 | `manufacture_date` | STRING | Device manufacturing date for age-based risk features. |
| 7 | `installation_date` | STRING | Field installation date for device age calculation. |
| 8 | `geographic_address_id` | LONG | FK to tmf_shared.geographic_address for location context. |
| 9 | `state_code` | STRING | US state abbreviation. Clustered column for partition-style access patterns. |
| 10 | `city` | STRING | City name of the device location. |
| 11 | `addr_latitude` | DECIMAL | WGS-84 latitude of the device address. |
| 12 | `addr_longitude` | DECIMAL | WGS-84 longitude of the device address. |
| 13 | `addr_h3_res8` | LONG | H3 resolution-8 hex index from the address. |
| 14 | `addr_h3_res9` | LONG | H3 resolution-9 hex index from the address. |
| 15 | `alarm_count` | LONG | Total number of alarms recorded for this device from copper_risk_target. Higher counts signal degrad |
| 16 | `critical_alarm_rate` | DECIMAL | Fraction of alarms classified as critical (0.0-1.0). Rate > 0.3 triggers critical risk tier classifi |
| 17 | `service_affecting_rate` | DECIMAL | Fraction of alarms that affected customer service (0.0-1.0). Key input to risk tier computation. |
| 18 | `sla_breach_count` | LONG | Number of SLA breaches associated with this device. From copper_risk_target. |
| 19 | `sla_breach_rate` | DECIMAL | Fraction of service events that breached SLA (0.0-1.0). Rate > 0.2 triggers critical risk tier. |
| 20 | `test_fail_rate` | DECIMAL | Fraction of loopback/BERT tests that failed for this device (0.0-1.0). Indicator of copper line degr |
| 21 | `problem_count` | LONG | Total number of service problems associated with this device. |
| 22 | `recurring_problem_rate` | DECIMAL | Fraction of problems that recurred after resolution (0.0-1.0). High rates suggest underlying plant i |
| 23 | `wire_center_id` | STRING | Identifier of the wire center serving this device. From copper_plant_wire_center_jurisdiction spatia |
| 24 | `wire_center_name` | STRING | Human-readable name of the serving wire center. |
| 25 | `clli_code` | STRING | CLLI (Common Language Location Identifier) code of the wire center. Standard telecom facility identi |
| 26 | `fiber_ready` | BOOLEAN | TRUE if the wire center has fiber infrastructure ready for migration. Key retirement gating criterio |
| 27 | `annual_retire_priority` | INT | Planned retirement year priority rank (1=soonest). From wire center jurisdiction data. |
| 28 | `puc_filing_required` | BOOLEAN | TRUE if state PUC (Public Utilities Commission) filing is required before copper retirement in this  |
| 29 | `distance_to_wire_center_km` | DOUBLE | Straight-line distance from device to its serving wire center in kilometers. Proxy for loop length a |
| 30 | `puc_name` | STRING | Full name of the state Public Utilities Commission with jurisdiction. |
| 31 | `puc_short_name` | STRING | Abbreviated PUC name for compact display in dashboards. |
| 32 | `governor_notice_days` | LONG | Required days of advance notice to the state governor before copper retirement. Varies by state regu |
| 33 | `puc_notice_days` | LONG | Required days of advance notice to the PUC before copper retirement. |
| 34 | `residential_direct_notice_days` | LONG | Required days of advance direct notice to residential customers before copper retirement. Per FCC an |
| 35 | `section_214_required` | BOOLEAN | TRUE if FCC Section 214 discontinuance authorization is required for this jurisdiction. |
| 36 | `computed_risk_tier` | STRING | Derived risk classification: critical (alarm>0.3 OR sla_breach>0.2), high (alarm>0.15 OR sla_breach> |
| 37 | `_pipeline_processed_at` | TIMESTAMP | DLP pipeline processing timestamp for this silver-layer materialization. |

## `silver_device_service_impact` (MATERIALIZED_VIEW)

> Silver layer: copper device to customer service impact mapping

**20 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `physical_device_id` | LONG | FK to silver_copper_plant_enriched. The copper device whose retirement impacts services. |
| 2 | `device_type` | STRING | Copper device type: cpe, ont, olt, or patch_panel. |
| 3 | `device_status` | STRING | Operational status of the device from silver_copper_plant_enriched. |
| 4 | `state_code` | STRING | US state abbreviation. Clustered column. |
| 5 | `wire_center_id` | STRING | Serving wire center identifier for the device. |
| 6 | `wire_center_name` | STRING | Human-readable wire center name. |
| 7 | `computed_risk_tier` | STRING | Risk tier of the device (critical/high/medium/low) from silver_copper_plant_enriched. |
| 8 | `addr_h3_res8` | LONG | H3 resolution-8 hex index of the device location for spatial aggregation. |
| 9 | `device_service_allocation_id` | LONG | PK from tmf_resource.device_service_allocation. Links the physical device to the service it supports |
| 10 | `allocation_status` | STRING | Status of the device-to-service allocation (e.g. active, reserved). From device_service_allocation. |
| 11 | `criticality_level` | STRING | Criticality classification of this allocation (e.g. mission_critical, standard). From device_service |
| 12 | `service_role` | STRING | Role of the device in delivering the service (e.g. primary, backup). From device_service_allocation. |
| 13 | `customer_facing_service_id` | LONG | FK to bronze_copper_services. The customer-facing service impacted by this device. |
| 14 | `service_type` | STRING | Type of copper-carried service: voice, fixed_line, or broadband. |
| 15 | `service_status` | STRING | Operational status of the customer-facing service. |
| 16 | `customer_id` | LONG | FK to tmf_customer.customer. The customer impacted by potential device retirement. |
| 17 | `customer_name` | STRING | Customer display name for impact reporting. |
| 18 | `customer_segment` | STRING | Customer segment (residential, enterprise, government) for migration prioritization. |
| 19 | `impact_category` | STRING | Derived impact type based on service_type: voice_disruption, data_disruption, line_disruption, or un |
| 20 | `_pipeline_processed_at` | TIMESTAMP | DLP pipeline processing timestamp for this silver-layer materialization. |

## `silver_resource_capacity` (MANAGED)

> Silver layer: network resource capacity at CO/exchange sites enriched with location data. Tracks fiber infrastructure readiness and migration capacity.

**44 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `resource_capacity_id` | LONG | PK. Unique identifier from tmf_enterprise.resource_capacity. |
| 2 | `physical_resource_id` | LONG | FK to tmf_enterprise.physical_resource. The network element being measured. |
| 3 | `infrastructure_layer` | STRING | OSI-style layer (physical, data_link, network, transport, application). |
| 4 | `technology_domain` | STRING | Technology domain (copper, fiber, hybrid, wireless, ip_core). |
| 5 | `resource_type` | STRING | Specific resource type (e.g. GPON_port, OLT_slot, CO_rack_space, power_circuit). |
| 6 | `category` | STRING | Capacity category (port, slot, power, space, bandwidth). |
| 7 | `status` | STRING | Resource status (active, planned, decommissioned). |
| 8 | `unit` | STRING | Unit of measurement (ports, watts, rack_units, Gbps). |
| 9 | `network_domain` | STRING | Network domain classification (access, distribution, core, metro). |
| 10 | `utilization_pct` | DECIMAL | Current utilization as percentage of total capacity (0-100). |
| 11 | `total_capacity` | DECIMAL | Total installed capacity in the specified units. |
| 12 | `used_capacity` | DECIMAL | Currently used/allocated capacity. |
| 13 | `available_capacity` | DECIMAL | Available (unallocated) capacity. Total - used - reserved. |
| 14 | `reserved_capacity` | DECIMAL | Capacity reserved for planned projects or protection. |
| 15 | `expansion_capacity` | DECIMAL | Additional capacity available through equipment expansion. |
| 16 | `demand_forecast` | DECIMAL | Forecasted demand in the same units. |
| 17 | `contention_ratio` | DECIMAL | Overbooking ratio of subscribed vs available capacity. Higher = more contention. |
| 18 | `threshold_warning_pct` | DECIMAL | Warning threshold percentage. Utilization above this triggers alerts. |
| 19 | `threshold_critical_pct` | DECIMAL | Critical threshold percentage. Utilization above this is at-risk. |
| 20 | `is_shared_resource` | BOOLEAN | TRUE if this resource is shared among multiple services/customers. |
| 21 | `is_reserved_for_protection` | BOOLEAN | TRUE if capacity is reserved for network protection/redundancy. |
| 22 | `regulatory_reporting_required` | BOOLEAN | TRUE if capacity levels must be reported to regulators. |
| 23 | `valid_from` | STRING | Start date of this capacity measurement period. |
| 24 | `valid_to` | STRING | End date of this capacity measurement period. |
| 25 | `planning_horizon_date` | STRING | Target date for capacity planning forecasts. |
| 26 | `geographic_site_id` | LONG | FK to geographic_site. The physical site housing this resource. |
| 27 | `site_name` | STRING | Name of the site (e.g. CO name, exchange name). |
| 28 | `site_type` | STRING | Site type classification (central_office, remote_terminal, hub). |
| 29 | `site_category` | STRING | Site category (network_building, cabinet, manhole). |
| 30 | `site_city` | STRING | City where the site is located. |
| 31 | `geographic_address_id` | LONG | FK to geographic_address. |
| 32 | `state_or_province` | STRING | US state abbreviation. |
| 33 | `locality` | STRING | City/locality name from geographic_address. |
| 34 | `country_code` | STRING | Country code (US). |
| 35 | `h3_res8` | LONG | H3 resolution-8 hex for spatial analysis. |
| 36 | `h3_res9` | LONG | H3 resolution-9 hex for fine-grained spatial analysis. |
| 37 | `latitude` | DECIMAL | WGS-84 latitude of the site. |
| 38 | `longitude` | DECIMAL | WGS-84 longitude of the site. |
| 39 | `headroom_pct` | DECIMAL | Available headroom percentage: (total - used) / total * 100. |
| 40 | `capacity_health` | STRING | Derived health status: critical (>threshold_critical), warning (>threshold_warning), healthy. |
| 41 | `is_fiber_infrastructure` | BOOLEAN | TRUE if this resource is fiber infrastructure. Key for migration readiness assessment. |
| 42 | `is_legacy_state` | BOOLEAN | TRUE if this site is in a legacy copper state (CO, MN, WA, OR, ID, AZ). |
| 43 | `migration_readiness` | STRING | Derived readiness status: ready (fiber + healthy capacity), constrained, not_ready. |
| 44 | `_computed_at` | TIMESTAMP | Processing timestamp. |

## `silver_revenue_recognition_constraints` (MANAGED)

> Silver layer: ASC 606 revenue recognition constraints on copper retirement — flags circuits with deferred revenue that block safe decommissioning

**27 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `customer_trx_id` | LONG | FK to ra_customer_trx_all. |
| 2 | `transaction_number` | STRING | Human-readable invoice number. |
| 3 | `transaction_date` | DATE | Invoice date. |
| 4 | `invoice_amount` | DECIMAL | Invoice total (matches tmf bill.total_amount). |
| 5 | `currency_code` | STRING | Invoice currency copied unchanged from customer billing_currency (NULL defaults to USD); currencies  |
| 6 | `bill_id` | LONG | Crosswalk to tmf_customer.bill.bill_id. |
| 7 | `customer_id` | LONG | FK to customer. The customer with deferred revenue. |
| 8 | `billing_account_id` | LONG | FK to financial_account. The billing account with deferred amounts. |
| 9 | `customer_facing_service_id` | LONG | FK to CFS. The service with deferred revenue obligations. |
| 10 | `service_type` | STRING | Type of service (voice, fixed_line, broadband). |
| 11 | `service_status` | STRING | Operational status of the service. |
| 12 | `geographic_address_id` | LONG | FK to geographic_address. |
| 13 | `service_h3_res8` | LONG | H3 resolution-8 hex of the service location. |
| 14 | `physical_device_id` | LONG | FK to physical_device. Copper device serving this service. |
| 15 | `device_type` | STRING | Copper device type. |
| 16 | `device_status` | STRING | Device operational status. |
| 17 | `deferred_period_count` | LONG | Number of billing periods with deferred revenue for this service. |
| 18 | `total_deferred_amount` | DECIMAL | Total dollar amount of deferred revenue remaining (ASC 606 obligation). |
| 19 | `total_recognized_amount` | DECIMAL | Total dollar amount already recognized. |
| 20 | `first_deferred_date` | DATE | Date of the earliest deferred revenue period. |
| 21 | `last_deferred_date` | DATE | Date of the latest deferred revenue period. |
| 22 | `recognition_pct_complete` | DECIMAL | Percentage of total revenue obligation already recognized (0-100). |
| 23 | `days_until_fully_recognized` | INT | Estimated days until all deferred revenue is fully recognized. |
| 24 | `constraint_severity` | STRING | Severity of the ASC 606 constraint: high (>$10K deferred), medium ($1-10K), low (<$1K). |
| 25 | `revrec_eligible_for_retirement` | BOOLEAN | TRUE if deferred revenue is sufficiently recognized to allow retirement. |
| 26 | `earliest_safe_retirement_date` | DATE | Earliest date this device can be retired without ASC 606 write-off risk. |
| 27 | `_pipeline_processed_at` | TIMESTAMP | Pipeline processing timestamp. |

## `state_puc_jurisdiction_requirements` (MANAGED)

> Reference table of state PUC regulatory requirements for copper retirement — notice periods, filing types, backup power rules, and compliance contacts per state.

**28 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `jurisdiction_id` | LONG | PK. Unique identifier for this regulatory jurisdiction record. |
| 2 | `state_code` | STRING | US state abbreviation. |
| 3 | `state_name` | STRING | Full state name. |
| 4 | `puc_name` | STRING | Full name of the state Public Utilities Commission. |
| 5 | `puc_short_name` | STRING | Abbreviated PUC name for dashboards. |
| 6 | `puc_website_url` | STRING | URL of the PUC website. |
| 7 | `governor_notice_days` | LONG | Required days of advance notice to the governor. |
| 8 | `puc_notice_days` | LONG | Required days of advance notice to the PUC. |
| 9 | `residential_direct_notice_days` | LONG | Required days of advance direct notice to residential customers. |
| 10 | `tribal_notice_days` | LONG | Required days of advance notice to tribal authorities. |
| 11 | `section_214_required` | BOOLEAN | TRUE if FCC Section 214 discontinuance authorization is required. |
| 12 | `section_214_streamlined` | BOOLEAN | TRUE if streamlined (rather than full) Section 214 process is available. |
| 13 | `section_251c5_filing_required` | BOOLEAN | TRUE if Section 251(c)(5) interconnection filing is required. |
| 14 | `public_notice_required` | BOOLEAN | TRUE if a public notice must be published. |
| 15 | `backup_power_disclosure_required` | BOOLEAN | TRUE if backup power compliance disclosure is required. |
| 16 | `backup_power_minimum_hours` | LONG | Minimum hours of backup power required by regulation. |
| 17 | `filing_type` | STRING | Type of regulatory filing required (full, streamlined, notification). |
| 18 | `e911_coordination_required` | BOOLEAN | TRUE if E911 service coordination required before retirement. |
| 19 | `interconnecting_carrier_notice_required` | BOOLEAN | TRUE if interconnecting carriers must be notified. |
| 20 | `legacy_device_compatibility_check` | BOOLEAN | TRUE if a compatibility check for legacy customer equipment is required. |
| 21 | `local_row_permit_required` | BOOLEAN | TRUE if a local right-of-way permit is needed. |
| 22 | `historic_district_review` | BOOLEAN | TRUE if historic district review is needed for construction work. |
| 23 | `state_has_additional_requirements` | BOOLEAN | TRUE if the state has requirements beyond the standard checklist. |
| 24 | `additional_requirements_summary` | STRING | Free-text summary of any additional state-specific requirements. |
| 25 | `regulatory_contact_email` | STRING | Contact email for the PUC regulatory office. |
| 26 | `last_updated_date` | DATE | Date this jurisdiction record was last reviewed/updated. |
| 27 | `effective_date` | DATE | Date these requirements became effective. |
| 28 | `notes` | STRING | Free-text notes about this jurisdiction. |

## `v5_fairness_dimension_summary` (MANAGED)

> V5 fairness dimension-level summary: statistical parity and equalized odds per slicing dimension. Generated 2026-09-13 by @ml-engineer. project=copper-retirement, developer=copper-ml

**13 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `dimension` | STRING | Slicing dimension (device_type, geography, service_type, customer_segment). |
| 2 | `n_slices` | LONG | Number of sub-demographic slices in this dimension. |
| 3 | `stat_parity_diff` | DOUBLE | Max difference in statistical parity rates across slices. Lower = more fair. |
| 4 | `equalized_odds_tpr_diff` | DOUBLE | Max difference in true positive rates across slices (equalized odds). |
| 5 | `equalized_odds_fpr_diff` | DOUBLE | Max difference in false positive rates across slices. |
| 6 | `min_auc` | DOUBLE | Minimum AUC-ROC across all slices in this dimension. |
| 7 | `max_auc` | DOUBLE | Maximum AUC-ROC across all slices. |
| 8 | `min_recall` | DOUBLE | Minimum recall across all slices. Low min_recall = model misses risk in some groups. |
| 9 | `max_recall` | DOUBLE | Maximum recall across all slices. |
| 10 | `min_precision` | DOUBLE | Minimum precision across all slices. |
| 11 | `max_precision` | DOUBLE | Maximum precision across all slices. |
| 12 | `report_date` | STRING | Date the dimension summary was generated. |
| 13 | `model_version` | LONG | V5 model version. |

## `v5_fairness_report` (MANAGED)

> V5 model fairness/bias report: per-sub-demographic precision/recall/FPR/AUC with statistical parity and equalized odds. Generated 2026-09-13 by @ml-engineer. project=copper-retirement, developer=copper-ml

**16 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `n` | LONG | Number of samples in this sub-demographic slice. |
| 2 | `precision` | DOUBLE | Precision metric for the V5 model on this slice. |
| 3 | `recall` | DOUBLE | Recall metric for the V5 model on this slice. |
| 4 | `fpr` | DOUBLE | False positive rate for this slice. |
| 5 | `f1` | DOUBLE | F1 score (harmonic mean of precision and recall) for this slice. |
| 6 | `auc_roc` | DOUBLE | Area under the ROC curve for this slice. |
| 7 | `accuracy` | DOUBLE | Overall accuracy for this slice. |
| 8 | `stat_parity_rate` | DOUBLE | Statistical parity rate — fraction of positive predictions in this slice. |
| 9 | `positive_rate` | DOUBLE | Rate of positive (high/critical risk) predictions in this slice. |
| 10 | `dimension` | STRING | Slicing dimension (device_type, state, service_type, customer_segment). |
| 11 | `slice_value` | STRING | Value within the dimension (e.g. cpe, CO, voice, enterprise). |
| 12 | `flag` | STRING | Fairness flag: pass, warning, or fail based on threshold analysis. |
| 13 | `report_date` | STRING | Date the fairness report was generated. |
| 14 | `model_version` | LONG | V5 model version this report evaluates. |
| 15 | `model_name` | STRING | Name of the model in UC Model Registry. |
| 16 | `mlflow_run_id` | STRING | MLflow run ID for lineage tracking. |

## `wire_center_boundary` (MANAGED)

> Wire center geographic boundaries with GeoJSON polygons, copper plant statistics, and fiber readiness indicators. Used for map visualization.

**21 columns:**

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `wire_center_id` | STRING | PK. Unique identifier for the wire center. |
| 2 | `geographic_site_id` | LONG | FK to geographic_site. The physical site of the wire center building. |
| 3 | `wire_center_name` | STRING | Human-readable name of the wire center. |
| 4 | `state_code` | STRING | US state abbreviation. |
| 5 | `centroid_lat` | DOUBLE | Latitude of the wire center service area geographic centroid. |
| 6 | `centroid_lon` | DOUBLE | Longitude of the wire center service area geographic centroid. |
| 7 | `h3_cell_res7` | STRING | H3 resolution-7 hex of the centroid. Coarser grain for regional views. |
| 8 | `h3_cell_res9` | STRING | H3 resolution-9 hex of the centroid. |
| 9 | `boundary_geojson` | STRING | GeoJSON polygon representing the wire center service area boundary. Used for map rendering. |
| 10 | `wire_center_type` | STRING | Facility type (central_office, remote_terminal). |
| 11 | `address_count` | INT | Number of serviceable addresses within this wire center boundary. |
| 12 | `copper_device_count` | INT | Number of copper devices served by this wire center. |
| 13 | `estimated_copper_pairs` | INT | Estimated total copper cable pairs in this wire center area. |
| 14 | `fiber_ready` | BOOLEAN | TRUE if fiber infrastructure is deployed and ready for migration. |
| 15 | `backup_power` | BOOLEAN | TRUE if backup power generation is available at this site. |
| 16 | `area_sq_km` | DOUBLE | Service area of the wire center in square kilometers. |
| 17 | `annual_retire_priority` | INT | Planned retirement year priority rank (1=retire first). |
| 18 | `puc_filing_required` | BOOLEAN | TRUE if PUC filing required before retirement. |
| 19 | `clli_code` | STRING | CLLI code of the wire center. |
| 20 | `source` | STRING | Data provenance tag. |
| 21 | `created_timestamp` | TIMESTAMP | Row creation timestamp. |

