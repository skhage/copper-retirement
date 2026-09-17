/**
 * CitationSidebar.tsx
 * Right-side panel that opens when a citation link is clicked.
 * Shows document excerpt with highlighted passage, metadata, and link to full document.
 */
import { ChevronRight } from 'lucide-react';
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
            aria-label="Close citation sidebar"
            title="Close"
            className="text-muted-foreground hover:text-foreground text-lg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FF3621]"
          >
            ×
          </button>
        </div>

        {/* Confidence + jurisdiction banner */}
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xs px-2 py-0.5 rounded font-medium" style={{
            backgroundColor: citation.confidence === 'high' ? 'rgba(0,169,114,0.15)' :
              citation.confidence === 'medium' ? 'rgba(217,119,6,0.15)' : 'rgba(255,54,33,0.15)',
            color: citation.confidence === 'high' ? '#00A972' :
              citation.confidence === 'medium' ? '#D97706' : '#FF3621',
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
          {citation.doc_id && (
            <div className="rounded px-3 py-2" style={{ backgroundColor: 'rgba(27,49,57,0.04)', border: '1px solid rgba(27,49,57,0.1)' }}>
              <p className="text-xs" style={{ color: '#6E8898' }}>Docket / Reference</p>
              <p className="text-sm font-mono font-semibold" style={{ color: '#FF3621', fontSize: '0.8rem' }}>
                {citation.doc_id}
              </p>
            </div>
          )}
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
        </div>

        {/* Excerpt */}
        <div className="mt-4">
          <p className="text-xs text-muted-foreground mb-1">Source Excerpt</p>
          <div className="rounded p-3 text-sm leading-relaxed" style={{ backgroundColor: 'rgba(217,119,6,0.08)', border: '1px solid rgba(217,119,6,0.2)' }}>
            {citation.excerpt}
          </div>
        </div>

        {/* Actions */}
        <div className="mt-4 space-y-2">
          <button
            onClick={() => onViewDocument(citation.doc_id)}
            className="w-full text-left px-3 py-2 text-sm border rounded hover:bg-muted transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FF3621]"
          >
            <ChevronRight size={14} strokeWidth={1.5} style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: 4 }} /> View full document
          </button>
          <button
            className="w-full text-left px-3 py-2 text-sm border rounded hover:bg-muted transition-colors text-muted-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FF3621]"
          >
            <ChevronRight size={14} strokeWidth={1.5} style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: 4 }} /> Copy citation
          </button>
        </div>
      </div>
    </div>
  );
}
