CREATE TABLE IF NOT EXISTS {fq}.`gold_commodity_price_forecast` (
  `forecast_month` STRING COMMENT 'Year-month of the forecast period (YYYY-MM format).',
  `region` STRING COMMENT 'Geographic region for this forecast (CO, MN, WA, OR, ID, AZ).',
  `copper_lme_forecast_usd_ton` DOUBLE COMMENT 'Forecasted LME copper price in USD per metric ton.',
  `copper_comex_forecast_usd_lb` DOUBLE COMMENT 'Forecasted COMEX copper price in USD per pound.',
  `fiber_cable_forecast_usd_km` DOUBLE COMMENT 'Forecasted fiber optic cable cost in USD per kilometer.',
  `labor_cost_index_forecast` DOUBLE COMMENT 'Forecasted regional labor cost index (base 100). Drives contractor cost estimates.',
  `material_cost_index_forecast` DOUBLE COMMENT 'Forecasted material cost index (base 100). Includes conduit, splice closures, etc.',
  `model_version` STRING COMMENT 'Version identifier of the forecasting model.',
  `forecast_generated_date` STRING COMMENT 'Date the forecast was generated.'
) USING DELTA
COMMENT 'SYNTHETIC DATA — Gold layer: forecasted copper/fiber commodity prices, labor costs, and material cost indices by region. One row per commodity_type per forecast_date per region. Sources: copper_commodity_price historical data with time-series forecasting. Used in Beat 4 commodity dashboard.'