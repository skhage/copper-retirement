/**
 * routes/regulatory.js — Regulatory tab API (ACC-APP-PORT-REG). Mounted at /api/regulatory.
 * Ported from the retired standalone regulatory-assistant app (2026-10-24); its synthetic corpus
 * (fcc_regulatory_document, copper_app.regulatory_documents) is NOT ported — real sources only.
 *
 * Data (reused, nothing new created — directive 13):
 *   ${CATALOG}.${SCHEMA}.jurisdiction_requirements_cited  (68 rows, REAL, official_url on every row)
 *   ${CATALOG}.${SCHEMA}.regulatory_source_register       (40 rows, REAL)
 *   ${CATALOG}.${SCHEMA}.regulatory_doc_chunks            (is_synthetic = false only: 1,419 real chunks)
 *   LLM: pay-per-token ${LLM_ENDPOINT} via ai_query on the existing SQL warehouse.
 *
 * Citation contract: every row/answer carries source title + official URL. Answers that cite no [S#]
 * are replaced with "No official source found for this question." (BRAND_GUIDE §0.2).
 * Retrieval (ACC-ML-REG-ASK-51D-RECALL, 2026-10-26) = hybrid over real chunks, no VS dependency (DEC-VS-OPTIONAL):
 *   bge-large cosine (same embedding as search_regulatory_chunks TVF) + keyword rank, fused by RRF, with a small
 *   boost for codified rules (CFR/USC) and verbatim section-number hits, max 2 chunks per source for diversity.
 *   Falls back to keyword-only scoring if the embedding call fails.
 * All user input is passed as named SQL parameters (no string interpolation).
 */
import express from 'express';
import { executeSQL } from '../databricksSQL.js';

const CATALOG = process.env.CATALOG || 'cdm_tmforum';
const SCHEMA = process.env.SCHEMA || 'copper_retirement';
const FQ = `${CATALOG}.${SCHEMA}`;
const LLM_ENDPOINT_RAW = process.env.LLM_ENDPOINT || 'databricks-claude-sonnet-4-5';
// Endpoint name is config (not user input) but is inlined into ai_query, so whitelist its charset.
const LLM_ENDPOINT = /^[A-Za-z0-9_-]+$/.test(LLM_ENDPOINT_RAW) ? LLM_ENDPOINT_RAW : 'databricks-claude-sonnet-4-5';
const NO_SOURCE = 'No official source found for this question.';

const P = (name, value) => ({ name, value: String(value), type: 'STRING' });
const jurOf = (v) => (v && /^[A-Za-z]{2}$/.test(v) ? v.toUpperCase() : 'ALL');

const STOP = new Set(('the a an and or of to in on for with by is are be what which who when how does do i we our my ' +
  'must need required require any all about from that this there their it its can should under rule rules state').split(' '));
function keywords(q) {
  const words = String(q || '').toLowerCase().match(/[a-z0-9.]{3,}/g) || [];
  const out = [];
  for (const w of words) {
    const k = w.replace(/\.+$/, '');
    if (k.length >= 3 && !STOP.has(k) && !out.includes(k)) out.push(k.length > 7 ? k.slice(0, 7) : k); // crude stem
    if (out.length === 6) break;
  }
  return out;
}

async function fetchMatrix(jur) {
  return executeSQL(`
    SELECT m.requirement_key, m.jurisdiction_code, m.jurisdiction_name, m.jurisdiction_level, m.requirement_type,
      m.requirement_summary, CAST(m.value_numeric AS STRING) AS value_numeric, m.value_unit, m.verification_status,
      m.source_id, m.citation, m.official_url, m.notes, COALESCE(r.title, m.citation) AS source_title,
      CAST(r.last_verified AS STRING) AS last_verified,
      -- ACC-APP-JUR-CITATION-URL: section-level page that contains the cited value (falls back to the source URL)
      COALESCE(m.citation_url, m.official_url) AS citation_url,
      CAST(COALESCE(m.citation_url_verified_on, r.last_verified) AS STRING) AS citation_verified_on
    FROM ${FQ}.jurisdiction_requirements_cited m
    LEFT JOIN ${FQ}.regulatory_source_register r ON r.source_id = m.source_id
    -- ACC-DES-DEF-REG-MATRIX-HIDDEN-GAPS: rows without official_url are returned (shown as flagged gaps), never hidden.
    WHERE m.is_synthetic = false
      AND (:jur = 'ALL' OR m.jurisdiction_code IN ('US', :jur))
    ORDER BY CASE m.jurisdiction_code WHEN 'US' THEN 0 ELSE 1 END, m.jurisdiction_code, m.requirement_type`,
  [P('jur', jur)]);
}

async function fetchSources() {
  return executeSQL(`
    SELECT source_id, jurisdiction, level, authority, topic, title, citation, official_url, verification_status,
      CAST(last_verified AS STRING) AS last_verified, CAST(effective_date AS STRING) AS effective_date
    FROM ${FQ}.regulatory_source_register
    WHERE is_synthetic = false AND official_url IS NOT NULL
    ORDER BY CASE level WHEN 'federal' THEN 0 ELSE 1 END, jurisdiction, title`);
}

async function fetchKpis() {
  const [m = {}] = await executeSQL(`
    SELECT COUNT(*) AS requirements,
      -- verified = verified_* status AND an official URL; gaps = everything else (matches the matrix 'Flagged gap' cells)
      COUNT_IF(upper(verification_status) LIKE 'VERIFIED\\_%' AND official_url IS NOT NULL) AS verified,
      COUNT_IF(NOT (coalesce(upper(verification_status), '') LIKE 'VERIFIED\\_%' AND official_url IS NOT NULL)) AS gaps,
      COUNT(DISTINCT jurisdiction_code) AS jurisdictions
    FROM ${FQ}.jurisdiction_requirements_cited WHERE is_synthetic = false`);
  const [s = {}] = await executeSQL(`
    SELECT COUNT(*) AS sources, COUNT_IF(lower(verification_status) LIKE 'verified\\_%') AS verified_sources
    FROM ${FQ}.regulatory_source_register WHERE is_synthetic = false`);
  const [c = {}] = await executeSQL(`SELECT COUNT(*) AS real_chunks FROM ${FQ}.regulatory_doc_chunks WHERE is_synthetic = false`);
  const n = (v) => parseInt(v, 10) || 0;
  return { requirements: n(m.requirements), verified: n(m.verified), gaps: n(m.gaps), jurisdictions: n(m.jurisdictions),
    sources: n(s.sources), verified_sources: n(s.verified_sources), real_chunks: n(c.real_chunks) };
}

// Section numbers like 51.333 or 63.71 in the question (matched verbatim in chunk text).
function sections(q) {
  return [...new Set(String(q || '').match(/\b\d{1,3}\.\d{2,4}\b/g) || [])].slice(0, 3);
}

async function retrieveHybrid(question, jur) {
  const ks = keywords(question);
  const ss = sections(question);
  const kw = ks.map((_, i) => `CASE WHEN ch.embedding_text ILIKE '%' || :k${i} || '%' THEN 1 ELSE 0 END`).join(' + ') || '0';
  const sec = ss.map((_, i) => `CASE WHEN ch.embedding_text LIKE '%' || :s${i} || '%' THEN 1 ELSE 0 END`).join(' + ') || '0';
  return executeSQL(`
    WITH qv AS (SELECT ai_query('databricks-bge-large-en', :q, returnType => 'ARRAY<FLOAT>') AS v),
    base AS (
      SELECT ch.chunk_id, ch.source_id, ch.title, ch.citation, ch.source_url, ch.jurisdiction,
        substr(ch.embedding_text, 1, 1600) AS excerpt,
        aggregate(zip_with(ch.embedding, qv.v, (a, b) -> CAST(a AS DOUBLE) * b), 0D, (acc, x) -> acc + x)
          / (sqrt(aggregate(ch.embedding, 0D, (acc, x) -> acc + CAST(x AS DOUBLE) * x))
             * sqrt(aggregate(qv.v, 0D, (acc, x) -> acc + CAST(x AS DOUBLE) * x))) AS sem,
        (${kw}) AS kw, (${sec}) AS sec_hit,
        CASE WHEN ch.citation ILIKE '%CFR%' OR ch.citation ILIKE '%U.S.C%' THEN 1 ELSE 0 END AS codified
      FROM ${FQ}.regulatory_doc_chunks ch CROSS JOIN qv
      WHERE ch.is_synthetic = false AND ch.source_url IS NOT NULL AND ch.embedding IS NOT NULL
        AND (:jur = 'ALL' OR ch.jurisdiction IN ('US', :jur))),
    r AS (SELECT *, row_number() OVER (ORDER BY sem DESC) AS rs, row_number() OVER (ORDER BY kw DESC, sem DESC) AS rk FROM base),
    f AS (SELECT *, 1.0 / (60 + rs) + 1.0 / (60 + rk) + 0.004 * codified + 0.01 * sec_hit
            + CASE WHEN :jur <> 'ALL' AND jurisdiction = :jur THEN 0.004 ELSE 0 END AS score FROM r),
    d AS (SELECT *, row_number() OVER (PARTITION BY source_id ORDER BY score DESC) AS per_src FROM f)
    SELECT d.chunk_id, d.source_id, d.title, d.citation, d.source_url, d.jurisdiction, d.excerpt, d.score,
      rg.verification_status, CAST(rg.last_verified AS STRING) AS last_verified
    FROM d LEFT JOIN ${FQ}.regulatory_source_register rg ON rg.source_id = d.source_id
    WHERE d.per_src <= 2
    ORDER BY d.score DESC, d.chunk_id LIMIT 6`,
  [P('q', String(question).slice(0, 1000)), P('jur', jur), ...ks.map((k, i) => P(`k${i}`, k)), ...ss.map((s, i) => P(`s${i}`, s))]);
}

async function retrieve(question, jur) {
  try {
    const rows = await retrieveHybrid(question, jur);
    if (rows.length) return rows;
  } catch (err) {
    console.error('[accelerator:regulatory] hybrid retrieval failed, falling back to keyword:', err.message);
  }
  return retrieveKeyword(question, jur);
}

async function retrieveKeyword(question, jur) {
  const ks = keywords(question);
  if (!ks.length) return [];
  const score = ks.map((_, i) => `CASE WHEN ch.embedding_text ILIKE '%' || :k${i} || '%' THEN 1 ELSE 0 END`).join(' + ');
  return executeSQL(`
    WITH c AS (
      SELECT ch.chunk_id, ch.source_id, ch.title, ch.citation, ch.source_url, ch.jurisdiction,
        substr(ch.embedding_text, 1, 1200) AS excerpt,
        (${score}) + CASE WHEN :jur <> 'ALL' AND ch.jurisdiction = :jur THEN 2 ELSE 0 END AS score
      FROM ${FQ}.regulatory_doc_chunks ch
      WHERE ch.is_synthetic = false AND ch.source_url IS NOT NULL
        AND (:jur = 'ALL' OR ch.jurisdiction IN ('US', :jur)))
    SELECT c.*, r.verification_status, CAST(r.last_verified AS STRING) AS last_verified
    FROM c LEFT JOIN ${FQ}.regulatory_source_register r ON r.source_id = c.source_id
    WHERE c.score > ${ks.length > 1 ? 1 : 0}
    ORDER BY c.score DESC, c.chunk_id LIMIT 5`,
  [P('jur', jur), ...ks.map((k, i) => P(`k${i}`, k))]);
}

async function ask(question, jur) {
  const chunks = await retrieve(question, jur);
  const sources = chunks.map((c, i) => ({ n: i + 1, chunk_id: c.chunk_id, source_id: c.source_id, title: c.title,
    citation: c.citation, url: c.source_url, jurisdiction: c.jurisdiction, verification_status: c.verification_status,
    last_verified: c.last_verified, excerpt: (c.excerpt || '').slice(0, 400) }));
  if (!sources.length) return { answer: NO_SOURCE, grounded: false, sources: [], mode: 'no_real_sources' };

  const ctx = chunks.map((c, i) => `[S${i + 1}] ${c.title} (${c.citation})\n${c.excerpt}`).join('\n\n');
  const prompt = 'You answer copper-retirement regulatory questions for a telecom carrier. Answer ONLY from the numbered ' +
    'official sources below. End every sentence with its citation like [S1]. Never invent rule numbers, deadlines or URLs. ' +
    "If the sources do not answer the question, start the reply with 'INSUFFICIENT SOURCES:' and say what is missing. " +
    `Max 150 words.\n\nQuestion: ${String(question).slice(0, 500)}\n\nSources:\n${ctx}`;
  let answer = null;
  try {
    const [r] = await executeSQL(`SELECT ai_query('${LLM_ENDPOINT}', :prompt) AS answer`, [P('prompt', prompt)]);
    answer = r?.answer || null;
  } catch (err) {
    console.error('[accelerator:regulatory] ai_query failed:', err.message);
    return { answer: null, grounded: false, sources, mode: 'passages_only', llm_error: 'LLM unavailable; showing cited passages only.' };
  }
  const cited = [...new Set((answer?.match(/\[S(\d+)\]/g) || []).map((m) => parseInt(m.slice(2), 10)))]
    .filter((k) => k >= 1 && k <= sources.length);
  const insufficient = /^\s*INSUFFICIENT SOURCES:/i.test(answer || '');
  if (!cited.length && !insufficient) return { answer: NO_SOURCE, grounded: false, sources, mode: 'uncited_suppressed' };
  return { answer, grounded: cited.length > 0 && !insufficient, insufficient, cited, sources, mode: 'grounded', llm: LLM_ENDPOINT };
}

const router = express.Router();
const wrap = (fn) => (req, res) => fn(req, res).catch((err) => {
  console.error(`[accelerator:regulatory] ${req.method} ${req.path}:`, err.message);
  res.status(err.status || 500).json({ error: err.message });
});

router.get('/matrix', wrap(async (req, res) => {
  const data = await fetchMatrix(jurOf(req.query.jurisdiction));
  res.json({ success: true, count: data.length, source: `${FQ}.jurisdiction_requirements_cited`, data });
}));
router.get('/sources', wrap(async (_req, res) => {
  const data = await fetchSources();
  res.json({ success: true, count: data.length, source: `${FQ}.regulatory_source_register`, data });
}));
router.get('/kpis', wrap(async (_req, res) => res.json({ success: true, data: await fetchKpis() })));
router.post('/ask', wrap(async (req, res) => {
  const { question, jurisdiction } = req.body || {};
  if (!question || String(question).trim().length < 3) return res.status(400).json({ error: 'question is required' });
  res.json({ success: true, data: await ask(question, jurOf(jurisdiction)) });
}));

export default router;
