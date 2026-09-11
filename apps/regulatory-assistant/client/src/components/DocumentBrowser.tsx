/**
 * DocumentBrowser.tsx
 * Screen 4 — Document Browser.
 * Searchable list of FCC orders, state PUC dockets, notice templates.
 * Filter by document_type, jurisdiction, date range.
 * Document detail panel with metadata.
 */
import { useState, useMemo, useEffect } from 'react';
import { USE_MOCK_DATA, getMockDocuments } from '../mock/mockData';
import type { RegDocument } from '../mock/mockData';

interface DocumentBrowserProps {
  jurisdictionFilter: string;
  highlightDocId: string | null;
}

const DOC_TYPE_LABELS: Record<string, string> = {
  fcc_order: 'FCC Order',
  puc_docket: 'PUC Docket',
  notice_template: 'Notice Template',
  guidance: 'Guidance',
  legislative: 'Legislative',
};

export function DocumentBrowser({ jurisdictionFilter, highlightDocId }: DocumentBrowserProps) {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [selectedDoc, setSelectedDoc] = useState<RegDocument | null>(null);

  const docs = useMemo(
    () => getMockDocuments({
      jurisdiction: jurisdictionFilter !== 'all' ? jurisdictionFilter : undefined,
      document_type: typeFilter !== 'all' ? typeFilter : undefined,
      search: search || undefined,
    }),
    [jurisdictionFilter, typeFilter, search]
  );

  // Auto-select highlighted document (from citation click)
  useEffect(() => {
    if (highlightDocId) {
      const doc = docs.find((d) => d.doc_id === highlightDocId);
      if (doc) setSelectedDoc(doc);
    }
  }, [highlightDocId, docs]);

  return (
    <div className="flex gap-4 h-[calc(100vh-280px)]">
      {/* Document list */}
      <div className="w-1/2 space-y-3">
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
            <option value="puc_docket">PUC Dockets</option>
            <option value="notice_template">Notice Templates</option>
            <option value="guidance">Guidance</option>
            <option value="legislative">Legislative</option>
          </select>
        </div>

        {/* Document list */}
        <div className="overflow-y-auto space-y-2" style={{ maxHeight: 'calc(100% - 50px)' }}>
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
              </div>
              <p className="text-sm font-medium">{doc.title}</p>
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{doc.summary}</p>
            </button>
          ))}
          {docs.length === 0 && (
            <div className="p-8 text-center text-muted-foreground">
              No documents match the current filters.
            </div>
          )}
        </div>
      </div>

      {/* Document detail panel */}
      <div className="w-1/2 border rounded-lg overflow-y-auto">
        {selectedDoc ? (
          <div className="p-4">
            {/* Staleness warning */}
            {selectedDoc.effective_end_date &&
              new Date(selectedDoc.effective_end_date) < new Date() && (
                <div className="mb-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
                  ⚠ This regulation may have been superseded (effective end: {selectedDoc.effective_end_date}).
                </div>
              )}

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
                <p>{selectedDoc.effective_date}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Document Type</p>
                <p>{DOC_TYPE_LABELS[selectedDoc.document_type]}</p>
              </div>
            </div>

            <div className="mb-4">
              <p className="text-xs text-muted-foreground mb-1">Keywords</p>
              <div className="flex flex-wrap gap-1">
                {selectedDoc.keywords.map((kw) => (
                  <span key={kw} className="text-xs bg-muted px-2 py-0.5 rounded">
                    {kw}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <p className="text-xs text-muted-foreground mb-1">Summary</p>
              <p className="text-sm leading-relaxed">{selectedDoc.summary}</p>
            </div>

            {/* Document viewer placeholder */}
            <div className="mt-4 border rounded-lg bg-muted p-8 text-center text-muted-foreground">
              <p className="text-sm font-medium">Document Viewer</p>
              <p className="text-xs mt-1">
                Full PDF/text rendering will be available when P1-REG document corpus is ingested.
              </p>
              <p className="text-xs mt-1">
                Citation passage highlighting requires Lakebase Search (P5-SEARCH).
              </p>
            </div>
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
