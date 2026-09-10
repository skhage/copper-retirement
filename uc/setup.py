"""Build safe, rerunnable Unity Catalog bootstrap SQL for Databricks on AWS."""

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

SCHEMAS = ("bronze", "silver", "gold", "ml", "ops", "agents")
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,254}$")


def _validate_identifier(value: str, field_name: str) -> str:
    if not _IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(
            f"{field_name} must start with a letter or underscore and contain only "
            "letters, numbers, and underscores"
        )
    return value


def _normalize_s3_url(value: str, field_name: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "s3" or not parsed.netloc:
        raise ValueError(f"{field_name} must be an s3:// URL with a bucket name")
    if parsed.query or parsed.fragment:
        raise ValueError(f"{field_name} must not contain a query string or fragment")

    path_parts = [part for part in parsed.path.split("/") if part]
    if not path_parts:
        raise ValueError(
            f"{field_name} must use a dedicated prefix below the bucket root"
        )
    if any(part in {".", ".."} for part in path_parts):
        raise ValueError(f"{field_name} must not contain relative path segments")

    return f"s3://{parsed.netloc}/{'/'.join(path_parts)}"


def _paths_overlap(left: str, right: str) -> bool:
    left_prefix = left.rstrip("/") + "/"
    right_prefix = right.rstrip("/") + "/"
    return (
        left == right or left.startswith(right_prefix) or right.startswith(left_prefix)
    )


def _quote_identifier(value: str) -> str:
    return f"`{value}`"


def _quote_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


@dataclass(frozen=True)
class UnityCatalogConfig:
    catalog_name: str
    managed_external_location_name: str
    managed_storage_url: str
    raw_external_location_name: str
    raw_storage_url: str
    storage_credential_name: str

    def __post_init__(self) -> None:
        for field_name in (
            "catalog_name",
            "managed_external_location_name",
            "raw_external_location_name",
            "storage_credential_name",
        ):
            object.__setattr__(
                self,
                field_name,
                _validate_identifier(getattr(self, field_name), field_name),
            )

        object.__setattr__(
            self,
            "managed_storage_url",
            _normalize_s3_url(self.managed_storage_url, "managed_storage_url"),
        )
        object.__setattr__(
            self,
            "raw_storage_url",
            _normalize_s3_url(self.raw_storage_url, "raw_storage_url"),
        )
        if _paths_overlap(self.managed_storage_url, self.raw_storage_url):
            raise ValueError(
                "managed_storage_url and raw_storage_url must use non-overlapping S3 prefixes"
            )


def build_setup_statements(config: UnityCatalogConfig) -> list[str]:
    """Return ordered, idempotent SQL statements for UC bootstrap."""
    managed_location = _quote_identifier(config.managed_external_location_name)
    raw_location = _quote_identifier(config.raw_external_location_name)
    credential = _quote_identifier(config.storage_credential_name)
    catalog = _quote_identifier(config.catalog_name)

    statements = [
        f"""CREATE EXTERNAL LOCATION IF NOT EXISTS {managed_location}
URL {_quote_string(config.managed_storage_url)}
WITH (STORAGE CREDENTIAL {credential})
COMMENT 'Writable managed storage for the copper-retirement catalog'""",
        f"""CREATE EXTERNAL LOCATION IF NOT EXISTS {raw_location}
URL {_quote_string(config.raw_storage_url)}
WITH (STORAGE CREDENTIAL {credential})
COMMENT 'Read-only raw landing area for synthetic and public source files'""",
        f"""CREATE CATALOG IF NOT EXISTS {catalog}
MANAGED LOCATION {_quote_string(config.managed_storage_url)}
COMMENT 'Copper-retirement demo; internal plant data is synthetic or simulated'""",
    ]
    statements.extend(
        f"CREATE SCHEMA IF NOT EXISTS {catalog}.{_quote_identifier(schema_name)} "
        f"COMMENT {_quote_string(_schema_comment(schema_name))}"
        for schema_name in SCHEMAS
    )
    return statements


def _schema_comment(schema_name: str) -> str:
    comments = {
        "bronze": "Raw landed synthetic and public source data",
        "silver": "Cleaned, conformed, and H3-indexed data",
        "gold": "Business-ready copper-retirement data products",
        "ml": "Model training data and ML lifecycle assets",
        "ops": "Lakebase-synchronized operational data",
        "agents": "Agent definitions, evaluation sets, and traces",
    }
    return comments[schema_name]
