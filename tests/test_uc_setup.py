import pytest

from uc.setup import SCHEMAS, UnityCatalogConfig, build_setup_statements


def _config(**overrides):
    values = {
        "catalog_name": "lumen_copper",
        "managed_external_location_name": "lumen_copper_managed",
        "managed_storage_url": "s3://example-bucket/copper-retirement/managed/",
        "raw_external_location_name": "lumen_copper_raw",
        "raw_storage_url": "s3://example-bucket/copper-retirement/raw/",
        "storage_credential_name": "copper_retirement_role",
    }
    values.update(overrides)
    return UnityCatalogConfig(**values)


def test_config_normalizes_s3_urls():
    config = _config()
    assert config.managed_storage_url == "s3://example-bucket/copper-retirement/managed"
    assert config.raw_storage_url == "s3://example-bucket/copper-retirement/raw"


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("managed_storage_url", "https://example.com/managed"),
        ("raw_storage_url", "s3://example-bucket"),
        ("raw_storage_url", "s3://example-bucket/raw?version=1"),
    ],
)
def test_config_rejects_unsafe_storage_urls(field_name, value):
    with pytest.raises(ValueError):
        _config(**{field_name: value})


@pytest.mark.parametrize(
    "raw_url",
    [
        "s3://example-bucket/copper-retirement/managed",
        "s3://example-bucket/copper-retirement/managed/raw",
        "s3://example-bucket/copper-retirement",
    ],
)
def test_config_rejects_overlapping_storage_prefixes(raw_url):
    with pytest.raises(ValueError, match="non-overlapping"):
        _config(raw_storage_url=raw_url)


def test_config_rejects_unsafe_identifiers():
    with pytest.raises(ValueError, match="catalog_name"):
        _config(catalog_name="lumen-copper; DROP CATALOG main")


def test_setup_statements_are_ordered_and_idempotent():
    statements = build_setup_statements(_config())
    assert len(statements) == 3 + len(SCHEMAS)
    assert statements[0].startswith("CREATE EXTERNAL LOCATION IF NOT EXISTS")
    assert statements[1].startswith("CREATE EXTERNAL LOCATION IF NOT EXISTS")
    assert statements[2].startswith("CREATE CATALOG IF NOT EXISTS")
    assert all(
        statement.startswith("CREATE SCHEMA IF NOT EXISTS")
        for statement in statements[3:]
    )


def test_setup_statements_use_role_credential_without_secrets():
    sql = "\n".join(build_setup_statements(_config()))
    assert "WITH (STORAGE CREDENTIAL `copper_retirement_role`)" in sql
    assert "ACCESS_KEY" not in sql
    assert "SECRET" not in sql
    assert "PASSWORD" not in sql


def test_setup_statements_create_every_required_schema():
    sql = "\n".join(build_setup_statements(_config()))
    for schema_name in SCHEMAS:
        assert f"`lumen_copper`.`{schema_name}`" in sql
