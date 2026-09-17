# Databricks notebook source
# DBTITLE 1,Header
# MAGIC %md
# MAGIC # Copper Risk Model — Monitoring & Drift Activation
# MAGIC # project: copper-retirement | developer: copper-ml
# MAGIC
# MAGIC **Purpose:** Verify and activate Lakehouse Monitoring for the V5 copper-retirement-risk model.  
# MAGIC **Run this notebook** after CEO enables auto-capture on the serving endpoint.  
# MAGIC **Monitor target:** `cdm_tmforum.copper_retirement.risk_inference_unpacked`  
# MAGIC **Baseline reference:** `copper-retirement/resources/monitoring_baseline.md`  
# MAGIC **MLflow experiment:** `/Users/stephen.hage@databricks.com/copper-retirement/experiments/copper_risk_classifier`