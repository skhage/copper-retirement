# copper-retirement
Help telcos use data to retire outdated services, reduce costs and gain one-time revenue

## Unity Catalog foundation

The bundle creates a Unity Catalog catalog, the `bronze`, `silver`, `gold`,
`ml`, `ops`, and `agents` schemas, and two AWS external locations:

- a writable, dedicated S3 prefix for managed catalog storage
- a separate read-only S3 prefix for raw synthetic/public source files

Create the Unity Catalog storage credential separately using an AWS IAM role and
Databricks' generated external ID. Do not use IAM-user access keys. The deployer
needs permission to create external locations with that credential and to create
catalogs in the workspace metastore.

Authenticate the Databricks CLI for the target workspace, then validate and
deploy without checking workspace URLs, role names, bucket names, or secrets
into source control:

```bash
databricks bundle validate --strict \
  --var="managed_storage_url=s3://<bucket>/<prefix>/managed" \
  --var="raw_storage_url=s3://<bucket>/<prefix>/raw" \
  --var="storage_credential_name=<uc-storage-credential>"

databricks bundle deploy \
  --var="managed_storage_url=s3://<bucket>/<prefix>/managed" \
  --var="raw_storage_url=s3://<bucket>/<prefix>/raw" \
  --var="storage_credential_name=<uc-storage-credential>"
```

`notebooks/00_setup_unity_catalog.py` provides an idempotent bootstrap fallback
that also reconciles external-location URLs, credentials, and read-only flags.
The bundle remains authoritative for deployment lifecycle and destroy protection.
