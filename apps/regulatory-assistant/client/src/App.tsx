/**
 * App.tsx
 * Root component for the Regulatory Assistant (P7-REG)
 * Demo Beat 4: "Are we clear on regs everywhere we touch?"
 *
 * 4-tab navigation:
 *   [Ask]  [Jurisdiction Map]  [Checklist]  [Documents]
 *
 * Global jurisdiction filter persists across all screens.
 * All data is SYNTHETIC until P6-REG + P0-DATAGEN-REG + P1-REG land.
 */
import { useState, useCallback } from 'react';
import { RegAgentChat } from './components/RegAgentChat';
import { JurisdictionMap } from './components/JurisdictionMap';
import { ComplianceChecklist } from './components/ComplianceChecklist';
import { DocumentBrowser } from './components/DocumentBrowser';
import { RegKPIs } from './components/RegKPIs';
import { CitationSidebar } from './components/CitationSidebar';
import type { ActiveTab, Citation } from './mock/mockData';

const TABS: { key: ActiveTab; label: string }[] = [
  { key: 'ask', label: 'Ask' },
  { key: 'jurisdiction', label: 'Jurisdiction Map' },
  { key: 'checklist', label: 'Checklist' },
  { key: 'documents', label: 'Documents' },
];

export default function App() {
  // --- State ---
  const [activeTab, setActiveTab] = useState<ActiveTab>('ask');
  const [jurisdictionFilter, setJurisdictionFilter] = useState<string>('all');
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [navigateToDoc, setNavigateToDoc] = useState<string | null>(null);

  const handleCitationClick = useCallback((citation: Citation) => {
    setActiveCitation(citation);
  }, []);

  const handleViewDocument = useCallback((docId: string) => {
    setNavigateToDoc(docId);
    setActiveTab('documents');
    setActiveCitation(null);
  }, []);

  const handleCloseCitation = useCallback(() => {
    setActiveCitation(null);
  }, []);

  const handleJurisdictionSelect = useCallback((state: string) => {
    setJurisdictionFilter(state);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Regulatory Assistant</h1>
            <p className="text-sm text-muted-foreground">
              LakeLink Fiber — Copper Retirement Compliance
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* Jurisdiction context (global filter) */}
            <div className="flex items-center gap-2 text-sm">
              <span className="text-muted-foreground">Jurisdiction:</span>
              <select
                value={jurisdictionFilter}
                onChange={(e) => setJurisdictionFilter(e.target.value)}
                className="border rounded px-2 py-1 text-sm bg-background"
              >
                <option value="all">All States</option>
                <option value="CA">California</option>
                <option value="WA">Washington</option>
                <option value="OR">Oregon</option>
                <option value="AZ">Arizona</option>
                <option value="MN">Minnesota</option>
                <option value="ID">Idaho</option>
              </select>
            </div>
            <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
              SYNTHETIC DATA
            </span>
          </div>
        </div>

        {/* Tab navigation */}
        <div className="flex gap-1 mt-4">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 text-sm font-medium rounded-t transition-colors ${
                activeTab === tab.key
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* KPI bar */}
      <div className="px-6 py-3 border-b bg-muted/30">
        <RegKPIs jurisdictionFilter={jurisdictionFilter} />
      </div>

      {/* Main content area + citation sidebar */}
      <div className="flex">
        <div className="flex-1 px-6 py-4">
          {activeTab === 'ask' && (
            <RegAgentChat
              jurisdictionFilter={jurisdictionFilter}
              onCitationClick={handleCitationClick}
            />
          )}
          {activeTab === 'jurisdiction' && (
            <JurisdictionMap
              jurisdictionFilter={jurisdictionFilter}
              onStateSelect={handleJurisdictionSelect}
            />
          )}
          {activeTab === 'checklist' && (
            <ComplianceChecklist jurisdictionFilter={jurisdictionFilter} />
          )}
          {activeTab === 'documents' && (
            <DocumentBrowser
              jurisdictionFilter={jurisdictionFilter}
              highlightDocId={navigateToDoc}
            />
          )}
        </div>

        {/* Citation sidebar (overlays on right when active) */}
        {activeCitation && (
          <CitationSidebar
            citation={activeCitation}
            onClose={handleCloseCitation}
            onViewDocument={handleViewDocument}
          />
        )}
      </div>
    </div>
  );
}
