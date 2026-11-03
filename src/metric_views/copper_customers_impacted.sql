-- Metric view: copper_customers_impacted
-- Exported 2026-11-01 by @data-analyst (ACC-DA-MV-DDL-EXPORT) from SHOW CREATE TABLE cdm_tmforum.copper_retirement.copper_customers_impacted.
-- Template parameters (text substitution before execution): ${catalog} (reference: cdm_tmforum), ${schema} (reference: copper_retirement).
-- Space-containing column names are backtick-quoted. Provisioning/execution is owned by ACC-DE-MV-DDL-PROVISION.
-- Synthetic-data note: see the view COMMENT below.

CREATE OR REPLACE VIEW ${catalog}.${schema}.copper_customers_impacted (
  `State` COMMENT 'US state code where the impacted copper device is deployed',
  `Device Type` COMMENT 'Type of copper network equipment affecting the customer',
  `Risk Tier` COMMENT 'Risk tier of the copper device impacting this customer — Critical devices require immediate migration',
  `Service Type` COMMENT 'Type of customer-facing service at risk: Voice (POTS/VoIP), Fixed Line (dedicated circuits), Broadband (DSL/internet)',
  `Customer Segment` COMMENT 'Business segment of the impacted customer',
  `Impact Category` COMMENT 'Category of service disruption the customer would face if the copper device is retired without migration',
  `Service Status` COMMENT 'Current lifecycle status of the customer-facing service',
  `Wire Center` COMMENT 'Wire center (central office) serving this customer allocation',
  `Criticality Level` COMMENT 'Criticality level of the device-service allocation — how important this specific service link is',
  `Modeled Footprint` COMMENT 'DEC-DSI-FOOTPRINT (2026-10-25): \'In modeled footprint\' = 6 legacy LakeLink states (CO, MN, WA, OR, ID, AZ), the only states with wire_center_boundary, copper_plant_wire_center_jurisdiction and the cited jurisdiction matrix. Other states have no wire center assignment (partner discovery input).',
  `Customers Impacted in Footprint` COMMENT 'HEADLINE per DEC-DSI-FOOTPRINT: unique customers impacted in the 6 legacy footprint states (CO, MN, WA, OR, ID, AZ). Synthetic demo data.',
  `Customers Outside Footprint` COMMENT 'Unique customers on devices outside the modeled footprint (no wire center). Reported separately, not merged into the headline (DEC-DSI-FOOTPRINT). Synthetic demo data.',
  `Devices Impacting Customers in Footprint` COMMENT 'Unique copper devices with customer allocations in the 6 legacy footprint states (DEC-DSI-FOOTPRINT).',
  `Customers Impacted` COMMENT 'Unique customers impacted across ALL states incl. outside the modeled footprint (national figure). The partner headline is Customers Impacted in Footprint (DEC-DSI-FOOTPRINT).',
  `Services at Risk` COMMENT 'Unique customer-facing services that depend on copper infrastructure and face disruption risk',
  `Devices Impacting Customers` COMMENT 'Unique copper devices that have customer service allocations — devices with direct customer impact',
  `Total Allocations` COMMENT 'Total device-to-service allocations — one device can serve multiple services',
  `Voice Services at Risk` COMMENT 'Voice services (POTS/VoIP) at risk from copper retirement — often subject to regulatory notice requirements',
  `Broadband Services at Risk` COMMENT 'Broadband services at risk from copper retirement',
  `Fixed Line Services at Risk` COMMENT 'Fixed line (dedicated circuit) services at risk from copper retirement',
  `Residential Customers` COMMENT 'Residential customers impacted — subject to FCC 90-day direct notice requirement (FCC 26-19)',
  `Enterprise Customers` COMMENT 'Enterprise customers impacted by copper retirement — typically higher revenue per customer',
  `Critical Impact Customers` COMMENT 'Customers served by critical-risk copper devices requiring immediate migration attention')
COMMENT 'DERIVED FROM SYNTHETIC DATA — Metric view: customers impacted by copper retirement — tracks customer count, service count, and business product count affected. Dimensions: state, wire_center, risk_tier, SLA_tier. Source: gold_wire_center_scorecard, gold_device_risk_predictions. Footprint split (DEC-DSI-FOOTPRINT 2026-10-25): headline = Customers Impacted in Footprint (6 legacy states); Customers Outside Footprint reported separately.'
WITH METRICS
LANGUAGE YAML
AS
$$
version: 1.1

source: ${catalog}.${schema}.silver_device_service_impact

comment: "DERIVED FROM SYNTHETIC DATA — Metric view: customers impacted by copper\
  \ retirement — tracks customer count, service count, and business product count\
  \ affected. Dimensions: state, wire_center, risk_tier, SLA_tier. Source: gold_wire_center_scorecard,\
  \ gold_device_risk_predictions. Footprint split (DEC-DSI-FOOTPRINT 2026-10-25):\
  \ headline = Customers Impacted in Footprint (6 legacy states); Customers Outside\
  \ Footprint reported separately."

dimensions:
  - name: State
    expr: state_code
    comment: US state code where the impacted copper device is deployed
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
    comment: Type of copper network equipment affecting the customer
    display_name: Device Type
    synonyms:
      - equipment type

  - name: Risk Tier
    expr: |-
      CASE computed_risk_tier
        WHEN 'critical' THEN 'Critical'
        WHEN 'high' THEN 'High'
        WHEN 'medium' THEN 'Medium'
        WHEN 'low' THEN 'Low'
        ELSE COALESCE(computed_risk_tier, 'Unknown')
      END
    comment: Risk tier of the copper device impacting this customer — Critical devices
      require immediate migration
    display_name: Risk Tier
    synonyms:
      - risk level
      - priority tier

  - name: Service Type
    expr: |-
      CASE service_type
        WHEN 'voice' THEN 'Voice'
        WHEN 'fixed_line' THEN 'Fixed Line'
        WHEN 'broadband' THEN 'Broadband'
        ELSE COALESCE(service_type, 'Unknown')
      END
    comment: "Type of customer-facing service at risk: Voice (POTS/VoIP), Fixed Line\
      \ (dedicated circuits), Broadband (DSL/internet)"
    display_name: Service Type
    synonyms:
      - service category
      - product type

  - name: Customer Segment
    expr: |-
      CASE customer_segment
        WHEN 'residential' THEN 'Residential'
        WHEN 'enterprise' THEN 'Enterprise'
        WHEN 'mid_market' THEN 'Mid-Market'
        WHEN 'sme' THEN 'SME'
        WHEN 'wholesale' THEN 'Wholesale'
        WHEN 'carrier' THEN 'Carrier'
        WHEN 'mvno' THEN 'MVNO'
        WHEN 'public_sector' THEN 'Public Sector'
        ELSE COALESCE(customer_segment, 'Unknown')
      END
    comment: Business segment of the impacted customer
    display_name: Customer Segment
    synonyms:
      - segment
      - customer type
      - market segment

  - name: Impact Category
    expr: |-
      CASE impact_category
        WHEN 'voice_disruption' THEN 'Voice Disruption'
        WHEN 'line_disruption' THEN 'Line Disruption'
        WHEN 'data_disruption' THEN 'Data Disruption'
        ELSE COALESCE(impact_category, 'Unknown')
      END
    comment: Category of service disruption the customer would face if the copper
      device is retired without migration
    display_name: Impact Category
    synonyms:
      - disruption type
      - impact type

  - name: Service Status
    expr: |-
      CASE service_status
        WHEN 'feasibility_checked' THEN 'Feasibility Checked'
        WHEN 'designed' THEN 'Designed'
        WHEN 'terminated' THEN 'Terminated'
        WHEN 'cancelled' THEN 'Cancelled'
        ELSE COALESCE(service_status, 'Unknown')
      END
    comment: Current lifecycle status of the customer-facing service
    display_name: Service Status
    synonyms:
      - service lifecycle

  - name: Wire Center
    expr: "COALESCE(wire_center_name, 'Unassigned')"
    comment: Wire center (central office) serving this customer allocation
    display_name: Wire Center
    synonyms:
      - central office
      - CO

  - name: Criticality Level
    expr: |-
      CASE criticality_level
        WHEN 'critical' THEN 'Critical'
        WHEN 'high' THEN 'High'
        WHEN 'medium' THEN 'Medium'
        WHEN 'low' THEN 'Low'
        ELSE COALESCE(criticality_level, 'Unknown')
      END
    comment: Criticality level of the device-service allocation — how important this
      specific service link is
    display_name: Criticality Level
    synonyms:
      - allocation priority

  - name: Modeled Footprint
    expr: "CASE WHEN state_code IN ('CO','MN','WA','OR','ID','AZ') THEN 'In modeled\
      \ footprint (6 legacy states)' ELSE 'Outside modeled footprint (no wire center)'\
      \ END"
    comment: "DEC-DSI-FOOTPRINT (2026-10-25): 'In modeled footprint' = 6 legacy LakeLink\
      \ states (CO, MN, WA, OR, ID, AZ), the only states with wire_center_boundary,\
      \ copper_plant_wire_center_jurisdiction and the cited jurisdiction matrix. Other\
      \ states have no wire center assignment (partner discovery input)."
    display_name: Modeled Footprint
    synonyms:
      - footprint
      - in footprint

measures:
  - name: Customers Impacted in Footprint
    expr: "COUNT(DISTINCT CASE WHEN state_code IN ('CO','MN','WA','OR','ID','AZ')\
      \ THEN customer_id END)"
    comment: "HEADLINE per DEC-DSI-FOOTPRINT: unique customers impacted in the 6 legacy\
      \ footprint states (CO, MN, WA, OR, ID, AZ). Synthetic demo data."
    display_name: Customers Impacted in Footprint
    format:
      type: number
      decimal_places:
        type: exact
        places: 0

  - name: Customers Outside Footprint
    expr: "COUNT(DISTINCT CASE WHEN state_code NOT IN ('CO','MN','WA','OR','ID','AZ')\
      \ OR state_code IS NULL THEN customer_id END)"
    comment: "Unique customers on devices outside the modeled footprint (no wire center).\
      \ Reported separately, not merged into the headline (DEC-DSI-FOOTPRINT). Synthetic\
      \ demo data."
    display_name: Customers Outside Footprint
    format:
      type: number
      decimal_places:
        type: exact
        places: 0

  - name: Devices Impacting Customers in Footprint
    expr: "COUNT(DISTINCT CASE WHEN state_code IN ('CO','MN','WA','OR','ID','AZ')\
      \ THEN physical_device_id END)"
    comment: Unique copper devices with customer allocations in the 6 legacy footprint
      states (DEC-DSI-FOOTPRINT).
    display_name: Devices Impacting Customers in Footprint

  - name: Customers Impacted
    expr: COUNT(DISTINCT customer_id)
    comment: Unique customers impacted across ALL states incl. outside the modeled
      footprint (national figure). The partner headline is Customers Impacted in Footprint
      (DEC-DSI-FOOTPRINT).
    display_name: Customers Impacted
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - affected customers
      - customer count
      - impacted customers

  - name: Services at Risk
    expr: COUNT(DISTINCT customer_facing_service_id)
    comment: Unique customer-facing services that depend on copper infrastructure
      and face disruption risk
    display_name: Services at Risk
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - affected services
      - service count

  - name: Devices Impacting Customers
    expr: COUNT(DISTINCT physical_device_id)
    comment: Unique copper devices that have customer service allocations — devices
      with direct customer impact
    display_name: Devices Impacting Customers
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - customer-facing devices

  - name: Total Allocations
    expr: COUNT(1)
    comment: Total device-to-service allocations — one device can serve multiple services
    display_name: Total Allocations
    format:
      type: number
      decimal_places:
        type: exact
        places: 0

  - name: Voice Services at Risk
    expr: COUNT(DISTINCT customer_facing_service_id) FILTER (WHERE service_type =
      'voice')
    comment: Voice services (POTS/VoIP) at risk from copper retirement — often subject
      to regulatory notice requirements
    display_name: Voice Services at Risk
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - voice lines affected
      - POTS at risk

  - name: Broadband Services at Risk
    expr: COUNT(DISTINCT customer_facing_service_id) FILTER (WHERE service_type =
      'broadband')
    comment: Broadband services at risk from copper retirement
    display_name: Broadband Services at Risk
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - DSL at risk
      - internet at risk

  - name: Fixed Line Services at Risk
    expr: COUNT(DISTINCT customer_facing_service_id) FILTER (WHERE service_type =
      'fixed_line')
    comment: Fixed line (dedicated circuit) services at risk from copper retirement
    display_name: Fixed Lines at Risk
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - dedicated circuits at risk

  - name: Residential Customers
    expr: COUNT(DISTINCT customer_id) FILTER (WHERE customer_segment = 'residential')
    comment: Residential customers impacted — subject to FCC 90-day direct notice
      requirement (FCC 26-19)
    display_name: Residential Customers
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - consumer customers
      - residential count

  - name: Enterprise Customers
    expr: COUNT(DISTINCT customer_id) FILTER (WHERE customer_segment = 'enterprise')
    comment: Enterprise customers impacted by copper retirement — typically higher
      revenue per customer
    display_name: Enterprise Customers
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - business customers
      - enterprise count

  - name: Critical Impact Customers
    expr: COUNT(DISTINCT customer_id) FILTER (WHERE computed_risk_tier = 'critical')
    comment: Customers served by critical-risk copper devices requiring immediate
      migration attention
    display_name: Critical Impact Customers
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - urgent migration customers
$$;
