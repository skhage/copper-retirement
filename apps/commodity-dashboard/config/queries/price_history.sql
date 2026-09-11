-- price_history.sql
-- Historical copper commodity prices for the price chart.
-- Source: cdm_tmforum.copper_retirement.copper_commodity_price
--         (pending P0-DATAGEN-COMMODITY-EXECUTE, ~6K rows, daily 2018-2025)
--
-- Modeled after refinitiv_fx_source.gl_daily_rates schema:
--   trade_date, price_type (spot/3m_forward/15m_forward),
--   open_usd_per_mt, high_usd_per_mt, low_usd_per_mt, close_usd_per_mt,
--   volume_lots, volatility_30d
--
-- NOTE: Table does not exist yet. This query is ready for when it lands.
-- Mock data is used in the app until then.

-- SELECT
--   trade_date,
--   price_type,
--   close_usd_per_mt / 2204.62 AS close_usd_per_lb,  -- MT to lb conversion
--   open_usd_per_mt / 2204.62 AS open_usd_per_lb,
--   high_usd_per_mt / 2204.62 AS high_usd_per_lb,
--   low_usd_per_mt / 2204.62 AS low_usd_per_lb,
--   volume_lots,
--   volatility_30d
-- FROM cdm_tmforum.copper_retirement.copper_commodity_price
-- WHERE price_type IN ('spot', '3m_forward', '15m_forward')
-- ORDER BY trade_date, price_type

-- Proxy: use FX rates date range to show available temporal coverage
SELECT
  MIN(CONVERSION_DATE) AS min_date,
  MAX(CONVERSION_DATE) AS max_date,
  COUNT(*) AS total_rows,
  COUNT(DISTINCT FROM_CURRENCY) AS currencies
FROM cdm_tmforum.refinitiv_fx_source.gl_daily_rates
