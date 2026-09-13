/**
 * corpus.ts
 * Client-side API helpers for the live fcc_regulatory_document corpus.
 * Calls server endpoints that query via Databricks SQL Statement API.
 * Falls back gracefully if server endpoints are unavailable.
 */

export interface CorpusDocument {
  document_id: string;
  title: string;
  document_type: string;
  issuing_body: string;
  jurisdiction_state_code: string;
  effective_date: string;
  regulatory_topic: string;
  summary_text: string;
  excerpt?: string;
  citation_reference: string;
  docket_number: string;
  notice_period_days?: string;
  word_count?: string;
  page_count?: string;
  document_status?: string;
}

export interface CorpusKPIs {
  jurisdictions_covered: string;
  total_documents: string;
  document_types: string;
  federal_docs: string;
  state_docs: string;
  total_words: string;
}

/**
 * Search the regulatory corpus by natural-language query.
 * Returns matching documents ranked by relevance.
 */
export async function searchCorpus(
  query: string,
  jurisdiction?: string
): Promise<CorpusDocument[]> {
  const resp = await fetch('/api/corpus/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, jurisdiction }),
  });
  if (!resp.ok) throw new Error(`Search failed: ${resp.statusText}`);
  const data = await resp.json();
  return data.documents || [];
}

/**
 * List documents from the live corpus with optional filters.
 */
export async function listDocuments(params: {
  jurisdiction?: string;
  document_type?: string;
  search?: string;
  limit?: number;
}): Promise<CorpusDocument[]> {
  const qs = new URLSearchParams();
  if (params.jurisdiction) qs.set('jurisdiction', params.jurisdiction);
  if (params.document_type) qs.set('document_type', params.document_type);
  if (params.search) qs.set('search', params.search);
  if (params.limit) qs.set('limit', String(params.limit));

  const resp = await fetch(`/api/corpus/documents?${qs}`);
  if (!resp.ok) throw new Error(`Document list failed: ${resp.statusText}`);
  const data = await resp.json();
  return data.documents || [];
}

/**
 * Fetch KPIs computed from the live corpus.
 */
export async function fetchKPIs(
  jurisdiction?: string
): Promise<CorpusKPIs | null> {
  const qs = jurisdiction && jurisdiction !== 'all'
    ? `?jurisdiction=${encodeURIComponent(jurisdiction)}`
    : '';
  const resp = await fetch(`/api/corpus/kpis${qs}`);
  if (!resp.ok) throw new Error(`KPI fetch failed: ${resp.statusText}`);
  const data = await resp.json();
  return data.kpis || null;
}

/**
 * Map a CorpusDocument to a Citation object for the chat UI.
 */
export function documentToCitation(
  doc: CorpusDocument,
  index: number
): {
  id: number;
  document_title: string;
  paragraph_ref: string;
  effective_date: string;
  jurisdiction: string;
  excerpt: string;
  confidence: 'high' | 'medium' | 'low';
  doc_id: string;
} {
  return {
    id: index + 1,
    document_title: doc.title,
    paragraph_ref: doc.citation_reference || doc.docket_number || doc.document_type,
    effective_date: doc.effective_date || 'N/A',
    jurisdiction: doc.jurisdiction_state_code || 'Federal',
    excerpt: doc.excerpt || doc.summary_text || '',
    confidence: doc.word_count && parseInt(doc.word_count) > 1000 ? 'high' : 'medium',
    doc_id: String(doc.document_id),
  };
}

/**
 * Compose a chat answer from matching corpus documents.
 * This is a retrieval-only approach until P6-REG model serving is deployed.
 */
export function composeAnswer(docs: CorpusDocument[], query: string): string {
  if (docs.length === 0) {
    return 'No matching regulatory documents found in the corpus for that query. Try rephrasing with specific terms like "Section 214", "copper retirement", "notice requirements", or a state name.';
  }

  const topDocs = docs.slice(0, 4);
  const parts: string[] = [];

  parts.push(
    `Found ${docs.length} relevant document${docs.length > 1 ? 's' : ''} in the regulatory corpus. Here are the key findings:\n`
  );

  topDocs.forEach((doc, i) => {
    const summary = doc.summary_text
      ? doc.summary_text.length > 300
        ? doc.summary_text.slice(0, 300) + '...'
        : doc.summary_text
      : 'No summary available.';
    parts.push(
      `[${i + 1}] ${doc.title} (${doc.jurisdiction_state_code || 'Federal'}, ${doc.effective_date || 'N/A'}):\n${summary}\n`
    );
  });

  if (docs.length > 4) {
    parts.push(
      `\n...and ${docs.length - 4} more matching documents. Use the Documents tab to browse the full corpus.`
    );
  }

  return parts.join('\n');
}
