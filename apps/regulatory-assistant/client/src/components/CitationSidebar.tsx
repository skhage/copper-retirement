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

        {/* Citation metadata */}
        <div className="space-y-3">
          <div>
            <p className="text-xs text-muted-foreground">Document</p>
            <p className="text-sm font-medium">{citation.document_title}</p>
          </div>
          <div className="flex gap-4">
            <div>
              <p className="text-xs text-muted-foreground">Reference</p>
              <p className="text-sm">{citation.paragraph_ref}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Jurisdiction</p>
              <p className="text-sm">{citation.jurisdiction}</p>
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Effective Date</p>
            <p className="text-sm">{citation.effective_date}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Confidence</p>
            <span className={`text-xs px-2 py-0.5 rounded ${
              citation.confidence === 'high' ? 'bg-green-100 text-green-800' :
              citation.confidence === 'medium' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              {citation.confidence}
            </span>
          </div>
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
