-- Metric view: copper_retirement_project_status
-- Exported 2026-11-01 by @data-analyst (ACC-DA-MV-DDL-EXPORT) from SHOW CREATE TABLE cdm_tmforum.copper_retirement.copper_retirement_project_status.
-- Template parameters (text substitution before execution): ${catalog} (reference: cdm_tmforum), ${schema} (reference: copper_retirement).
-- Space-containing column names are backtick-quoted. Provisioning/execution is owned by ACC-DE-MV-DDL-PROVISION.
-- Synthetic-data note: see the view COMMENT below.

CREATE OR REPLACE VIEW ${catalog}.${schema}.copper_retirement_project_status (
  `State` COMMENT 'US state code where the copper device is deployed',
  `Device Type` COMMENT 'Type of copper network equipment: CPE (Customer Premises Equipment), OLT (Optical Line Terminal), ONT (Optical Network Terminal), Patch Panel',
  `Risk Tier` COMMENT 'Computed risk tier for copper retirement prioritization based on alarm rates, SLA breaches, and service impact',
  `Device Status` COMMENT 'Current operational status of the device: Installed (in-field, working), Active (in service), Faulty (needs replacement), In Stock (spare inventory)',
  `Fiber Ready` COMMENT 'Whether the wire center serving this device has fiber infrastructure ready for migration',
  `Wire Center` COMMENT 'Wire center (central office) serving this copper device',
  `City` COMMENT 'City where the copper device is located',
  `Total Copper Devices` COMMENT 'Total count of copper network devices in the retirement program',
  `Active Devices` COMMENT 'Devices currently installed or active in the network — these require migration before retirement',
  `Faulty Devices` COMMENT 'Devices flagged as faulty — highest urgency for retirement or replacement',
  `Critical Risk Devices` COMMENT 'Devices in the critical risk tier requiring immediate retirement action',
  `Fiber Ready Devices` COMMENT 'Copper devices in wire centers where fiber infrastructure is already deployed — ready for migration',
  `Fiber Ready Pct` COMMENT 'Percentage of copper devices located in fiber-ready wire centers',
  `Critical Risk Pct` COMMENT 'Percentage of devices in the critical risk tier',
  `Avg Alarm Count` COMMENT 'Average number of alarms per copper device — higher values indicate degrading plant health',
  `Total Problem Count` COMMENT 'Total reported problems across all copper devices',
  `Avg SLA Breach Rate` COMMENT 'Average SLA breach rate across copper devices — key quality indicator for retirement urgency',
  `Unique Wire Centers` COMMENT 'Number of distinct wire centers with copper devices — indicates geographic spread of retirement program')
COMMENT 'DERIVED FROM SYNTHETIC DATA — Copper retirement project status KPIs — tracks device inventory, retirement progress, risk distribution, and fiber readiness across the Lakelink Fiber network. Source of truth for executive status reporting on the copper decommissioning program.'
WITH METRICS
LANGUAGE YAML
AS
$$
version: 1.1

source: ${catalog}.${schema}.silver_copper_plant_enriched

comment: "DERIVED FROM SYNTHETIC DATA — Copper retirement project status KPIs — tracks\
  \ device inventory, retirement progress, risk distribution, and fiber readiness\
  \ across the Lakelink Fiber network. Source of truth for executive status reporting\
  \ on the copper decommissioning program."

dimensions:
  - name: State
    expr: state_code
    comment: US state code where the copper device is deployed
    display_name: State
    synonyms:
      - state code
      - geography
      - location

  - name: Device Type
    expr: |-
      CASE device_type
        WHEN 'cpe' THEN 'CPE'
        WHEN 'olt' THEN 'OLT'
        WHEN 'ont' THEN 'ONT'
        WHEN 'patch_panel' THEN 'Patch Panel'
        ELSE device_type
      END
    comment: "Type of copper network equipment: CPE (Customer Premises Equipment),\
      \ OLT (Optical Line Terminal), ONT (Optical Network Terminal), Patch Panel"
    display_name: Device Type
    synonyms:
      - equipment type
      - device category

  - name: Risk Tier
    expr: |-
      CASE computed_risk_tier
        WHEN 'critical' THEN 'Critical'
        WHEN 'high' THEN 'High'
        WHEN 'medium' THEN 'Medium'
        WHEN 'low' THEN 'Low'
        ELSE COALESCE(computed_risk_tier, 'Unknown')
      END
    comment: "Computed risk tier for copper retirement prioritization based on alarm\
      \ rates, SLA breaches, and service impact"
    display_name: Risk Tier
    synonyms:
      - risk level
      - risk category
      - priority tier

  - name: Device Status
    expr: |-
      CASE device_status
        WHEN 'installed' THEN 'Installed'
        WHEN 'active' THEN 'Active'
        WHEN 'faulty' THEN 'Faulty'
        WHEN 'in_stock' THEN 'In Stock'
        ELSE COALESCE(device_status, 'Unknown')
      END
    comment: "Current operational status of the device: Installed (in-field, working),\
      \ Active (in service), Faulty (needs replacement), In Stock (spare inventory)"
    display_name: Device Status
    synonyms:
      - operational status
      - equipment status

  - name: Fiber Ready
    expr: |-
      CASE
        WHEN fiber_ready = true THEN 'Fiber Ready'
        WHEN fiber_ready = false THEN 'Not Fiber Ready'
        ELSE 'Unknown'
      END
    comment: Whether the wire center serving this device has fiber infrastructure
      ready for migration
    display_name: Fiber Readiness
    synonyms:
      - fiber readiness
      - migration ready

  - name: Wire Center
    expr: "COALESCE(wire_center_name, 'Unassigned')"
    comment: Wire center (central office) serving this copper device
    display_name: Wire Center
    synonyms:
      - central office
      - CO
      - wire center name

  - name: City
    expr: "COALESCE(city, 'Unknown')"
    comment: City where the copper device is located
    display_name: City

measures:
  - name: Total Copper Devices
    expr: COUNT(1)
    comment: Total count of copper network devices in the retirement program
    display_name: Total Copper Devices
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - device count
      - total devices
      - copper plant size

  - name: Active Devices
    expr: "COUNT(1) FILTER (WHERE device_status IN ('installed', 'active'))"
    comment: Devices currently installed or active in the network — these require
      migration before retirement
    display_name: Active Devices
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - in-service devices
      - operational devices

  - name: Faulty Devices
    expr: COUNT(1) FILTER (WHERE device_status = 'faulty')
    comment: Devices flagged as faulty — highest urgency for retirement or replacement
    display_name: Faulty Devices
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - broken devices
      - failed equipment

  - name: Critical Risk Devices
    expr: COUNT(1) FILTER (WHERE computed_risk_tier = 'critical')
    comment: Devices in the critical risk tier requiring immediate retirement action
    display_name: Critical Risk Devices
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - critical devices
      - high priority devices

  - name: Fiber Ready Devices
    expr: COUNT(1) FILTER (WHERE fiber_ready = true)
    comment: Copper devices in wire centers where fiber infrastructure is already
      deployed — ready for migration
    display_name: Fiber Ready Devices
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - migration ready devices
      - fiber eligible

  - name: Fiber Ready Pct
    expr: COUNT(1) FILTER (WHERE fiber_ready = true) * 100.0 / COUNT(1)
    comment: Percentage of copper devices located in fiber-ready wire centers
    display_name: Fiber Ready %
    format:
      type: percentage
      decimal_places:
        type: max
        places: 1
    synonyms:
      - fiber readiness rate
      - migration readiness

  - name: Critical Risk Pct
    expr: COUNT(1) FILTER (WHERE computed_risk_tier = 'critical') * 100.0 / COUNT(1)
    comment: Percentage of devices in the critical risk tier
    display_name: Critical Risk %
    format:
      type: percentage
      decimal_places:
        type: max
        places: 1
    synonyms:
      - critical rate

  - name: Avg Alarm Count
    expr: AVG(alarm_count)
    comment: Average number of alarms per copper device — higher values indicate degrading
      plant health
    display_name: Avg Alarm Count
    format:
      type: number
      decimal_places:
        type: max
        places: 1
    synonyms:
      - average alarms
      - mean alarm rate

  - name: Total Problem Count
    expr: SUM(problem_count)
    comment: Total reported problems across all copper devices
    display_name: Total Problems
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - total issues
      - problem volume

  - name: Avg SLA Breach Rate
    expr: AVG(sla_breach_rate)
    comment: Average SLA breach rate across copper devices — key quality indicator
      for retirement urgency
    display_name: Avg SLA Breach Rate
    format:
      type: percentage
      decimal_places:
        type: max
        places: 2
    synonyms:
      - SLA violation rate
      - breach rate

  - name: Unique Wire Centers
    expr: COUNT(DISTINCT wire_center_id)
    comment: Number of distinct wire centers with copper devices — indicates geographic
      spread of retirement program
    display_name: Wire Centers
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - central offices
      - CO count
$$;
