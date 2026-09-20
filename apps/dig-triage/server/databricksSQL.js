/**
 * databricksSQL.js
 * Data layer for calling Databricks UC SQL functions via the Statement Execution API.
 * Used by dig-triage Express server to invoke incident_lookup, proximity_search,
 * and reroute_suggest UC functions.
 *
 * Auth: Uses DATABRICKS_TOKEN (auto-injected by Databricks Apps runtime).
 * Requires: DATABRICKS_HOST, DATABRICKS_WAREHOUSE_ID env vars.
 */

const DATABRICKS_HOST = process.env.DATABRICKS_HOST;
const WAREHOUSE_ID = process.env.DATABRICKS_WAREHOUSE_ID;

/**
 * Execute a SQL statement via the Databricks SQL Statement Execution API.
 * Returns an array of row objects with column names as keys.
 *
 * @param {string} statement - SQL statement to execute
 * @param {Array<{name:string, value:string, type?:string}>} [parameters] - Named parameters
 * @returns {Promise<Array<Record<string, any>>>}
 */
async function executeSQL(statement, parameters) {
  if (!DATABRICKS_HOST) throw new Error('DATABRICKS_HOST env var not set');
  if (!WAREHOUSE_ID) throw new Error('DATABRICKS_WAREHOUSE_ID env var not set');

  const token = process.env.DATABRICKS_TOKEN;
  if (!token) throw new Error('DATABRICKS_TOKEN not set — are you running inside Databricks Apps?');

  const url = `${DATABRICKS_HOST}/api/2.0/sql/statements`;

  const body = {
    warehouse_id: WAREHOUSE_ID,
    statement,
    wait_timeout: '30s',
    on_wait_timeout: 'CANCEL',
    format: 'JSON_ARRAY',
  };
  if (parameters && parameters.length > 0) {
    body.parameters = parameters;
  }

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`SQL API error ${res.status}: ${errText}`);
  }

  const data = await res.json();

  if (data.status?.state === 'FAILED') {
    throw new Error(
      `SQL execution failed: ${data.status.error?.message || 'unknown error'}`
    );
  }

  // Map result rows to objects
  const columns = data.manifest?.schema?.columns || [];
  const rows = data.result?.data_array || [];
  return rows.map((row) => {
    const obj = {};
    columns.forEach((col, i) => {
      obj[col.name] = row[i];
    });
    return obj;
  });
}

/**
 * Lookup a single incident by ID via the UC incident_lookup function.
 * @param {number} incidentId
 * @returns {Promise<object|null>}
 */
export async function incidentLookup(incidentId) {
  const id = parseInt(incidentId, 10);
  if (isNaN(id)) throw new Error(`Invalid incident ID: ${incidentId}`);

  const rows = await executeSQL(
    `SELECT * FROM cdm_tmforum.copper_retirement.incident_lookup(${id})`
  );
  return rows.length > 0 ? rows[0] : null;
}

/**
 * Search for incidents near a lat/lon point within a radius.
 * @param {number} latitude
 * @param {number} longitude
 * @param {number} [radiusKm=25]
 * @returns {Promise<Array<object>>}
 */
export async function proximitySearch(latitude, longitude, radiusKm = 25) {
  const lat = parseFloat(latitude);
  const lon = parseFloat(longitude);
  const radius = parseFloat(radiusKm);
  if (isNaN(lat) || isNaN(lon)) throw new Error('Invalid lat/lon');

  const rows = await executeSQL(
    `SELECT * FROM cdm_tmforum.copper_retirement.proximity_search(${lat}, ${lon}, ${radius})`
  );
  return rows;
}

/**
 * Get reroute suggestions for an incident.
 * @param {number} incidentId
 * @returns {Promise<object|null>}
 */
export async function rerouteSuggest(incidentId) {
  const id = parseInt(incidentId, 10);
  if (isNaN(id)) throw new Error(`Invalid incident ID: ${incidentId}`);

  const rows = await executeSQL(
    `SELECT * FROM cdm_tmforum.copper_retirement.reroute_suggest(${id})`
  );
  return rows.length > 0 ? rows[0] : null;
}

/**
 * Health check — verifies SQL connectivity.
 * @returns {Promise<boolean>}
 */
export async function healthCheck() {
  try {
    const rows = await executeSQL('SELECT 1 AS ok');
    return rows.length > 0 && rows[0].ok === '1';
  } catch {
    return false;
  }
}
