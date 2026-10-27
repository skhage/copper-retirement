CREATE TABLE IF NOT EXISTS {fq}.`copper_commodity_price_official` (
  `price_month` DATE COMMENT 'First day of the observation month (IMF monthly average)',
  `copper_price_usd_ton` DOUBLE COMMENT 'Global copper price, USD per metric ton, monthly average (IMF PCOPPUSDM benchmark)',
  `copper_price_usd_lb` DOUBLE COMMENT 'Derived: copper_price_usd_ton / 2204.62262 (USD per pound). Not a COMEX quote',
  `price_source` STRING COMMENT 'Publisher and series identifier of the price',
  `source_url` STRING COMMENT 'Official human-readable citation URL for the series',
  `download_url` STRING COMMENT 'Exact URL the raw CSV was downloaded from',
  `retrieved_at` TIMESTAMP COMMENT 'UTC timestamp when the CSV was downloaded',
  `sha256` STRING COMMENT 'SHA-256 hash of the downloaded raw CSV, for audit and reproducibility',
  `bytes` BIGINT COMMENT 'Size in bytes of the downloaded raw CSV',
  `http_status` INT COMMENT 'HTTP status code of the download',
  `volume_path` STRING COMMENT 'UC volume path of the raw downloaded CSV',
  `is_synthetic` BOOLEAN COMMENT 'FALSE = real public data. Always false in this table'
) USING DELTA
COMMENT 'REAL (non-synthetic) monthly global copper price: IMF Primary Commodity Price System series PCOPPUSDM (Global price of Copper, USD per metric ton, monthly average, not seasonally adjusted), retrieved from FRED (Federal Reserve Bank of St. Louis), https://fred.stlouisfed.org/series/PCOPPUSDM. Authoritative citable price for the partner ROI calculator and salvage value. One row per month. Supersedes the synthetic copper_commodity_price for any partner-facing $ figures. Raw CSV kept in the regulatory_source_docs volume. Note: IMF benchmark price, not a licensed LME settlement feed.'