# Databricks notebook source
# DBTITLE 1,Manual Inference Log Demo
# MAGIC %md
# MAGIC # project: copper-retirement | developer: copper-ml
# MAGIC
# MAGIC # Manual Inference Logging: Copper Retirement Risk Model
# MAGIC
# MAGIC Workaround notebook for demo visibility while auto-capture is pending CEO enablement.  
# MAGIC This notebook:
# MAGIC 1. Assembles features for **sample device segments** (5 per device_type × risk_tier)
# MAGIC 2. Calls the **copper-retirement-risk** serving endpoint via REST
# MAGIC 3. Captures request/response payloads with timing
# MAGIC 4. **INSERTs** into `cdm_tmforum.copper_retirement.risk_model_inference_payload`
# MAGIC
# MAGIC **Task:** ML-MANUAL-INF-LOG-DEMO | **Model:** V5 LightGBM (39 features, 4-class)

# COMMAND ----------

# DBTITLE 1,Configuration
# Configuration
CATALOG = "cdm_tmforum"
SCHEMA = "copper_retirement"
MODEL_NAME = f"{CATALOG}.ml_models.copper_retirement_risk"
MODEL_ALIAS = "champion"
ENDPOINT_NAME = "copper-retirement-risk"
INFERENCE_TABLE = f"{CATALOG}.{SCHEMA}.risk_model_inference_payload"
RISK_TIERS = ["low", "medium", "high", "critical"]

# Sampling: devices per (device_type x risk_tier) segment
SAMPLES_PER_SEGMENT = 5

# Batch size for endpoint calls (devices per request)
BATCH_SIZE = 10

# COMMAND ----------

# DBTITLE 1,Assemble features (reused from batch_score_copper_risk)
from pyspark.sql import functions as F
import mlflow

mlflow.set_registry_uri("databricks-uc")
client = mlflow.MlflowClient()

# Resolve champion version for metadata
model_version = client.get_model_version_by_alias(MODEL_NAME, MODEL_ALIAS)
print(f"Champion: {MODEL_NAME} v{model_version.version}")

# --- Feature assembly (mirrors batch_score_copper_risk) ---
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

dispute = spark.table(f"{CATALOG}.{SCHEMA}.feature_device_billing_dispute").select(
    "physical_device_id",
    F.col("dispute_count").cast("double"),
    F.col("escalated_dispute_count").cast("double"),
    F.col("sla_breach_dispute_count").cast("double"),
    F.col("months_since_last_dispute").cast("double"),
)

complaint = spark.table(f"{CATALOG}.{SCHEMA}.feature_device_complaint_rate").select(
    "physical_device_id",
    F.col("complaint_count").cast("double"),
    F.col("complaint_rate_per_month").cast("double"),
    F.col("escalated_complaint_count").cast("double"),
    F.col("high_severity_count").cast("double").alias("high_severity_complaint_count"),
    F.col("avg_resolution_hours").cast("double").alias("complaint_avg_resolution_hours"),
)

usage = spark.table(f"{CATALOG}.{SCHEMA}.feature_device_service_usage").select(
    "physical_device_id",
    F.col("active_months").cast("double"),
    F.col("avg_monthly_usage").cast("double"),
    F.col("avg_monthly_revenue").cast("double"),
)

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

# Device type encoding (training-time order: cpe=0, ont=1, olt=2, patch_panel=3)
device_type_map = {"cpe": 0.0, "ont": 1.0, "olt": 2.0, "patch_panel": 3.0}
mapping_expr = F.create_map([F.lit(x) for pair in device_type_map.items() for x in pair])

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

# DBTITLE 1,Sample devices by segment (device_type x risk_tier)
from pyspark.sql import Window
import random

# Stratified sample: SAMPLES_PER_SEGMENT devices per (device_type, risk_tier)
w = Window.partitionBy("device_type", "risk_tier").orderBy(F.rand(seed=42))

sampled = (
    features_df
    .withColumn("_rank", F.row_number().over(w))
    .filter(F.col("_rank") <= SAMPLES_PER_SEGMENT)
    .drop("_rank")
)

sampled_pdf = sampled.toPandas()
print(f"Sampled {len(sampled_pdf)} devices across {sampled_pdf.groupby(['device_type','risk_tier']).ngroups} segments")
print(f"\nSegment counts:")
print(sampled_pdf.groupby(['device_type', 'risk_tier']).size().unstack(fill_value=0).to_string())

# Model feature columns (39 features, same order as model signature)
FEATURE_COLS = [
    "alarm_count", "critical_alarm_rate", "service_affecting_rate",
    "sla_breach_count", "sla_breach_rate", "test_fail_rate",
    "problem_count", "recurring_problem_rate",
    "dispute_count", "escalated_dispute_count", "sla_breach_dispute_count",
    "months_since_last_dispute",
    "complaint_count", "complaint_rate_per_month", "escalated_complaint_count",
    "high_severity_complaint_count", "complaint_avg_resolution_hours",
    "active_months", "avg_monthly_usage", "avg_monthly_revenue",
    "device_age_days", "firmware_obsolescence_score", "days_since_last_patch",
    "days_past_eol", "days_past_support_expiry",
    "is_past_eol", "is_support_expired", "has_vulnerabilities",
    "has_upgrade_blocked", "has_upgrade_ineligible",
    "installed_software_count", "has_software_data",
    "plant_pair_count", "avg_loop_length_ft", "avg_splice_count",
    "avg_cable_vintage_year", "avg_db_loss", "moisture_rate",
    "device_type_encoded",
]

# COMMAND ----------

# DBTITLE 1,Call serving endpoint via SDK and capture inference logs
import json
import uuid
import time
from datetime import datetime, timezone
from collections import Counter

# Use SDK for authenticated endpoint calls
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
requester = w.current_user.me().user_name
served_entity_id = "copper_retirement_risk-5"

# Score in batches and capture inference logs
inference_records = []
total_devices = len(sampled_pdf)
num_batches = (total_devices + BATCH_SIZE - 1) // BATCH_SIZE
tier_map = {0: 'low', 1: 'medium', 2: 'high', 3: 'critical'}

print(f"Scoring {total_devices} devices in {num_batches} batches via SDK...\n")

for batch_idx in range(num_batches):
    start = batch_idx * BATCH_SIZE
    end = min(start + BATCH_SIZE, total_devices)
    batch_pdf = sampled_pdf.iloc[start:end]
    
    # Build request payload
    records = batch_pdf[FEATURE_COLS].to_dict(orient="records")
    for rec in records:
        for k, v in rec.items():
            rec[k] = float(v) if v is not None else 0.0
    
    request_json = json.dumps({"dataframe_records": records})
    segment_label = f"manual-demo-batch-{batch_idx:03d}"
    
    # Call endpoint via SDK with timing
    request_time = datetime.now(timezone.utc)
    t0 = time.time()
    try:
        resp = w.serving_endpoints.query(
            name=ENDPOINT_NAME,
            dataframe_records=records
        )
        elapsed_ms = int((time.time() - t0) * 1000)
        status_code = 200
        response_json = json.dumps({"predictions": resp.predictions})
    except Exception as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        status_code = 500
        response_json = json.dumps({"error": str(e)})
    
    inference_records.append({
        "databricks_request_id": str(uuid.uuid4()),
        "request_date": request_time.date(),
        "client_request_id": segment_label,
        "request_time": request_time,
        "status_code": status_code,
        "sampling_fraction": 1.0,
        "execution_duration_ms": elapsed_ms,
        "request": request_json,
        "response": response_json,
        "logging_error_codes": None,
        "served_entity_id": served_entity_id,
        "requester": requester,
    })
    
    # Progress with prediction distribution
    tier_counts = batch_pdf['risk_tier'].value_counts().to_dict()
    status_icon = "\u2705" if status_code == 200 else "\u274c"
    pred_display = ""
    if status_code == 200:
        pred_names = [tier_map.get(p, '?') for p in resp.predictions]
        pred_display = f" \u2192 {dict(Counter(pred_names))}"
    print(f"  Batch {batch_idx+1}/{num_batches}: {end-start} devices, {status_icon} HTTP {status_code}, {elapsed_ms}ms | actual: {tier_counts}{pred_display}")

print(f"\nDone: {len(inference_records)} inference log records")
success_count = sum(1 for r in inference_records if r['status_code'] == 200)
print(f"Success: {success_count}/{len(inference_records)} batches")
if success_count > 0:
    latencies = [r['execution_duration_ms'] for r in inference_records if r['status_code'] == 200]
    print(f"Latency: avg {sum(latencies)//len(latencies)}ms, min {min(latencies)}ms, max {max(latencies)}ms")

# COMMAND ----------

# DBTITLE 1,INSERT inference logs into payload table
import pandas as pd
from pyspark.sql.types import (
    StructType, StructField, StringType, DateType, TimestampType,
    IntegerType, DoubleType, LongType, ArrayType,
)

# Build DataFrame matching inference table schema
inf_schema = StructType([
    StructField("databricks_request_id", StringType(), True),
    StructField("request_date", DateType(), True),
    StructField("client_request_id", StringType(), True),
    StructField("request_time", TimestampType(), True),
    StructField("status_code", IntegerType(), True),
    StructField("sampling_fraction", DoubleType(), True),
    StructField("execution_duration_ms", LongType(), True),
    StructField("request", StringType(), True),
    StructField("response", StringType(), True),
    StructField("logging_error_codes", ArrayType(StringType()), True),
    StructField("served_entity_id", StringType(), True),
    StructField("requester", StringType(), True),
])

inf_pdf = pd.DataFrame(inference_records)
inf_spark = spark.createDataFrame(inf_pdf, schema=inf_schema)

# Append (not overwrite) to preserve existing test rows
inf_spark.write.mode("append").saveAsTable(INFERENCE_TABLE)

print(f"\n✅ Inserted {len(inference_records)} inference log records into {INFERENCE_TABLE}")

# Verify
total = spark.sql(f"SELECT COUNT(*) FROM {INFERENCE_TABLE}").collect()[0][0]
print(f"Total rows in inference table: {total}")

# COMMAND ----------

# DBTITLE 1,Summary: inference log verification
# Summary report of manual inference logs
print("=" * 70)
print("MANUAL INFERENCE LOG DEMO — SUMMARY")
print("=" * 70)

summary = spark.sql(f"""
    SELECT 
        request_date,
        client_request_id,
        status_code,
        execution_duration_ms,
        LENGTH(request) as request_bytes,
        LENGTH(response) as response_bytes
    FROM {INFERENCE_TABLE}
    WHERE client_request_id LIKE 'manual-demo-batch-%'
    ORDER BY request_time
""")
summary.show(50, False)

# Risk tier distribution from responses
from pyspark.sql.functions import from_json, explode, col
print("\nPrediction distribution (from endpoint responses):")
resp_df = spark.sql(f"""
    SELECT 
        get_json_object(response, '$.predictions') as predictions
    FROM {INFERENCE_TABLE}
    WHERE client_request_id LIKE 'manual-demo-batch-%' AND status_code = 200
""")
for row in resp_df.collect():
    preds = json.loads(row.predictions) if row.predictions else []
    tier_map = {0: 'low', 1: 'medium', 2: 'high', 3: 'critical'}
    tier_names = [tier_map.get(p, f'unknown({p})') for p in preds]
    from collections import Counter
    counts = Counter(tier_names)
    print(f"  {dict(counts)}")

print(f"\n\u2705 ML-MANUAL-INF-LOG-DEMO complete.")
print(f"Inference table: {INFERENCE_TABLE}")
print(f"Model: {MODEL_NAME} v{model_version.version} ({MODEL_ALIAS})")
print(f"Devices scored: {total_devices} (stratified sample across all segments)")