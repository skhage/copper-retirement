# Databricks notebook source
# DBTITLE 1,Batch Score: Copper Retirement Risk — Champion Model
# MAGIC %md
# MAGIC # Batch Score: Copper Retirement Risk
# MAGIC
# MAGIC Weekly batch scoring job that:
# MAGIC 1. Loads the **champion** model (`cdm_tmforum.ml_models.copper_retirement_risk@champion`)
# MAGIC 2. Assembles features from `copper_risk_target` + feature tables
# MAGIC 3. Scores all 2,672 copper devices
# MAGIC 4. Writes predictions to `cdm_tmforum.copper_retirement.copper_risk_predictions`
# MAGIC
# MAGIC **Schedule:** Weekly (or on DLP pipeline refresh)

# COMMAND ----------

# DBTITLE 1,Configuration
# Configuration
CATALOG = "cdm_tmforum"
SCHEMA = "copper_retirement"
MODEL_NAME = f"{CATALOG}.ml_models.copper_retirement_risk"
MODEL_ALIAS = "champion"
OUTPUT_TABLE = f"{CATALOG}.{SCHEMA}.copper_risk_predictions"
RISK_TIERS = ["low", "medium", "high", "critical"]

# COMMAND ----------

# DBTITLE 1,Load champion model metadata
import mlflow
from datetime import datetime

mlflow.set_registry_uri("databricks-uc")
client = mlflow.MlflowClient()

# Resolve champion version
model_uri = f"models:/{MODEL_NAME}@{MODEL_ALIAS}"
model_info = mlflow.models.get_model_info(model_uri)
model_version = client.get_model_version_by_alias(MODEL_NAME, MODEL_ALIAS)

print(f"Champion model: {MODEL_NAME} v{model_version.version}")
print(f"Run ID: {model_version.run_id}")
print(f"Features: {len(model_info.signature.inputs)} input columns")

# COMMAND ----------

# DBTITLE 1,Assemble feature DataFrame
from pyspark.sql import functions as F

# Base device features from copper_risk_target
base = spark.table(f"{CATALOG}.{SCHEMA}.copper_risk_target").select(
    "physical_device_id", "device_type", "device_status", "risk_tier",
    F.col("alarm_count").cast("double"),
    F.col("critical_alarm_rate").cast("double"),
    F.col("service_affecting_rate").cast("double"),
    F.col("sla_breach_count").cast("double"),
    F.col("sla_breach_rate").cast("double"),
    F.col("test_fail_rate").cast("double"),
    F.col("problem_count").cast("double"),
    F.col("recurring_problem_rate").cast("double"),
)

# Billing dispute features
dispute = spark.table(f"{CATALOG}.{SCHEMA}.feature_device_billing_dispute").select(
    "physical_device_id",
    F.col("dispute_count").cast("double"),
    F.col("escalated_dispute_count").cast("double"),
    F.col("sla_breach_dispute_count").cast("double"),
    F.col("months_since_last_dispute").cast("double"),
)

# Complaint features
complaint = spark.table(f"{CATALOG}.{SCHEMA}.feature_device_complaint_rate").select(
    "physical_device_id",
    F.col("complaint_count").cast("double"),
    F.col("complaint_rate_per_month").cast("double"),
    F.col("escalated_complaint_count").cast("double"),
    F.col("high_severity_count").cast("double").alias("high_severity_complaint_count"),
    F.col("avg_resolution_hours").cast("double").alias("complaint_avg_resolution_hours"),
)

# Service usage features
usage = spark.table(f"{CATALOG}.{SCHEMA}.feature_device_service_usage").select(
    "physical_device_id",
    F.col("active_months").cast("double"),
    F.col("avg_monthly_usage").cast("double"),
    F.col("avg_monthly_revenue").cast("double"),
)

# Firmware age features
firmware = spark.table(f"{CATALOG}.{SCHEMA}.feature_device_firmware_age").select(
    F.col("physical_device_id").alias("fw_device_id"),
    F.col("device_age_days").cast("double"),
    F.col("firmware_obsolescence_score").cast("double"),
    F.col("days_since_last_patch").cast("double"),
    F.col("days_past_eol").cast("double"),
    F.col("days_past_support_expiry").cast("double"),
    F.col("is_past_eol").cast("double"),
    F.col("is_support_expired").cast("double"),
    F.col("has_vulnerabilities").cast("double"),
    F.col("has_upgrade_blocked").cast("double"),
    F.col("has_upgrade_ineligible").cast("double"),
    F.col("installed_software_count").cast("double"),
    F.col("has_software_data").cast("double"),
)

# Plant features (aggregated per device)
plant = (
    spark.table(f"{CATALOG}.{SCHEMA}.copper_loop_plant")
    .groupBy("physical_device_id")
    .agg(
        F.count("*").cast("double").alias("plant_pair_count"),
        F.avg("loop_length_ft").cast("double").alias("avg_loop_length_ft"),
        F.avg("splice_point_count").cast("double").alias("avg_splice_count"),
        F.avg("cable_vintage_year").cast("double").alias("avg_cable_vintage_year"),
        F.avg("test_result_db_loss").cast("double").alias("avg_db_loss"),
        F.avg(F.col("moisture_detected").cast("double")).alias("moisture_rate"),
    )
)

# Device type encoding (training-time order — NOT alphabetical: cpe=0, ont=1, olt=2, patch_panel=3)
device_type_map = {"cpe": 0.0, "ont": 1.0, "olt": 2.0, "patch_panel": 3.0}
mapping_expr = F.create_map([F.lit(x) for pair in device_type_map.items() for x in pair])

# Join all features
features_df = (
    base
    .join(dispute, "physical_device_id", "left")
    .join(complaint, "physical_device_id", "left")
    .join(usage, "physical_device_id", "left")
    .join(firmware, base.physical_device_id == firmware.fw_device_id, "left")
    .drop("fw_device_id")
    .join(plant, "physical_device_id", "left")
    .withColumn("device_type_encoded", mapping_expr[F.col("device_type")])
    .fillna(0.0)
)

print(f"Feature DataFrame: {features_df.count()} rows, {len(features_df.columns)} columns")

# COMMAND ----------

# DBTITLE 1,Build predictions output table
# Map predicted class index back to risk tier label
risk_tier_udf = F.udf(lambda idx: RISK_TIERS[idx] if idx is not None and 0 <= idx < len(RISK_TIERS) else None)

# For class probabilities, load the native sklearn-flavored model (stable API)
import pandas as pd

try:
    native_model = mlflow.sklearn.load_model(model_uri)
except Exception:
    native_model = mlflow.lightgbm.load_model(model_uri)

input_pdf = features_df.select(*feature_cols).toPandas()
proba = native_model.predict_proba(input_pdf)

proba_df = pd.DataFrame(proba, columns=[f"prob_{t}" for t in RISK_TIERS])
proba_df["predicted_class"] = proba_df[[f"prob_{t}" for t in RISK_TIERS]].values.argmax(axis=1)
proba_df["predicted_risk_tier"] = proba_df["predicted_class"].map(dict(enumerate(RISK_TIERS)))
proba_df["max_confidence"] = proba_df[[f"prob_{t}" for t in RISK_TIERS]].max(axis=1)

# Combine with device identifiers
id_cols = features_df.select("physical_device_id", "device_type", "device_status", "risk_tier").toPandas()
result_pdf = pd.concat([id_cols.reset_index(drop=True), proba_df.reset_index(drop=True)], axis=1)
result_pdf["model_version"] = int(model_version.version)
result_pdf["model_run_id"] = model_version.run_id
result_pdf["scored_at"] = datetime.utcnow()

# Select final columns matching output schema
result_pdf = result_pdf[[
    "physical_device_id", "device_type", "device_status", "risk_tier",
    "predicted_risk_tier", "prob_low", "prob_medium", "prob_high", "prob_critical",
    "max_confidence", "model_version", "model_run_id", "scored_at",
]]

print(f"Predictions: {len(result_pdf)} devices scored")
print(f"\nRisk tier distribution:")
print(result_pdf["predicted_risk_tier"].value_counts().to_string())

# COMMAND ----------

# DBTITLE 1,Write predictions to Unity Catalog
# Overwrite predictions table with latest scores
result_spark = spark.createDataFrame(result_pdf)
result_spark.write.mode("overwrite").saveAsTable(OUTPUT_TABLE)

print(f"\nWrote {result_spark.count()} predictions to {OUTPUT_TABLE}")
print(f"Model: {MODEL_NAME} v{model_version.version} ({MODEL_ALIAS})")
print(f"Scored at: {datetime.utcnow().isoformat()}")