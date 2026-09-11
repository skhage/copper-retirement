-- fx_rates.sql
-- Latest FX rates for copper pricing context (LME is USD-denominated).
-- Source: cdm_tmforum.refinitiv_fx_source.gl_daily_rates (23K rows, AVAILABLE NOW)

SELECT
  FROM_CURRENCY,
  TO_CURRENCY,
  CONVERSION_DATE,
  CONVERSION_RATE,
  SOURCE
FROM cdm_tmforum.refinitiv_fx_source.gl_daily_rates
WHERE CONVERSION_DATE = (
  SELECT MAX(CONVERSION_DATE)
  FROM cdm_tmforum.refinitiv_fx_source.gl_daily_rates
)
ORDER BY FROM_CURRENCY
