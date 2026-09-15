/**
 * CitationSidebar.tsx
 * Right-side panel that opens when a citation link is clicked.
 * Shows document excerpt with highlighted passage, metadata, and link to full document.
 */
import type { Citation } from '../mock/mockData';

interface CitationSidebarProps {
  citation: Citation;
  onClose: () => void;
  onViewDocument: (docId: string) => void;
}

export function CitationSidebar({ citation, onClose, onViewDocument }: CitationSidebarProps) {
  return (
    <div className="w-96 border-l bg-background overflow-y-auto h-[calc(100vh-220px)]">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-sm">Source Citation</h3>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground text-lg"
          >
            ×
          </button>
        </div>

        {/* Confidence + jurisdiction banner */}
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xs px-2 py-0.5 rounded font-medium" style={{
            backgroundColor: citation.confidence === 'high' ? '#dcfce7' :
              citation.confidence === 'medium' ? '#fef9c3' : '#fee2e2',
            color: citation.confidence === 'high' ? '#15803d' :
              citation.confidence === 'medium' ? '#854d0e' : '#b91c1c',
          }}>
            {citation.confidence} confidence
          </span>
          <span className="text-xs px-2 py-0.5 rounded font-medium" style={{
            backgroundColor: 'rgba(27,49,57,0.06)',
            color: '#1B3139',
          }}>
            {citation.jurisdiction || 'Federal'}
          </span>
        </div>

        {/* Citation metadata */}
        <div className="space-y-3">
          <div>
            <p className="text-xs" style={{ color: '#6E8898' }}>Document Title</p>
            <p className="text-sm font-semibold" style={{ color: '#1B3139' }}>
              {citation.document_title}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs" style={{ color: '#6E8898' }}>Citation / Section</p>
              <p className="text-sm font-medium" style={{ color: '#1B3139' }}>
                {citation.paragraph_ref || '\u2014'}
              </p>
            </div>
            <div>
              <p className="text-xs" style={{ color: '#6E8898' }}>Effective Date</p>
              <p className="text-sm" style={{ color: '#1B3139' }}>
                {citation.effective_date || 'N/A'}
              </p>
            </div>
          </div>
          {citation.doc_id && (
            <div>
              <p className="text-xs" style={{ color: '#6E8898' }}>Docket / ID</p>
              <p className="text-sm font-mono" style={{ color: '#1B3139', fontSize: '0.8rem' }}>
                {citation.doc_id}
              </p>
            </div>
          )}
        </div>

        {/* Excerpt */}
        <div className="mt-4">
          <p className="text-xs text-muted-foreground mb-1">Source Excerpt</p>
          <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm leading-relaxed">
            {citation.excerpt}
          </div>
        </div>

        {/* Actions */}
        <div className="mt-4 space-y-2">
          <button
            onClick={() => onViewDocument(citation.doc_id)}
            className="w-full text-left px-3 py-2 text-sm border rounded hover:bg-muted transition-colors"
          >
            ▸ View full document
          </button>
          <button
            className="w-full text-left px-3 py-2 text-sm border rounded hover:bg-muted transition-colors text-muted-foreground"
          >
            ▸ Copy citation
          </button>
        </div>
      </div>
    </div>
  );
}
