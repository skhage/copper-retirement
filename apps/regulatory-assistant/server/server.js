/**
 * server.js
 * Express backend for the Regulatory Assistant (P7-REG).
 * Serves the Vite-built React frontend from dist/.
 *
 * Live corpus endpoints query cdm_tmforum.copper_retirement.fcc_regulatory_document
 * via the Databricks SQL Statement Execution API.
 */
import express from 'express';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
app.use(express.json());

// ---------------------------------------------------------------------------
// Databricks SQL Statement Execution API helper
// ---------------------------------------------------------------------------
const CORPUS_TABLE = 'cdm_tmforum.copper_retirement.fcc_regulatory_document';

async function getAuthHeaders() {
  const token = process.env.DATABRICKS_TOKEN;
  if (token) return { Authorization: `Bearer ${token}` };
  // Databricks Apps OAuth M2M token exchange
  const clientId = process.env.DATABRICKS_CLIENT_ID;
  const clientSecret = process.env.DATABRICKS_CLIENT_SECRET;
  const host = process.env.DATABRICKS_HOST;
  if (clientId && clientSecret && host) {
    const tokenUrl = `https://${host.replace(/^https?:\/\//, '')}/oidc/v1/token`;
    const resp = await fetch(tokenUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: clientId,
        client_secret: clientSecret,
        scope: 'all-apis',
      }),
    });
    const data = await resp.json();
    if (data.access_token) return { Authorization: `Bearer ${data.access_token}` };
  }
  return null;
}

async function executeSql(statement, parameters = []) {
  const host = process.env.DATABRICKS_HOST;
  const warehouseId = process.env.DATABRICKS_WAREHOUSE_ID;
  if (!host || !warehouseId) return null;

  const authHeaders = await getAuthHeaders();
  if (!authHeaders) return null;

  const url = `https://${host.replace(/^https?:\/\//, '')}/api/2.0/sql/statements/`;
  const body = {
    warehouse_id: warehouseId,
    statement,
    wait_timeout: '30s',
    disposition: 'INLINE',
    format: 'JSON_ARRAY',
  };
  if (parameters.length > 0) body.parameters = parameters;

  const resp = await fetch(url, {
    method: 'POST',
    headers: { ...authHeaders, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  const data = await resp.json();
  if (data.status?.state !== 'SUCCEEDED') {
    const errMsg = data.status?.error?.message || JSON.stringify(data.status);
    throw new Error(`SQL error: ${errMsg}`);
  }

  const columns = data.manifest?.schema?.columns?.map((c) => c.name) || [];
  const rows = data.result?.data_array || [];
  return rows.map((row) =>
    Object.fromEntries(columns.map((col, i) => [col, row[i]]))
  );
}

// ---------------------------------------------------------------------------
// API: Search corpus (for RAG chat)
// ---------------------------------------------------------------------------
app.post('/api/corpus/search', async (req, res) => {
  try {
    const { query, jurisdiction } = req.body;
    if (!query) return res.status(400).json({ error: 'Missing query' });

    // Extract keywords (3+ chars, skip stop words)
    const stopWords = new Set([
      'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
      'her', 'was', 'one', 'our', 'out', 'has', 'have', 'what', 'when',
      'where', 'how', 'does', 'this', 'that', 'with', 'from', 'about',
      'would', 'could', 'should', 'will', 'been', 'were', 'they', 'them',
      'their', 'there', 'which', 'who', 'whom', 'into', 'than', 'then',
    ]);
    const keywords = query
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, '')
      .split(/\s+/)
      .filter((w) => w.length > 2 && !stopWords.has(w))
      .slice(0, 5);

    if (keywords.length === 0) {
      return res.json({
        documents: [],
        answer: 'Please provide more specific terms to search the regulatory corpus.',
      });
    }

    // Build parameterized search — each keyword matches across key columns
    const conditions = keywords.map(
      (_, i) =>
        `(LOWER(COALESCE(title,'')) LIKE CONCAT('%', :kw${i}, '%') OR ` +
        `LOWER(COALESCE(summary_text,'')) LIKE CONCAT('%', :kw${i}, '%') OR ` +
        `LOWER(COALESCE(full_text_excerpt,'')) LIKE CONCAT('%', :kw${i}, '%') OR ` +
        `LOWER(COALESCE(regulatory_topic,'')) LIKE CONCAT('%', :kw${i}, '%'))`
    );

    let whereClause = conditions.join(' OR ');
    const params = keywords.map((kw, i) => ({
      name: `kw${i}`,
      value: kw,
      type: 'STRING',
    }));

    if (jurisdiction && jurisdiction !== 'all') {
      whereClause = `(${whereClause}) AND (jurisdiction_state_code = :jurisdiction OR jurisdiction_state_code IN ('US') OR jurisdiction_state_code IS NULL)`;
      params.push({ name: 'jurisdiction', value: jurisdiction, type: 'STRING' });
    }

    const sql = `
      SELECT document_id, title, document_type, issuing_body,
             jurisdiction_state_code, effective_date, regulatory_topic,
             summary_text, LEFT(full_text_excerpt, 800) AS excerpt,
             citation_reference, docket_number, notice_period_days,
             word_count
      FROM ${CORPUS_TABLE}
      WHERE ${whereClause}
      ORDER BY effective_date DESC
      LIMIT 8
    `;

    const results = await executeSql(sql, params);
    if (!results) {
      return res.json({ documents: [], fallback: true });
    }

    res.json({ documents: results });
  } catch (err) {
    console.error('[corpus/search] Error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ---------------------------------------------------------------------------
// API: List documents (for Document Browser)
// ---------------------------------------------------------------------------
app.get('/api/corpus/documents', async (req, res) => {
  try {
    const { jurisdiction, document_type, search, limit } = req.query;
    const params = [];
    const conditions = [];

    if (jurisdiction && jurisdiction !== 'all') {
      conditions.push(
        `(jurisdiction_state_code = :jurisdiction OR jurisdiction_state_code IN ('US') OR jurisdiction_state_code IS NULL)`
      );
      params.push({ name: 'jurisdiction', value: jurisdiction, type: 'STRING' });
    }
    if (document_type && document_type !== 'all') {
      conditions.push(`document_type = :doc_type`);
      params.push({ name: 'doc_type', value: document_type, type: 'STRING' });
    }
    if (search) {
      conditions.push(
        `(LOWER(COALESCE(title,'')) LIKE CONCAT('%', LOWER(:search), '%') OR ` +
        `LOWER(COALESCE(summary_text,'')) LIKE CONCAT('%', LOWER(:search), '%') OR ` +
        `LOWER(COALESCE(regulatory_topic,'')) LIKE CONCAT('%', LOWER(:search), '%'))`
      );
      params.push({ name: 'search', value: search, type: 'STRING' });
    }

    const where = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
    const maxRows = Math.min(parseInt(limit) || 100, 500);

    const sql = `
      SELECT document_id, title, document_type, issuing_body,
             jurisdiction_state_code, effective_date, document_status,
             regulatory_topic, summary_text, citation_reference,
             docket_number, notice_period_days, word_count, page_count
      FROM ${CORPUS_TABLE}
      ${where}
      ORDER BY effective_date DESC
      LIMIT ${maxRows}
    `;

    const results = await executeSql(sql, params);
    if (!results) return res.json({ documents: [], fallback: true });

    res.json({ documents: results });
  } catch (err) {
    console.error('[corpus/documents] Error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ---------------------------------------------------------------------------
// API: KPIs from the live corpus
// ---------------------------------------------------------------------------
app.get('/api/corpus/kpis', async (req, res) => {
  try {
    const { jurisdiction } = req.query;
    const params = [];
    let jurisdictionFilter = '';

    if (jurisdiction && jurisdiction !== 'all') {
      jurisdictionFilter =
        `AND (jurisdiction_state_code = :jurisdiction OR jurisdiction_state_code IN ('US') OR jurisdiction_state_code IS NULL)`;
      params.push({ name: 'jurisdiction', value: jurisdiction, type: 'STRING' });
    }

    const sql = `
      SELECT
        COUNT(DISTINCT jurisdiction_state_code) AS jurisdictions_covered,
        COUNT(*) AS total_documents,
        COUNT(DISTINCT document_type) AS document_types,
        SUM(CASE WHEN document_type IN ('fcc_order', 'fcc_guidance', 'fcc_public_notice')
                 THEN 1 ELSE 0 END) AS federal_docs,
        SUM(CASE WHEN document_type IN ('state_puc_docket', 'state_governor_notice')
                 THEN 1 ELSE 0 END) AS state_docs,
        COALESCE(SUM(word_count), 0) AS total_words
      FROM ${CORPUS_TABLE}
      WHERE 1 = 1 ${jurisdictionFilter}
    `;

    const results = await executeSql(sql, params);
    if (!results || results.length === 0) {
      return res.json({ kpis: null, fallback: true });
    }

    res.json({ kpis: results[0] });
  } catch (err) {
    console.error('[corpus/kpis] Error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ---------------------------------------------------------------------------
// Static files + SPA fallback (must come AFTER API routes)
// ---------------------------------------------------------------------------
app.use(express.static(path.join(__dirname, '..', 'dist')));

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'dist', 'index.html'));
});

const port = parseInt(process.env.DATABRICKS_APP_PORT || '8000', 10);
app.listen(port, '0.0.0.0', () => {
  console.log(`[regulatory-assistant] Server listening on 0.0.0.0:${port}`);
  console.log(`  DATABRICKS_HOST: ${process.env.DATABRICKS_HOST ? 'set' : 'NOT SET'}`);
  console.log(`  DATABRICKS_WAREHOUSE_ID: ${process.env.DATABRICKS_WAREHOUSE_ID ? 'set' : 'NOT SET'}`);
  console.log(`  Auth: ${process.env.DATABRICKS_TOKEN ? 'TOKEN' : process.env.DATABRICKS_CLIENT_ID ? 'OAUTH' : 'NONE'}`);
});