/**
 * ragChat.ts
 * Client-side API helper for the P6-REG RAG chat endpoint.
 * Calls /api/agent/chat which performs:
 *   Vector Search retrieval → context formatting → FMAPI generation → structured response
 *
 * Falls back to corpus keyword search if RAG endpoint is unavailable.
 */
import { searchCorpus, documentToCitation, composeAnswer } from './corpus';
import type { Citation } from '../mock/mockData';

export interface RAGSource {
  title: string;
  docket_number: string | null;
  citation_reference: string | null;
  jurisdiction: string | null;
  notice_period_days: string | null;
  issuing_body: string | null;
  issued_date: string | null;
  document_type: string | null;
  score: number | null;
  excerpt: string;
}

export interface RAGResponse {
  answer: string;
  sources: RAGSource[];
  num_sources: number;
  model: string;
  source_type: 'rag' | 'corpus' | 'mock' | 'error';
  citations: Citation[];
}

/**
 * Convert a RAG source to a Citation for the chat UI.
 */
function sourceToCitation(source: RAGSource, index: number): Citation {
  return {
    id: index + 1,
    document_title: source.title || 'Untitled',
    paragraph_ref: source.citation_reference || source.docket_number || source.document_type || '',
    effective_date: source.issued_date || 'N/A',
    jurisdiction: source.jurisdiction || 'Federal',
    excerpt: source.excerpt || '',
    confidence: (source.score && source.score > 0.7) ? 'high' : (source.score && source.score > 0.55) ? 'medium' : 'low',
    doc_id: source.docket_number || source.title || '',
  };
}

/**
 * Send a question to the RAG chat endpoint.
 * Falls back to corpus keyword search if the RAG endpoint fails.
 */
export async function askRegulatory(
  question: string,
  jurisdiction?: string
): Promise<RAGResponse> {
  try {
    // Try RAG endpoint first
    const resp = await fetch('/api/agent/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, jurisdiction }),
    });

    if (resp.ok) {
      const data = await resp.json();
      if (data.answer) {
        const citations = (data.sources || []).slice(0, 6).map(
          (s: RAGSource, i: number) => sourceToCitation(s, i)
        );
        return {
          answer: data.answer,
          sources: data.sources || [],
          num_sources: data.num_sources || 0,
          model: data.model || 'unknown',
          source_type: 'rag',
          citations,
        };
      }
    }

    // RAG returned no answer — fall through to corpus search
    console.warn('[ragChat] RAG endpoint returned no answer, falling back to corpus search');
  } catch (err) {
    console.warn('[ragChat] RAG endpoint unavailable, falling back to corpus search:', err);
  }

  // Fallback: corpus keyword search
  try {
    const docs = await searchCorpus(question, jurisdiction);
    if (docs.length > 0) {
      const answer = composeAnswer(docs, question);
      const citations = docs.slice(0, 4).map((doc, i) => documentToCitation(doc, i));
      return {
        answer,
        sources: [],
        num_sources: docs.length,
        model: 'keyword-search',
        source_type: 'corpus',
        citations,
      };
    }
  } catch {
    console.warn('[ragChat] Corpus search also failed');
  }

  // Both failed
  return {
    answer: `No matching regulatory documents found for that query.\n\nTry:\n\u2022 Specific regulatory terms: "Section 214", "discontinuance", "notice requirements"\n\u2022 A state name: CO, WA, OR, AZ, MN, ID\n\u2022 A topic: "911 coordination", "copper retirement", "PUC filing"\n\nJurisdiction context: ${jurisdiction === 'all' || !jurisdiction ? 'All states' : jurisdiction}.`,
    sources: [],
    num_sources: 0,
    model: 'none',
    source_type: 'error',
    citations: [],
  };
}
