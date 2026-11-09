"""Load the REAL, cited regulatory reference objects the Regulatory tab reads (ACC-DE-FRESH-REG-REFERENCE).

Fresh partner deploy path for objects that had no producer in deployable code:
  <schema>.regulatory_source_register        (69 official sources; REAL, cited)
  <schema>.jurisdiction_requirements_cited   (cited jurisdiction requirements matrix; REAL)
  <schema>.regulatory_source_files           (download log: volume_path, source_url, retrieved_at, sha256, bytes, http_status)
  <schema>.regulatory_doc_chunks             (chunks + 1024-dim databricks-bge-large-en embeddings, is_synthetic=false)
  <schema>.search_regulatory_chunks(query,k) (SQL TVF: cosine search over real chunks; every row carries source_url)
  volume <schema>.regulatory_source_docs     (downloaded official PDFs/HTML)

The register and matrix are loaded from JSONL exports (register.jsonl, matrix.jsonl) in --reference-dir
(default: <repo>/data/reference/regulatory). Documents are RE-DOWNLOADED from each official_url
(polite user agent, retries), parsed (ai_parse_document for PDF, stdlib HTML-to-text for HTML) and chunked
(~2000 chars, 200 overlap, citation header) exactly like the reference workspace. Nothing is invented:
every chunk carries the official source_url and citation from the register.

Modes:
  --export      write register.jsonl / matrix.jsonl FROM <catalog>.<schema> into --reference-dir
                (run in the reference workspace, then commit the files).
  (default)     load into <catalog>.<schema>. Existing objects are skipped unless --replace.
  --dry-run     print the plan only.   --smoke N   download+parse+chunk N sources in memory, write nothing.
  --skip-download  load register/matrix/TVF only.
  --offline     restricted-egress fallback: load chunk text + source_url from --reference-dir/chunks.jsonl
                (public-domain REAL chunks only, written by --export) instead of downloading; re-embeds in the
                target workspace. No outbound HTTP to official sites is needed.
  --max-failures N  fail loudly (exit 2) when more than N sources fail/stub on download (default 3 = the known
                WAF 403s: AZ SOS x2, CO SOS 8146). Always writes a per-source egress report (JSON) to the volume.

Prerequisites (fail fast with a clear message if missing): serving endpoint databricks-bge-large-en reachable via
ai_query; for the default (online) mode, outbound HTTPS egress to the official_url hosts in register.jsonl.

Usage: python load_regulatory_reference.py --catalog <catalog> --schema <schema> [--reference-dir DIR]
       [--export] [--replace] [--dry-run] [--smoke N] [--skip-download] [--offline] [--max-failures N]
No hardcoded catalogs or user paths. Tags: telco_project=copper-retirement.
"""
import argparse
import hashlib
import html
import json
import os
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser

IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
USER_AGENT = ("Mozilla/5.0 (compatible; CopperRetirementAccelerator/1.0; regulatory-research; "
              "+https://www.databricks.com) python-requests")
CHUNK_SIZE, CHUNK_OVERLAP = 2000, 200
EMBED_MODEL = "databricks-bge-large-en"
TAG = "ALTER {kind} {obj} SET TAGS ('telco_project' = 'copper-retirement')"
CHALLENGE_MARKERS = ("TSPD", "challenge-platform", "cf-browser-verification", "Request Rejected", "Access Denied")

TABLE_DOCS = {
    "regulatory_source_register": (
        "REAL DATA. Register of official regulatory sources for copper retirement (FCC/eCFR, 811 one-call, OSHA, PHMSA, "
        "FHWA, EPA lead cable, state PUCs). One row per source; official_url is the citation of record. telco_project=copper-retirement.",
        {"source_id": "Stable source key, e.g. FED-FCC-NCD-51D", "jurisdiction": "US or 2-letter state code",
         "level": "federal | state | industry", "authority": "Issuing authority", "topic": "Regulatory topic",
         "title": "Official title", "citation": "Official citation (rule/statute/order number)",
         "official_url": "Official source URL (citation of record)", "doc_format": "pdf | html",
         "effective_date": "Effective date when stated by the source", "is_public_domain": "True if public-domain government text",
         "key_requirements": "Key requirements summarized from the official text", "verification_status": "URL/content verification outcome",
         "http_status": "HTTP status at last verification", "last_verified": "Date the URL was last verified",
         "retrieved_via": "How the document was retrieved", "is_synthetic": "Always false: real official source"}),
    "jurisdiction_requirements_cited": (
        "REAL DATA. Jurisdiction requirements matrix for copper retirement; every row cites an official source in "
        "regulatory_source_register. Unverifiable values are flagged, never invented. telco_project=copper-retirement.",
        {"requirement_key": "Unique requirement key", "jurisdiction_code": "US or 2-letter state code",
         "jurisdiction_name": "Jurisdiction name", "jurisdiction_level": "federal | state",
         "requirement_type": "Requirement category (notice period, filing, 811, lead cable, ...)",
         "requirement_summary": "Requirement in plain language, from the cited text", "value_numeric": "Numeric value (e.g. days) when applicable",
         "value_unit": "Unit of value_numeric", "verification_status": "Verification outcome for this requirement",
         "source_id": "FK to regulatory_source_register.source_id", "citation": "Official citation",
         "official_url": "Official URL of the source", "is_synthetic": "Always false: real cited requirement",
         "citation_url": "Deep link used for the citation", "citation_url_verified_on": "Date citation_url was verified"}),
}


class _Text(HTMLParser):
    SKIP = {"script", "style", "noscript", "nav", "header", "footer", "svg"}
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "table"}

    def __init__(self):
        super().__init__(); self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP: self.skip += 1
        elif tag in self.BLOCK: self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip: self.skip -= 1
        elif tag in self.BLOCK: self.out.append("\n")

    def handle_data(self, d):
        if not self.skip: self.out.append(d)


def html_to_text(raw: bytes) -> str:
    p = _Text(); p.feed(raw.decode("utf-8", errors="replace"))
    txt = html.unescape("".join(p.out))
    txt = re.sub(r"[ \t\r\f\v]+", " ", txt)
    return re.sub(r"\n\s*\n+", "\n\n", txt).strip()


def slug(url: str) -> str:
    s = re.sub(r"^https?://", "", url or "")
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()[:80]


def chunk(text: str):
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i + CHUNK_SIZE])
        if i + CHUNK_SIZE >= len(text): break
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return out


def fetch(url, retries=3, timeout=45):
    import requests
    last = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf,*/*"},
                             timeout=timeout, allow_redirects=True)
            if r.status_code == 200: return r, None
            last = f"HTTP {r.status_code}"
            if r.status_code in (401, 403, 404, 410): return r, last
        except Exception as e:  # network errors: retry
            last = str(e)[:300]
        time.sleep(2 ** attempt)
    return None, last


def export(spark, fq, ref_dir):
    os.makedirs(ref_dir, exist_ok=True)
    for name, fname, drop in (("regulatory_source_register", "register.jsonl", ["notes"]),
                              ("jurisdiction_requirements_cited", "matrix.jsonl", ["built_by", "built_at", "register_verification_status", "notes"])):
        df = spark.table(f"{fq}.{name}")
        df = df.drop(*[c for c in drop if c in df.columns]).toPandas()
        path = os.path.join(ref_dir, fname)
        df.to_json(path, orient="records", lines=True, date_format="iso")
        print(f"EXPORT {name}: {len(df)} rows -> {path}")
    # Offline fallback corpus: REAL public-domain chunks only (excludes is_public_domain=false, e.g. IND-CGA-BP21).
    # Embeddings are NOT exported; they are recomputed with databricks-bge-large-en on load.
    cdf = spark.sql(f"""SELECT c.* EXCEPT (embedding) FROM {fq}.regulatory_doc_chunks c
        WHERE c.is_synthetic = false AND c.source_url IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM {fq}.regulatory_source_register r
                          WHERE r.source_id = c.source_id AND r.is_public_domain = false)""").toPandas()
    path = os.path.join(ref_dir, "chunks.jsonl")
    cdf.to_json(path, orient="records", lines=True, date_format="iso")
    print(f"EXPORT regulatory_doc_chunks (public-domain real): {len(cdf)} rows -> {path}")


def load_reference_table(spark, fq, catalog, schema, name, path, replace, dry):
    import pandas as pd
    if spark.catalog.tableExists(f"{catalog}.{schema}.{name}") and not replace:
        print(f"SKIP   table    {catalog}.{schema}.{name} (exists; pass --replace to rebuild)"); return
    print(f"{'PLAN ' if dry else 'CREATE'} table    {catalog}.{schema}.{name} <- {path}")
    if dry: return
    pdf = pd.read_json(path, lines=True, dtype=False)
    for c in ("effective_date", "last_verified", "citation_url_verified_on"):
        if c in pdf.columns: pdf[c] = pd.to_datetime(pdf[c], errors="coerce").dt.date
    pdf["is_synthetic"] = False
    sdf = spark.createDataFrame(pdf.astype(object).where(pdf.notna(), None))
    sdf.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fq}.{name}")
    tcomment, cols = TABLE_DOCS[name]
    spark.sql(f"COMMENT ON TABLE {fq}.{name} IS '{tcomment.replace(chr(39), chr(39)*2)}'")
    for c, cm in cols.items():
        if c in sdf.columns:
            spark.sql(f"ALTER TABLE {fq}.{name} ALTER COLUMN {c} COMMENT '{cm.replace(chr(39), chr(39)*2)}'")
    spark.sql(TAG.format(kind="TABLE", obj=f"{fq}.{name}"))
    print(f"       rows: {sdf.count()}")


def download_and_chunk(spark, catalog, schema, register_rows, write_files):
    """Returns (file_log_rows, chunk_rows). Writes files to the volume only when write_files."""
    vol = f"/Volumes/{catalog}/{schema}/regulatory_source_docs"
    files, chunks = [], []
    for r in register_rows:
        url, sid = r["official_url"], r["source_id"]
        now = datetime.now(timezone.utc)
        resp, err = fetch(url)
        rec = dict(source_id=sid, volume_path=None, source_url=url, retrieved_at=now, sha256=None, bytes=None,
                   http_status=getattr(resp, "status_code", None), content_type=None, file_format=None,
                   download_status="failed", error=err, is_synthetic=False)
        if resp is None or err:
            files.append(rec); print(f"FAIL   {sid}: {err}"); continue
        body, ctype = resp.content, resp.headers.get("Content-Type", "")
        is_pdf = "pdf" in ctype.lower() or body[:5] == b"%PDF-"
        ext = "pdf" if is_pdf else "html"
        rec.update(content_type=ctype, file_format=ext, sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
        if not is_pdf and (len(body) < 2048 or any(m.encode() in body[:20000] for m in CHALLENGE_MARKERS)):
            rec.update(download_status="stub_redirect", error=f"bot challenge / stub page ({len(body)} bytes); manual download needed")
            files.append(rec); print(f"STUB   {sid}"); continue
        path = f"{vol}/{r.get('level') or 'other'}/{r.get('jurisdiction') or 'XX'}/{sid}.{ext}"
        if write_files:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as fh: fh.write(body)
        rec.update(volume_path=path, download_status="downloaded")
        files.append(rec)
        if str(r.get("is_public_domain")).lower() == "false":
            # Copyrighted (e.g. IND-CGA-BP21): keep the file for internal reference, never chunk it into the partner RAG corpus.
            print(f"SKIPRAG {sid}: is_public_domain=false (not redistributable; cite by URL only)"); continue
        if is_pdf:
            if not write_files:
                print(f"OK     {sid} (pdf, {len(body)} bytes; parse skipped in smoke mode)"); continue
            row = spark.sql(f"""
                SELECT concat_ws('\\n\\n', transform(try_cast(p:document:elements AS ARRAY<VARIANT>), e -> try_cast(e:content AS STRING))) AS txt
                FROM (SELECT ai_parse_document(content) AS p FROM read_files('{path}', format => 'binaryFile'))""").first()
            text = (row.txt if row else "") or ""
        else:
            text = html_to_text(body)
        header = (f"Title: {r.get('title')}\nIssuing Body: {r.get('authority')}\nJurisdiction: {r.get('jurisdiction')}\n"
                  f"Citation: {r.get('citation')}\nSource URL: {url}\nTopic: {r.get('topic')}\n\n")
        pieces = chunk(text)
        for i, piece in enumerate(pieces):
            chunks.append(dict(
                chunk_id=f"{sid}__{slug(url)}_{i}", regulatory_document_id=None, chunk_index=i, total_chunks=len(pieces),
                docket_number=None, document_type=r.get("topic"), title=r.get("title"), issuing_body=r.get("authority"),
                jurisdiction_state_code=r.get("jurisdiction"), issued_date=None, document_status="official_source",
                regulatory_topic=r.get("topic"), citation_reference=r.get("citation"), carrier_name=None, notice_period_days=None,
                embedding_text=header + piece, chunk_char_length=len(piece), source_text_length=len(text),
                source_id=sid, source_url=url, jurisdiction=r.get("jurisdiction"), citation=r.get("citation"),
                is_synthetic=False, source_sha256=rec["sha256"]))
        print(f"OK     {sid}: {ext}, {len(body)} bytes, {len(pieces)} chunks")
        time.sleep(1)  # polite crawl delay
    return files, chunks


def preflight_embedding(spark):
    """Fail fast if the embedding endpoint is not reachable (prerequisite for chunks and the TVF)."""
    try:
        spark.sql(f"SELECT ai_query('{EMBED_MODEL}', 'preflight', returnType => 'ARRAY<FLOAT>') AS v").first()
        print(f"OK     preflight: embedding endpoint {EMBED_MODEL} reachable")
    except Exception as e:
        raise SystemExit(f"PREREQ FAILED: serving endpoint {EMBED_MODEL} not reachable via ai_query ({str(e)[:300]}). "
                         "Enable Foundation Model APIs / grant access, then re-run. Regulatory tab citations depend on it.")


def write_egress_report(catalog, schema, files, chunks, max_failures):
    """Per-source egress report; exit 2 when failures exceed max_failures or no chunks were produced."""
    failed = [f for f in files if f["download_status"] != "downloaded"]
    print("\nEGRESS REPORT (source_id | download_status | http_status | error | url)")
    for f in failed:
        print(f"  {f['source_id']} | {f['download_status']} | {f['http_status']} | {f['error']} | {f['source_url']}")
    report = dict(generated_at=datetime.now(timezone.utc).isoformat(), sources=len(files), downloaded=len(files) - len(failed),
                  failed_or_stub=len(failed), chunks=len(chunks), max_failures=max_failures,
                  failures=[{k: f[k] for k in ("source_id", "download_status", "http_status", "error", "source_url")} for f in failed])
    path = f"/Volumes/{catalog}/{schema}/regulatory_source_docs/_egress_report_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    try:
        with open(path, "w") as fh: json.dump(report, fh, indent=2, default=str)
        print(f"REPORT {path}")
    except OSError as e:
        print(f"WARN   could not write egress report to volume: {e}")
    if not chunks or len(failed) > max_failures:
        print(f"\nFAIL LOUD: {len(failed)} of {len(files)} sources failed (allowed {max_failures}); chunks={len(chunks)}. "
              "The Regulatory tab will answer WITHOUT citations. Fix egress to the hosts above, or re-run with --offline "
              "(uses --reference-dir/chunks.jsonl). See PARTNER-PLAYBOOK prerequisites.")
        raise SystemExit(2)


def load_offline_chunks(spark, fq, ref_dir):
    """Restricted-egress fallback: chunk text + source_url from chunks.jsonl; re-embed in this workspace."""
    import pandas as pd
    path = os.path.join(ref_dir, "chunks.jsonl")
    if not os.path.exists(path):
        raise SystemExit(f"--offline needs {path} (create it with --export in the reference workspace and commit it).")
    pdf = pd.read_json(path, lines=True, dtype=False)
    if pdf.empty:
        raise SystemExit(f"--offline: {path} has 0 rows")
    spark.sql(CHUNKS_DDL.format(fq=fq))
    spark.sql(TAG.format(kind="TABLE", obj=f"{fq}.regulatory_doc_chunks"))
    target = spark.table(f"{fq}.regulatory_doc_chunks").drop("embedding").schema
    pdf = pdf[[c for c in target.fieldNames() if c in pdf.columns]]
    for c in target.fieldNames():
        if c not in pdf.columns: pdf[c] = None
    pdf["is_synthetic"] = False
    cdf = spark.createDataFrame(pdf[target.fieldNames()].astype(object).where(pdf.notna(), None), schema=target)
    cdf.createOrReplaceTempView("_offline_reg_chunks")
    spark.sql(f"DELETE FROM {fq}.regulatory_doc_chunks WHERE is_synthetic = false")
    spark.sql(f"""INSERT INTO {fq}.regulatory_doc_chunks BY NAME
                  SELECT o.*, ai_query('{EMBED_MODEL}', o.embedding_text, returnType => 'ARRAY<FLOAT>') AS embedding
                  FROM _offline_reg_chunks o
                  WHERE o.source_url IS NOT NULL AND NOT EXISTS (SELECT 1 FROM {fq}.regulatory_source_register r
                        WHERE r.source_id = o.source_id AND r.is_public_domain = false)""")
    n = spark.sql(f"SELECT count(*) n FROM {fq}.regulatory_doc_chunks WHERE is_synthetic = false").first().n
    print(f"OFFLINE loaded {n} real chunks from {path}")
    if n == 0:
        raise SystemExit("FAIL LOUD: --offline produced 0 real chunks; Regulatory tab would have no citations.")


CHUNKS_DDL = """
CREATE TABLE IF NOT EXISTS {fq}.regulatory_doc_chunks (
  chunk_id STRING NOT NULL COMMENT 'Primary key: <source_id>__<url-slug>_<chunk_index>',
  regulatory_document_id BIGINT COMMENT 'Legacy synthetic document id (NULL for real sources)',
  chunk_index INT COMMENT 'Zero-based chunk position within the source document',
  total_chunks INT COMMENT 'Number of chunks for the source document',
  docket_number STRING COMMENT 'Docket number when applicable', document_type STRING COMMENT 'Document type / topic',
  title STRING COMMENT 'Official title', issuing_body STRING COMMENT 'Issuing authority',
  jurisdiction_state_code STRING COMMENT 'US or 2-letter state code', issued_date STRING COMMENT 'Issue date when stated',
  document_status STRING COMMENT 'official_source for real documents', regulatory_topic STRING COMMENT 'Regulatory topic',
  citation_reference STRING COMMENT 'Official citation', carrier_name STRING COMMENT 'Carrier (legacy synthetic only)',
  notice_period_days INT COMMENT 'Notice period (legacy synthetic only)',
  embedding_text STRING COMMENT 'Citation header + chunk text that is embedded and returned to the RAG app',
  chunk_char_length INT COMMENT 'Characters in the chunk body', source_text_length INT COMMENT 'Characters in the full parsed source',
  embedding ARRAY<FLOAT> COMMENT '1024-dim databricks-bge-large-en embedding of embedding_text',
  source_id STRING COMMENT 'FK to regulatory_source_register.source_id', source_url STRING COMMENT 'Official source URL (citation of record)',
  jurisdiction STRING COMMENT 'US or 2-letter state code', citation STRING COMMENT 'Official citation',
  is_synthetic BOOLEAN COMMENT 'False for real official sources; true for legacy synthetic chunks',
  source_sha256 STRING COMMENT 'SHA-256 of the downloaded source file')
COMMENT 'Regulatory document chunks for RAG. Real chunks (is_synthetic=false) come from official sources in regulatory_source_register and always carry source_url. telco_project=copper-retirement.'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
"""

TVF_SQL = """
CREATE OR REPLACE FUNCTION {fq}.search_regulatory_chunks(query STRING, k INT DEFAULT 5)
RETURNS TABLE (chunk_id STRING, source_id STRING, title STRING, jurisdiction STRING, citation STRING, source_url STRING, score DOUBLE, chunk_text STRING)
COMMENT 'Semantic search over REAL regulatory chunks (is_synthetic = false) in regulatory_doc_chunks. Partner-redistribution guard: excludes sources with regulatory_source_register.is_public_domain = false (e.g. IND-CGA-BP21). Embeds the query with databricks-bge-large-en and ranks by cosine similarity. Every row carries the official source_url for citation. telco_project=copper-retirement.'
RETURN
  WITH q AS (SELECT ai_query('databricks-bge-large-en', query, returnType => 'ARRAY<FLOAT>') AS qv),
  scored AS (
    SELECT c.chunk_id, c.source_id, c.title, c.jurisdiction, c.citation, c.source_url, c.embedding_text,
      aggregate(zip_with(c.embedding, q.qv, (a, b) -> CAST(a AS DOUBLE) * b), 0D, (acc, x) -> acc + x)
        / (sqrt(aggregate(c.embedding, 0D, (acc, x) -> acc + CAST(x AS DOUBLE) * x)) * sqrt(aggregate(q.qv, 0D, (acc, x) -> acc + CAST(x AS DOUBLE) * x))) AS score
    FROM {fq}.regulatory_doc_chunks c CROSS JOIN q
    WHERE c.is_synthetic = false AND c.embedding IS NOT NULL AND c.source_url IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM {fq}.regulatory_source_register r WHERE r.source_id = c.source_id AND r.is_public_domain = false)
  ),
  ranked AS (SELECT *, row_number() OVER (ORDER BY score DESC) AS rn FROM scored)
  SELECT chunk_id, source_id, title, jurisdiction, citation, source_url, score, embedding_text AS chunk_text
  FROM ranked WHERE rn <= k
"""


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", default="copper_retirement")
    p.add_argument("--reference-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "reference", "regulatory"))
    p.add_argument("--export", action="store_true")
    p.add_argument("--replace", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--skip-download", action="store_true")
    p.add_argument("--smoke", type=int, default=0)
    p.add_argument("--offline", action="store_true")
    p.add_argument("--max-failures", type=int, default=3)
    a = p.parse_args()
    for v in (a.catalog, a.schema):
        if not IDENT.match(v): raise SystemExit(f"Invalid identifier: {v!r}")

    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    fq = f"`{a.catalog}`.`{a.schema}`"
    if a.export:
        export(spark, fq, a.reference_dir); return

    reg_path, mat_path = os.path.join(a.reference_dir, "register.jsonl"), os.path.join(a.reference_dir, "matrix.jsonl")
    if a.smoke:
        import pandas as pd
        rows = pd.read_json(reg_path, lines=True, dtype=False).head(a.smoke).to_dict("records")
        files, chunks = download_and_chunk(spark, a.catalog, a.schema, rows, write_files=False)
        print(f"SMOKE  files={len(files)} downloaded={sum(f['download_status'] == 'downloaded' for f in files)} chunks={len(chunks)}"); return

    print(f"{'PLAN ' if a.dry_run else 'CREATE'} volume   {a.catalog}.{a.schema}.regulatory_source_docs (if missing)")
    if not a.dry_run:
        spark.sql(f"CREATE VOLUME IF NOT EXISTS {fq}.regulatory_source_docs COMMENT 'Official regulatory source documents (PDF/HTML) downloaded from regulatory_source_register.official_url. REAL DATA.'")
        spark.sql(TAG.format(kind="VOLUME", obj=f"{fq}.regulatory_source_docs"))

    load_reference_table(spark, fq, a.catalog, a.schema, "regulatory_source_register", reg_path, a.replace, a.dry_run)
    load_reference_table(spark, fq, a.catalog, a.schema, "jurisdiction_requirements_cited", mat_path, a.replace, a.dry_run)

    if not a.dry_run and not a.skip_download:
        preflight_embedding(spark)
    has_real = (spark.catalog.tableExists(f"{a.catalog}.{a.schema}.regulatory_doc_chunks") and
                spark.sql(f"SELECT count(*) n FROM {fq}.regulatory_doc_chunks WHERE is_synthetic = false").first().n > 0)
    if a.offline and not a.dry_run and (a.replace or not has_real):
        load_offline_chunks(spark, fq, a.reference_dir)
    elif a.skip_download or a.dry_run or (has_real and not a.replace):
        print(f"SKIP   download/parse/chunk ({'real chunks exist; pass --replace' if has_real else 'flag/dry-run'})")
    else:
        rows = [r.asDict() for r in spark.table(f"{fq}.regulatory_source_register").where("official_url IS NOT NULL").collect()]
        files, chunks = download_and_chunk(spark, a.catalog, a.schema, rows, write_files=True)
        fdf = spark.createDataFrame(files, schema="source_id string, volume_path string, source_url string, retrieved_at timestamp, sha256 string, bytes bigint, http_status int, content_type string, file_format string, download_status string, error string, is_synthetic boolean")
        fdf.write.mode("overwrite").saveAsTable(f"{fq}.regulatory_source_files")
        spark.sql(f"COMMENT ON TABLE {fq}.regulatory_source_files IS 'REAL DATA. Download log for official regulatory sources: one row per source_url attempt (volume_path, retrieved_at, sha256, bytes, http_status, download_status). telco_project=copper-retirement.'")
        spark.sql(TAG.format(kind="TABLE", obj=f"{fq}.regulatory_source_files"))
        spark.sql(CHUNKS_DDL.format(fq=fq))
        spark.sql(TAG.format(kind="TABLE", obj=f"{fq}.regulatory_doc_chunks"))
        if chunks:
            cdf = spark.createDataFrame(chunks, schema=spark.table(f"{fq}.regulatory_doc_chunks").drop("embedding").schema)
            cdf.createOrReplaceTempView("_new_reg_chunks")
            spark.sql(f"DELETE FROM {fq}.regulatory_doc_chunks WHERE is_synthetic = false")
            spark.sql(f"""INSERT INTO {fq}.regulatory_doc_chunks BY NAME
                          SELECT *, ai_query('{EMBED_MODEL}', embedding_text, returnType => 'ARRAY<FLOAT>') AS embedding FROM _new_reg_chunks""")
        failed = [f["source_id"] for f in files if f["download_status"] != "downloaded"]
        print(f"files={len(files)} failed_or_stub={len(failed)} {failed} chunks={len(chunks)}")
        # TVF is created before exiting so the failure is visible, then fail loudly.
        if not spark.catalog.functionExists(f"{a.catalog}.{a.schema}.search_regulatory_chunks"):
            spark.sql(TVF_SQL.format(fq=fq))
        write_egress_report(a.catalog, a.schema, files, chunks, a.max_failures)

    print(f"{'PLAN ' if a.dry_run else 'CREATE'} function {a.catalog}.{a.schema}.search_regulatory_chunks")
    if not a.dry_run:
        if not spark.catalog.tableExists(f"{a.catalog}.{a.schema}.regulatory_doc_chunks"):
            spark.sql(CHUNKS_DDL.format(fq=fq))
        if a.replace or not spark.catalog.functionExists(f"{a.catalog}.{a.schema}.search_regulatory_chunks"):
            spark.sql(TVF_SQL.format(fq=fq))
        else:
            print("SKIP   function search_regulatory_chunks (exists)")


if __name__ == "__main__":
    main()
