/**
 * DocumentBrowser.tsx
 * Screen 4 — Document Browser.
 * Fetches documents from the live fcc_regulatory_document corpus.
 * Falls back to mock data if the API is unavailable.
 */
import { useState, useEffect, useCallback } from 'react';
import { listDocuments } from '../api/corpus';
import type { CorpusDocument } from '../api/corpus';
import { getMockDocuments } from '../mock/mockData';
import type { RegDocument } from '../mock/mockData';

interface DocumentBrowserProps {
  jurisdictionFilter: string;
  highlightDocId: string | null;
}

const DOC_TYPE_LABELS: Record<string, string> = {
  fcc_order: 'FCC Order',
  fcc_guidance: 'FCC Guidance',
  fcc_public_notice: 'FCC Public Notice',
  state_puc_docket: 'State PUC Docket',
  state_governor_notice: 'State Gov Notice',
  carrier_section_214_filing: 'Section 214 Filing',
  carrier_retirement_notice: 'Retirement Notice',
  compliance_checklist: 'Compliance Checklist',
  notice_template: 'Notice Template',
  guidance: 'Guidance',
  legislative: 'Legislative',
  puc_docket: 'PUC Docket',
};

/** Unified document shape for the UI */
interface DisplayDoc {
  doc_id: string;
  title: string;
  document_type: string;
  issuing_body: string;
  jurisdiction: string;
  effective_date: string;
  summary: string;
  regulatory_topic?: string;
  citation_reference?: string;
  docket_number?: string;
  notice_period_days?: string;
  word_count?: string;
  isLive: boolean;
}

function corpusToDisplay(doc: CorpusDocument): DisplayDoc {
  return {
    doc_id: String(doc.document_id),
    title: doc.title,
    document_type: doc.document_type,
    issuing_body: doc.issuing_body,
    jurisdiction: doc.jurisdiction_state_code || 'Federal',
    effective_date: doc.effective_date || '',
    summary: doc.summary_text || '',
    regulatory_topic: doc.regulatory_topic,
    citation_reference: doc.citation_reference,
    docket_number: doc.docket_number,
    notice_period_days: doc.notice_period_days,
    word_count: doc.word_count,
    isLive: true,
  };
}

function mockToDisplay(doc: RegDocument): DisplayDoc {
  return {
    doc_id: doc.doc_id,
    title: doc.title,
    document_type: doc.document_type,
    issuing_body: doc.issuing_body,
    jurisdiction: doc.jurisdiction,
    effective_date: doc.effective_date,
    summary: doc.summary,
    isLive: false,
  };
}

export function DocumentBrowser({ jurisdictionFilter, highlightDocId }: DocumentBrowserProps) {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [selectedDoc, setSelectedDoc] = useState<DisplayDoc | null>(null);
  const [docs, setDocs] = useState<DisplayDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [isLive, setIsLive] = useState(false);

  const fetchDocs = useCallback(async () => {
    setLoading(true);
    try {
      const results = await listDocuments({
        jurisdiction: jurisdictionFilter !== 'all' ? jurisdictionFilter : undefined,
        document_type: typeFilter !== 'all' ? typeFilter : undefined,
        search: search || undefined,
      });
      if (results.length > 0) {
        setDocs(results.map(corpusToDisplay));
        setIsLive(true);
      } else {
        // Try mock fallback if API returned empty (might be filter mismatch)
        const mockDocs = getMockDocuments({
          jurisdiction: jurisdictionFilter !== 'all' ? jurisdictionFilter : undefined,
          document_type: typeFilter !== 'all' ? typeFilter : undefined,
          search: search || undefined,
        });
        setDocs(mockDocs.map(mockToDisplay));
        setIsLive(false);
      }
    } catch {
      // API unavailable — use mock data
      const mockDocs = getMockDocuments({
        jurisdiction: jurisdictionFilter !== 'all' ? jurisdictionFilter : undefined,
        document_type: typeFilter !== 'all' ? typeFilter : undefined,
        search: search || undefined,
      });
      setDocs(mockDocs.map(mockToDisplay));
      setIsLive(false);
    }
    setLoading(false);
  }, [jurisdictionFilter, typeFilter, search]);

  // Debounce search to avoid hammering the API
  useEffect(() => {
    const timer = setTimeout(fetchDocs, 300);
    return () => clearTimeout(timer);
  }, [fetchDocs]);

  // Auto-select highlighted document (from citation click)
  useEffect(() => {
    if (highlightDocId) {
      const doc = docs.find((d) => d.doc_id === highlightDocId);
      if (doc) setSelectedDoc(doc);
    }
  }, [highlightDocId, docs]);

  return (
    <div className="flex flex-col lg:flex-row gap-4 lg:h-[calc(100vh-280px)]">
      {/* Document list */}
      <div className="w-full lg:w-1/2 space-y-3">
        {/* Search + filters */}
        <div className="flex gap-2">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search documents..."
            className="flex-1 border rounded px-3 py-1.5 text-sm bg-background"
          />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="border rounded px-2 py-1 text-sm bg-background"
          >
            <option value="all">All Types</option>
            <option value="fcc_order">FCC Orders</option>
            <option value="fcc_guidance">FCC Guidance</option>
            <option value="fcc_public_notice">FCC Notices</option>
            <option value="state_puc_docket">State PUC Dockets</option>
            <option value="carrier_section_214_filing">Section 214 Filings</option>
            <option value="carrier_retirement_notice">Retirement Notices</option>
          </select>
        </div>

        {/* Source indicator */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {isLive ? (
            <><span style={{ width: 6, height: 6, borderRadius: '50%', background: '#00A972', display: 'inline-block' }} /> Live corpus ({docs.length} documents)</>
          ) : (
            <><span style={{ width: 6, height: 6, borderRadius: '50%', background: '#D97706', display: 'inline-block' }} /> Mock data</>
          )}
          {loading && <span>Loading...</span>}
        </div>

        {/* Document list */}
        <div className="overflow-y-auto space-y-2" style={{ maxHeight: 'calc(100% - 80px)' }}>
          {docs.map((doc) => (
            <button
              key={doc.doc_id}
              onClick={() => setSelectedDoc(doc)}
              className={`w-full text-left border rounded-lg p-3 hover:bg-muted/50 transition-colors ${
                selectedDoc?.doc_id === doc.doc_id ? 'ring-2 ring-primary' : ''
              } ${highlightDocId === doc.doc_id ? 'bg-yellow-50' : ''}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs bg-muted px-1.5 py-0.5 rounded">
                  {DOC_TYPE_LABELS[doc.document_type] ?? doc.document_type}
                </span>
                <span className="text-xs text-muted-foreground">{doc.jurisdiction}</span>
                {doc.effective_date && (
                  <span className="text-xs text-muted-foreground">{doc.effective_date}</span>
                )}
              </div>
              <p className="text-sm font-medium">{doc.title}</p>
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{doc.summary}</p>
            </button>
          ))}
          {docs.length === 0 && !loading && (
            <div className="p-8 text-center text-muted-foreground">
              No documents match the current filters.
            </div>
          )}
        </div>
      </div>

      {/* Document detail panel */}
      <div className="w-full lg:w-1/2 border rounded-lg overflow-y-auto min-h-[300px] lg:min-h-0">
        {selectedDoc ? (
          <div className="p-4">
            <h3 className="text-lg font-semibold mb-2">{selectedDoc.title}</h3>

            <div className="grid grid-cols-2 gap-3 text-sm mb-4">
              <div>
                <p className="text-xs text-muted-foreground">Issuing Body</p>
                <p>{selectedDoc.issuing_body}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Jurisdiction</p>
                <p>{selectedDoc.jurisdiction}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Effective Date</p>
                <p>{selectedDoc.effective_date || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Document Type</p>
                <p>{DOC_TYPE_LABELS[selectedDoc.document_type] ?? selectedDoc.document_type}</p>
              </div>
              {selectedDoc.docket_number && (
                <div>
                  <p className="text-xs text-muted-foreground">Docket Number</p>
                  <p>{selectedDoc.docket_number}</p>
                </div>
              )}
              {selectedDoc.notice_period_days && (
                <div>
                  <p className="text-xs text-muted-foreground">Notice Period</p>
                  <p>{selectedDoc.notice_period_days} days</p>
                </div>
              )}
              {selectedDoc.word_count && (
                <div>
                  <p className="text-xs text-muted-foreground">Word Count</p>
                  <p>{parseInt(selectedDoc.word_count).toLocaleString()}</p>
                </div>
              )}
            </div>

            {selectedDoc.regulatory_topic && (
              <div className="mb-4">
                <p className="text-xs text-muted-foreground mb-1">Regulatory Topic</p>
                <span className="text-xs bg-muted px-2 py-0.5 rounded">
                  {selectedDoc.regulatory_topic.replace(/_/g, ' ')}
                </span>
              </div>
            )}

            {selectedDoc.citation_reference && (
              <div className="mb-4">
                <p className="text-xs text-muted-foreground mb-1">Citation Reference</p>
                <p className="text-sm">{selectedDoc.citation_reference}</p>
              </div>
            )}

            <div>
              <p className="text-xs text-muted-foreground mb-1">Summary</p>
              <p className="text-sm leading-relaxed">{selectedDoc.summary}</p>
            </div>

            {/* Document content preview for live docs */}
            {selectedDoc.isLive && (
              <div className="mt-4 p-3 border rounded-lg bg-muted/30">
                <p className="text-xs text-muted-foreground mb-1">Source</p>
                <p className="text-xs">
                  Live from <code>fcc_regulatory_document</code> corpus
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <p className="text-sm">Select a document to view details</p>
          </div>
        )}
      </div>
    </div>
  );
}
