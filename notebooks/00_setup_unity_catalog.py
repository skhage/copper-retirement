# Databricks notebook source
# MAGIC %md
# MAGIC # Unity Catalog foundation (AWS)
# MAGIC
# MAGIC This notebook is a rerunnable bootstrap fallback for the declarative resources in
# MAGIC `bundle/resources/unity_catalog.yml`. Supply an existing Unity Catalog storage
# MAGIC credential backed by an AWS IAM role. Do not use AWS access keys or secrets.
# MAGIC
# MAGIC The Asset Bundle remains authoritative for enforcing the raw external location as
# MAGIC read-only and for detecting configuration drift.

# COMMAND ----------

import sys
from pathlib import Path

from databricks.sdk import WorkspaceClient

sys.path.append(str(Path.cwd().parent))

from uc.setup import UnityCatalogConfig, build_setup_statements

dbutils.widgets.text("catalog_name", "lumen_copper")
dbutils.widgets.text("managed_external_location_name", "lumen_copper_managed")
dbutils.widgets.text("managed_storage_url", "")
dbutils.widgets.text("raw_external_location_name", "lumen_copper_raw")
dbutils.widgets.text("raw_storage_url", "")
dbutils.widgets.text("storage_credential_name", "")

config = UnityCatalogConfig(
    catalog_name=dbutils.widgets.get("catalog_name"),
    managed_external_location_name=dbutils.widgets.get(
        "managed_external_location_name"
    ),
    managed_storage_url=dbutils.widgets.get("managed_storage_url"),
    raw_external_location_name=dbutils.widgets.get("raw_external_location_name"),
    raw_storage_url=dbutils.widgets.get("raw_storage_url"),
    storage_credential_name=dbutils.widgets.get("storage_credential_name"),
)

# COMMAND ----------

for statement in build_setup_statements(config):
    spark.sql(statement)

workspace_client = WorkspaceClient()
workspace_client.external_locations.update(
    config.managed_external_location_name,
    credential_name=config.storage_credential_name,
    enable_file_events=False,
    fallback=False,
    read_only=False,
    skip_validation=False,
    url=config.managed_storage_url,
)
workspace_client.external_locations.update(
    config.raw_external_location_name,
    credential_name=config.storage_credential_name,
    enable_file_events=False,
    fallback=False,
    read_only=True,
    skip_validation=False,
    url=config.raw_storage_url,
)

display(
    spark.sql(f"SHOW SCHEMAS IN `{config.catalog_name}`").where(
        "databaseName IN ('bronze', 'silver', 'gold', 'ml', 'ops', 'agents')"
    )
)

# COMMAND ----------

display(
    spark.sql("SHOW EXTERNAL LOCATIONS").where(
        f"name IN ('{config.managed_external_location_name}', "
        f"'{config.raw_external_location_name}')"
    )
)
