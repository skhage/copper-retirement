# Databricks notebook source
# DBTITLE 1,P6 Regulatory RAG Chain — Copper Retirement
# MAGIC %md
# MAGIC # P6 Regulatory RAG Chain — Copper Retirement
# MAGIC
# MAGIC Retrieval-Augmented Generation pipeline for regulatory Q&A on copper retirement.
# MAGIC
# MAGIC **Architecture:** Vector Search (similarity retrieval) → Context formatting → Foundation Model API (generation) → Structured response with citations
# MAGIC
# MAGIC **Components:**
# MAGIC - **Index:** `cdm_tmforum.copper_retirement.regulatory_doc_chunks_vs_index` (528 chunks, BGE-large-en embeddings)
# MAGIC - **Endpoint:** `cmeg-demos-vs` (Databricks Vector Search)
# MAGIC - **LLM:** `databricks-meta-llama-3-3-70b-instruct` (Foundation Model API)
# MAGIC - **Source data:** FCC orders, state PUC filings, carrier guides, Section 214 discontinuance docs
# MAGIC
# MAGIC **Usage:**
# MAGIC ```python
# MAGIC result = regulatory_rag_query("What notice periods apply to copper retirement in Colorado?")
# MAGIC print(result["answer"])
# MAGIC print(result["citations"])
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Configuration
# ---------- Configuration ----------

# Vector Search
VS_INDEX_NAME = "cdm_tmforum.copper_retirement.regulatory_doc_chunks_vs_index"
VS_ENDPOINT_NAME = "cmeg-demos-vs"

# Foundation Model API
LLM_ENDPOINT = "databricks-meta-llama-3-3-70b-instruct"
LLM_MAX_TOKENS = 2048
LLM_TEMPERATURE = 0.1  # Low temperature for factual regulatory responses

# Retrieval settings
TOP_K = 8                # Number of chunks to retrieve
SCORE_THRESHOLD = 0.55   # Minimum similarity score to include

# Metadata columns to retrieve alongside text
RETRIEVAL_COLUMNS = [
    "chunk_id", "title", "embedding_text", "docket_number",
    "regulatory_topic", "jurisdiction_state_code", "citation_reference",
    "notice_period_days", "issuing_body", "issued_date", "document_status",
    "document_type"
]

# COMMAND ----------

# DBTITLE 1,Initialize clients
from databricks.sdk import WorkspaceClient
from openai import OpenAI
import json, textwrap
from typing import Optional

w = WorkspaceClient()

# Token for FMAPI
_api_token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

# OpenAI-compatible client pointed at Databricks FMAPI
llm_client = OpenAI(
    api_key=_api_token,
    base_url=f"{w.config.host}/serving-endpoints"
)

print(f"\u2705 LLM client initialized: {LLM_ENDPOINT}")
print(f"\u2705 VS index: {VS_INDEX_NAME} on {VS_ENDPOINT_NAME}")

# COMMAND ----------

# DBTITLE 1,retrieve_regulatory_chunks — Vector Search retrieval
def retrieve_regulatory_chunks(
    query: str,
    top_k: int = TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    filters: Optional[dict] = None,
) -> list[dict]:
    """
    Query the regulatory document VS index and return ranked chunks
    with metadata. Optional filters narrow by jurisdiction, topic, etc.

    Parameters
    ----------
    query : str
        Natural-language regulatory question.
    top_k : int
        Max chunks to retrieve.
    score_threshold : float
        Minimum similarity score (0-1) to include a chunk.
    filters : dict, optional
        Column-level filters, e.g. {"jurisdiction_state_code": "CO"}.
        Passed directly to VS query_index filters_json.

    Returns
    -------
    list[dict]
        Ranked list of chunk dicts with keys: chunk_id, title,
        embedding_text, score, docket_number, citation_reference,
        jurisdiction_state_code, regulatory_topic, notice_period_days,
        issuing_body, issued_date, document_status, document_type.
    """
    kwargs = dict(
        index_name=VS_INDEX_NAME,
        columns=RETRIEVAL_COLUMNS,
        query_text=query,
        num_results=top_k,
    )
    if filters:
        kwargs["filters_json"] = json.dumps(filters)

    vs_response = w.vector_search_indexes.query_index(**kwargs)

    # Parse into clean dicts
    col_names = [c.name for c in vs_response.manifest.columns]
    chunks = []
    for row in vs_response.result.data_array:
        chunk = dict(zip(col_names, row))
        if chunk.get("score", 0) >= score_threshold:
            chunks.append(chunk)

    return chunks

# Quick test
_test = retrieve_regulatory_chunks("FCC copper retirement notice requirements", top_k=3)
print(f"Retrieved {len(_test)} chunks. Top score: {_test[0]['score']:.4f}" if _test else "No results")

# COMMAND ----------

# DBTITLE 1,format_context — Build LLM context from retrieved chunks
def format_context(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a structured context string for the LLM.
    Each chunk is wrapped with source metadata for citation traceability.
    """
    if not chunks:
        return "No relevant regulatory documents were found."

    sections = []
    for i, c in enumerate(chunks, 1):
        meta_parts = []
        if c.get("docket_number"):
            meta_parts.append(f"Docket: {c['docket_number']}")
        if c.get("citation_reference"):
            meta_parts.append(f"Citation: {c['citation_reference']}")
        if c.get("jurisdiction_state_code"):
            meta_parts.append(f"Jurisdiction: {c['jurisdiction_state_code']}")
        if c.get("issuing_body"):
            meta_parts.append(f"Issuing Body: {c['issuing_body']}")
        if c.get("issued_date"):
            meta_parts.append(f"Date: {c['issued_date']}")
        if c.get("document_status"):
            meta_parts.append(f"Status: {c['document_status']}")
        if c.get("notice_period_days") is not None:
            meta_parts.append(f"Notice Period: {int(c['notice_period_days'])} days")

        meta_line = " | ".join(meta_parts)
        section = (
            f"[Source {i}: {c.get('title', 'Unknown')}]\n"
            f"  {meta_line}\n"
            f"  {c.get('embedding_text', '')}"
        )
        sections.append(section)

    return "\n\n".join(sections)

# Preview formatted context
_ctx = format_context(_test)
print(_ctx[:600])

# COMMAND ----------

# DBTITLE 1,SYSTEM_PROMPT — Regulatory Q&A system prompt
SYSTEM_PROMPT = """You are a regulatory compliance assistant for LakeLink Fiber, a telecommunications carrier retiring legacy copper infrastructure and migrating customers to fiber.

Your role is to answer questions about regulatory requirements for copper line retirement, based ONLY on the source documents provided in the context. You must:

1. **Cite sources** — Reference specific docket numbers, CFR citations, and document titles when making claims.
2. **Distinguish federal vs. state** — FCC rules (47 U.S.C. § 214, 47 C.F.R. §§ 63.71, 63.602) set the floor; state PUCs may impose additional requirements.
3. **Flag notice periods** — Always highlight applicable notice periods (e.g., 180-day FCC, 90-day residential, state-specific).
4. **Be precise** — Use exact regulatory language when available. Do not paraphrase in ways that change legal meaning.
5. **Acknowledge gaps** — If the provided context does not contain enough information to answer, say so clearly rather than speculating.
6. **Legacy states context** — LakeLink operates in CO, MN, WA, OR, ID, AZ. Flag when state-specific rules apply to these states.

Format your response as:
- **Answer**: Direct answer to the question
- **Key Requirements**: Bulleted list of specific regulatory requirements
- **Citations**: List of source documents referenced
- **Caveats**: Any limitations or uncertainties in the answer"""

# COMMAND ----------

# DBTITLE 1,generate_answer — LLM generation with FMAPI
def generate_answer(query: str, context: str) -> str:
    """
    Call the Foundation Model API with the regulatory context and user query.
    Returns the LLM's structured response.
    """
    user_message = f"""Based on the following regulatory source documents, answer the question.

--- REGULATORY SOURCES ---
{context}
--- END SOURCES ---

Question: {query}"""

    response = llm_client.chat.completions.create(
        model=LLM_ENDPOINT,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=LLM_MAX_TOKENS,
        temperature=LLM_TEMPERATURE,
    )
    return response.choices[0].message.content

# COMMAND ----------

# DBTITLE 1,regulatory_rag_query — Main RAG chain entry point
def regulatory_rag_query(
    question: str,
    top_k: int = TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    filters: Optional[dict] = None,
) -> dict:
    """
    End-to-end RAG query for regulatory copper retirement questions.

    Parameters
    ----------
    question : str
        Natural-language regulatory question.
    top_k : int
        Number of source chunks to retrieve.
    score_threshold : float
        Minimum similarity score for chunk inclusion.
    filters : dict, optional
        VS metadata filters (e.g., {"jurisdiction_state_code": "CO"}).

    Returns
    -------
    dict with keys:
        - question: original query
        - answer: LLM-generated response
        - sources: list of source chunk metadata (title, docket, citation, score)
        - num_sources: count of retrieved chunks
        - model: LLM model used
    """
    # Step 1: Retrieve
    chunks = retrieve_regulatory_chunks(
        query=question,
        top_k=top_k,
        score_threshold=score_threshold,
        filters=filters,
    )

    # Step 2: Format context
    context = format_context(chunks)

    # Step 3: Generate
    answer = generate_answer(question, context)

    # Step 4: Package response
    sources = [
        {
            "title": c.get("title"),
            "docket_number": c.get("docket_number"),
            "citation_reference": c.get("citation_reference"),
            "jurisdiction": c.get("jurisdiction_state_code"),
            "notice_period_days": c.get("notice_period_days"),
            "score": round(c.get("score", 0), 4),
        }
        for c in chunks
    ]

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "num_sources": len(sources),
        "model": LLM_ENDPOINT,
    }

# COMMAND ----------

# DBTITLE 1,Test — Copper retirement notice requirements
# ---- Test: General FCC notice requirements ----
result = regulatory_rag_query(
    "What are the FCC notice requirements and timelines for retiring copper telephone lines?"
)

print(f"Question: {result['question']}")
print(f"Sources retrieved: {result['num_sources']}")
print(f"Model: {result['model']}")
print("\n" + "=" * 80)
print(result['answer'])
print("\n" + "=" * 80)
print("\nSource documents:")
for s in result['sources']:
    print(f"  [{s['score']}] {s['title']} — {s['docket_number']} ({s['citation_reference']})")

# COMMAND ----------

# DBTITLE 1,Test — State-specific query (Colorado)
# ---- Test: Colorado-specific requirements ----
result_co = regulatory_rag_query(
    "What are Colorado's specific requirements for copper retirement beyond federal FCC rules?",
    filters={"jurisdiction_state_code": "CO"}
)

print(f"Question: {result_co['question']}")
print(f"Sources retrieved: {result_co['num_sources']}")
print("\n" + "=" * 80)
print(result_co['answer'])
print("\n" + "=" * 80)
print("\nSource documents:")
for s in result_co['sources']:
    print(f"  [{s['score']}] {s['title']} — {s['docket_number']} (Notice: {s['notice_period_days']} days)")

# COMMAND ----------

# DBTITLE 1,Test — Section 214 discontinuance process
# ---- Test: Section 214 discontinuance process ----
result_214 = regulatory_rag_query(
    "What is the Section 214 discontinuance process and when does it apply to copper retirement?"
)

print(f"Question: {result_214['question']}")
print(f"Sources retrieved: {result_214['num_sources']}")
print("\n" + "=" * 80)
print(result_214['answer'])