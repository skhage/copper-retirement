# Databricks notebook source
# DBTITLE 1,Batch Score: Copper Retirement Risk — Champion Model
# MAGIC %md
# MAGIC # Batch Score: Copper Retirement Risk
# MAGIC
# MAGIC > **SYNTHETIC DATA** — features come from the synthetic Lakelink Fiber TMF SID dataset.
# MAGIC
# MAGIC Weekly batch scoring job that:
# MAGIC 1. Loads the **champion** model (`<catalog>.<model_schema>.copper_retirement_risk@champion`)
# MAGIC 2. Assembles features from `copper_risk_target` + feature tables
# MAGIC 3. Scores all copper devices (2,672 in the demo dataset)
# MAGIC 4. Writes predictions to `<catalog>.<schema>.copper_risk_predictions`
# MAGIC
# MAGIC **Section 2 (optional, `run_inference_demo=true`)** — manual inference logging demo (merged from the retired `scripts/manual_inference_log_demo`, ACC-NB-DEMO-CONSOLIDATE): samples devices per device_type x risk_tier, calls the serving endpoint and appends request/response payloads to `risk_model_inference_payload`.
# MAGIC
# MAGIC **Parameters (widgets / job params):** `catalog`, `schema`, `model_schema`, `serving_endpoint`, `run_inference_demo`. Defaults match the bundle variables in `databricks.yml`.
# MAGIC
# MAGIC **Schedule:** Weekly (or on pipeline refresh)

# COMMAND ----------

# DBTITLE 1,Configuration
# Configuration — parameterized (ACC-DE-PARAMETERIZE); defaults mirror databricks.yml bundle variables
dbutils.widgets.text("catalog", "cdm_tmforum")
dbutils.widgets.text("schema", "copper_retirement")
dbutils.widgets.text("model_schema", "ml_models")
dbutils.widgets.text("serving_endpoint", "copper-retirement-risk")
dbutils.widgets.dropdown("run_inference_demo", "false", ["false", "true"])

CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
MODEL_NAME = f"{CATALOG}.{dbutils.widgets.get('model_schema')}.copper_retirement_risk"
MODEL_ALIAS = "champion"
ENDPOINT_NAME = dbutils.widgets.get("serving_endpoint")
RUN_INFERENCE_DEMO = dbutils.widgets.get("run_inference_demo") == "true"
OUTPUT_TABLE = f"{CATALOG}.{SCHEMA}.copper_risk_predictions"
INFERENCE_TABLE = f"{CATALOG}.{SCHEMA}.risk_model_inference_payload"
RISK_TIERS = ["low", "medium", "high", "critical"]

# Inference demo sampling (Section 2)
SAMPLES_PER_SEGMENT = 5
BATCH_SIZE = 10

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

print(f"Feature DataFrame: {features_df.count()} rows, {len(features_df.columns)} columns")

# COMMAND ----------

# DBTITLE 1,Materialize copper_risk_features (partner retrain feature table)
# ACC-DE-RISK-FEATURE-TABLE: persist the 39-feature contract + label + fairness slices as
# <catalog>.<schema>.copper_risk_features (default feature_table of the partner retrain template).
# SYNTHETIC DATA. INSERT OVERWRITE keeps the table's column comments and telco_project tag.
seg = spark.sql(f"""
  SELECT physical_device_id, max_by(customer_segment, n) AS customer_segment FROM (
    SELECT physical_device_id, customer_segment, count(*) n
    FROM {CATALOG}.{SCHEMA}.silver_device_service_impact
    WHERE customer_segment IS NOT NULL GROUP BY 1, 2) GROUP BY 1""")
st = spark.table(f"{CATALOG}.{SCHEMA}.silver_copper_plant_enriched").groupBy("physical_device_id").agg(F.first("state_code").alias("state_code"))
region_expr = (
    F.when(F.col("state_code").isin("WA","OR","ID","MT","WY","CO","UT","NV","CA","AK","HI"), "West")
     .when(F.col("state_code").isin("AZ","NM","TX","OK"), "Southwest")
     .when(F.col("state_code").isin("MN","WI","MI","IA","MO","IL","IN","OH","ND","SD","NE","KS"), "Midwest")
     .when(F.col("state_code").isin("ME","NH","VT","MA","RI","CT","NY","NJ","PA","DE","MD","DC"), "Northeast")
     .when(F.col("state_code").isNotNull(), "Southeast").otherwise("unknown"))
risk_features = (
    features_df.join(seg, "physical_device_id", "left").join(st, "physical_device_id", "left")
    .withColumn("region", region_expr)
    .withColumn("customer_segment", F.coalesce("customer_segment", F.lit("unknown")))
    .select("physical_device_id", *[F.col(c).cast("double") for c in FEATURE_COLS], "risk_tier", "device_type", "region", "customer_segment")
)
FEATURE_TABLE = f"{CATALOG}.{SCHEMA}.copper_risk_features"
risk_features.createOrReplaceTempView("_risk_features")
if spark.catalog.tableExists(FEATURE_TABLE):
    spark.sql(f"INSERT OVERWRITE {FEATURE_TABLE} SELECT * FROM _risk_features")
else:
    risk_features.write.saveAsTable(FEATURE_TABLE)
    spark.sql(f"ALTER TABLE {FEATURE_TABLE} SET TAGS ('telco_project'='copper-retirement')")
    spark.sql(f"COMMENT ON TABLE {FEATURE_TABLE} IS 'SYNTHETIC DEMO DATA. 39-feature risk model contract + risk_tier label + fairness slices (device_type, region, customer_segment).'")
print(f"{FEATURE_TABLE}: {spark.table(FEATURE_TABLE).count()} rows")

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

input_pdf = features_df.select(*FEATURE_COLS).toPandas()
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

# COMMAND ----------

# DBTITLE 1,Section 2: Manual inference logging demo
# MAGIC %md
# MAGIC ## Section 2 — Manual inference logging demo (optional)
# MAGIC
# MAGIC Runs only when `run_inference_demo=true`. Merged from the retired `scripts/manual_inference_log_demo` (ACC-NB-DEMO-CONSOLIDATE). Samples `SAMPLES_PER_SEGMENT` devices per device_type x risk_tier, calls the `serving_endpoint` in batches, and **appends** request/response payloads to `risk_model_inference_payload` so the drift monitor has traffic in a fresh demo workspace. **SYNTHETIC DATA.**

# COMMAND ----------

# DBTITLE 1,Demo: sample devices by segment
if not RUN_INFERENCE_DEMO:
    dbutils.notebook.exit("Batch scoring complete; inference demo skipped (run_inference_demo=false).")

from pyspark.sql import Window

# Stratified sample: SAMPLES_PER_SEGMENT devices per (device_type, risk_tier)
seg_window = Window.partitionBy("device_type", "risk_tier").orderBy(F.rand(seed=42))
sampled_pdf = (
    features_df
    .withColumn("_rank", F.row_number().over(seg_window))
    .filter(F.col("_rank") <= SAMPLES_PER_SEGMENT)
    .drop("_rank")
    .toPandas()
)
print(f"Sampled {len(sampled_pdf)} devices across {sampled_pdf.groupby(['device_type','risk_tier']).ngroups} segments")
print(sampled_pdf.groupby(['device_type', 'risk_tier']).size().unstack(fill_value=0).to_string())

# COMMAND ----------

# DBTITLE 1,Demo: call serving endpoint and capture inference logs
import json, uuid, time
from datetime import timezone
from collections import Counter
from databricks.sdk import WorkspaceClient

ws = WorkspaceClient()
requester = ws.current_user.me().user_name
served_entity_id = f"{MODEL_NAME.split('.')[-1]}-{model_version.version}"
tier_map = dict(enumerate(RISK_TIERS))

inference_records = []
total_devices = len(sampled_pdf)
num_batches = (total_devices + BATCH_SIZE - 1) // BATCH_SIZE
print(f"Scoring {total_devices} devices in {num_batches} batches against {ENDPOINT_NAME}...")

for batch_idx in range(num_batches):
    batch_pdf = sampled_pdf.iloc[batch_idx * BATCH_SIZE:(batch_idx + 1) * BATCH_SIZE]
    records = [{k: float(v) if v is not None else 0.0 for k, v in rec.items()}
               for rec in batch_pdf[FEATURE_COLS].to_dict(orient="records")]
    request_time = datetime.now(timezone.utc)
    t0 = time.time()
    try:
        resp = ws.serving_endpoints.query(name=ENDPOINT_NAME, dataframe_records=records)
        status_code, response_json = 200, json.dumps({"predictions": resp.predictions})
    except Exception as e:
        resp, status_code, response_json = None, 500, json.dumps({"error": str(e)})
    elapsed_ms = int((time.time() - t0) * 1000)
    inference_records.append({
        "databricks_request_id": str(uuid.uuid4()),
        "request_date": request_time.date(),
        "client_request_id": f"manual-demo-batch-{batch_idx:03d}",
        "request_time": request_time,
        "status_code": status_code,
        "sampling_fraction": 1.0,
        "execution_duration_ms": elapsed_ms,
        "request": json.dumps({"dataframe_records": records}),
        "response": response_json,
        "logging_error_codes": None,
        "served_entity_id": served_entity_id,
        "requester": requester,
    })
    preds = dict(Counter(tier_map.get(p, '?') for p in resp.predictions)) if resp else {}
    print(f"  Batch {batch_idx+1}/{num_batches}: HTTP {status_code}, {elapsed_ms}ms -> {preds}")

print(f"Success: {sum(r['status_code'] == 200 for r in inference_records)}/{len(inference_records)} batches")

# COMMAND ----------

# DBTITLE 1,Demo: append inference logs to payload table
from pyspark.sql.types import (
    StructType, StructField, StringType, DateType, TimestampType,
    IntegerType, DoubleType, LongType, ArrayType,
)

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

# Append (not overwrite) to preserve existing rows
spark.createDataFrame(pd.DataFrame(inference_records), schema=inf_schema).write.mode("append").saveAsTable(INFERENCE_TABLE)
print(f"Inserted {len(inference_records)} records into {INFERENCE_TABLE}")

display(spark.sql(f"""
    SELECT request_date, client_request_id, status_code, execution_duration_ms,
           LENGTH(request) AS request_bytes, LENGTH(response) AS response_bytes
    FROM {INFERENCE_TABLE}
    WHERE client_request_id LIKE 'manual-demo-batch-%'
    ORDER BY request_time DESC
    LIMIT 50
"""))