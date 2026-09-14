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
import { LakeLinkHeader } from './components/LakeLinkHeader';
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
      {/* Header — shared LakeLinkHeader (BRAND_GUIDE §6) */}
      <LakeLinkHeader
        subtitle="Regulatory Assistant"
        tagline="Copper Retirement Compliance"
        dataSource="LIVE"
      >
        {/* Jurisdiction context (global filter) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.875rem' }}>
          <span style={{ color: '#6E8898' }}>Jurisdiction:</span>
          <select
            value={jurisdictionFilter}
            onChange={(e) => setJurisdictionFilter(e.target.value)}
            className="border rounded px-2 py-1 text-sm bg-background"
          >
            <option value="all">All States</option>
            <option value="CO">Colorado</option>
            <option value="WA">Washington</option>
            <option value="OR">Oregon</option>
            <option value="AZ">Arizona</option>
            <option value="MN">Minnesota</option>
            <option value="ID">Idaho</option>
          </select>
        </div>
      </LakeLinkHeader>

      {/* Tab navigation */}
      <div style={{ padding: '0 24px', borderBottom: '1px solid #E5E2DD' }}>
        <div style={{ display: 'flex', gap: 4, paddingTop: 8 }}>
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                padding: '8px 16px',
                fontSize: '0.875rem',
                fontWeight: 500,
                borderRadius: '6px 6px 0 0',
                border: 'none',
                cursor: 'pointer',
                transition: 'background-color 0.15s',
                ...(activeTab === tab.key
                  ? { background: '#FF3621', color: '#FFFFFF' }
                  : { background: 'transparent', color: '#6E8898' }),
              }}
              onMouseEnter={(e) => {
                if (activeTab !== tab.key) e.currentTarget.style.background = '#F0EDEA';
              }}
              onMouseLeave={(e) => {
                if (activeTab !== tab.key) e.currentTarget.style.background = 'transparent';
              }}
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
