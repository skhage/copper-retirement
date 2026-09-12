# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,P2-H3: Populate H3 Indexes
# MAGIC %md
# MAGIC # P2-H3: Populate H3 Index Columns
# MAGIC
# MAGIC **Task:** Populate h3_res8 and h3_res9 columns on 3 tables using `h3_longlatash3(longitude, latitude, resolution)`.
# MAGIC
# MAGIC **Prerequisites (completed by @data-engineer 2026-09-12):**
# MAGIC - `ALTER TABLE ADD COLUMNS` executed on all 3 tables (columns exist, all NULL)
# MAGIC - H3 function validated: 100% conversion rate on 10K addresses
# MAGIC - FK chains validated: physical_device → geographic_address (100%), CFS → geographic_address (100%)
# MAGIC
# MAGIC **Run All cells below to populate.**

# COMMAND ----------

# DBTITLE 1,Cell 1: Populate geographic_address H3 columns
# MAGIC %sql
# MAGIC -- Step 1: Populate h3_res8 and h3_res9 on geographic_address (10K rows)
# MAGIC -- h3_longlatash3 takes (longitude, latitude, resolution) — note lon FIRST
# MAGIC MERGE INTO cdm_tmforum.tmf_shared.geographic_address AS target
# MAGIC USING (
# MAGIC   SELECT 
# MAGIC     geographic_address_id,
# MAGIC     h3_longlatash3(longitude, latitude, 8) AS h3_res8_new,
# MAGIC     h3_longlatash3(longitude, latitude, 9) AS h3_res9_new
# MAGIC   FROM cdm_tmforum.tmf_shared.geographic_address
# MAGIC   WHERE latitude IS NOT NULL AND longitude IS NOT NULL
# MAGIC ) AS source
# MAGIC ON target.geographic_address_id = source.geographic_address_id
# MAGIC WHEN MATCHED THEN UPDATE SET
# MAGIC   target.h3_res8 = source.h3_res8_new,
# MAGIC   target.h3_res9 = source.h3_res9_new

# COMMAND ----------

# DBTITLE 1,Cell 2: Populate physical_device H3 via geographic_address FK join
# MAGIC %sql
# MAGIC -- Step 2: Populate h3_res8 and h3_res9 on physical_device via geographic_address_id FK
# MAGIC -- 10K devices, 2,672 copper (cpe/ont/olt/patch_panel), 100% FK match
# MAGIC MERGE INTO cdm_tmforum.tmf_enterprise.physical_device AS target
# MAGIC USING (
# MAGIC   SELECT 
# MAGIC     pd.physical_device_id,
# MAGIC     h3_longlatash3(ga.longitude, ga.latitude, 8) AS h3_res8_new,
# MAGIC     h3_longlatash3(ga.longitude, ga.latitude, 9) AS h3_res9_new
# MAGIC   FROM cdm_tmforum.tmf_enterprise.physical_device pd
# MAGIC   JOIN cdm_tmforum.tmf_shared.geographic_address ga 
# MAGIC     ON pd.geographic_address_id = ga.geographic_address_id
# MAGIC   WHERE ga.latitude IS NOT NULL AND ga.longitude IS NOT NULL
# MAGIC ) AS source
# MAGIC ON target.physical_device_id = source.physical_device_id
# MAGIC WHEN MATCHED THEN UPDATE SET
# MAGIC   target.h3_res8 = source.h3_res8_new,
# MAGIC   target.h3_res9 = source.h3_res9_new

# COMMAND ----------

# DBTITLE 1,Cell 3: Populate CFS H3 via geographic_address FK join
# MAGIC %sql
# MAGIC -- Step 3: Populate h3_res8 and h3_res9 on customer_facing_service via geographic_address_id FK
# MAGIC -- 100K CFS rows, 17,655 copper (voice/fixed_line/broadband), 100% FK match
# MAGIC MERGE INTO cdm_tmforum.tmf_service.customer_facing_service AS target
# MAGIC USING (
# MAGIC   SELECT 
# MAGIC     cfs.customer_facing_service_id,
# MAGIC     h3_longlatash3(ga.longitude, ga.latitude, 8) AS h3_res8_new,
# MAGIC     h3_longlatash3(ga.longitude, ga.latitude, 9) AS h3_res9_new
# MAGIC   FROM cdm_tmforum.tmf_service.customer_facing_service cfs
# MAGIC   JOIN cdm_tmforum.tmf_shared.geographic_address ga 
# MAGIC     ON cfs.geographic_address_id = ga.geographic_address_id
# MAGIC   WHERE ga.latitude IS NOT NULL AND ga.longitude IS NOT NULL
# MAGIC ) AS source
# MAGIC ON target.customer_facing_service_id = source.customer_facing_service_id
# MAGIC WHEN MATCHED THEN UPDATE SET
# MAGIC   target.h3_res8 = source.h3_res8_new,
# MAGIC   target.h3_res9 = source.h3_res9_new

# COMMAND ----------

# DBTITLE 1,Cell 4: Validate H3 population
# MAGIC %sql
# MAGIC -- Step 4: Validate H3 population across all 3 tables
# MAGIC SELECT 'geographic_address' AS table_name, COUNT(*) AS total, COUNT(h3_res8) AS h3_res8_pop, COUNT(h3_res9) AS h3_res9_pop, COUNT(DISTINCT h3_res8) AS distinct_res8, COUNT(DISTINCT h3_res9) AS distinct_res9
# MAGIC FROM cdm_tmforum.tmf_shared.geographic_address
# MAGIC UNION ALL
# MAGIC SELECT 'physical_device', COUNT(*), COUNT(h3_res8), COUNT(h3_res9), COUNT(DISTINCT h3_res8), COUNT(DISTINCT h3_res9)
# MAGIC FROM cdm_tmforum.tmf_enterprise.physical_device
# MAGIC UNION ALL
# MAGIC SELECT 'customer_facing_service', COUNT(*), COUNT(h3_res8), COUNT(h3_res9), COUNT(DISTINCT h3_res8), COUNT(DISTINCT h3_res9)
# MAGIC FROM cdm_tmforum.tmf_service.customer_facing_service