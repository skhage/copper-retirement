/**
 * App.tsx
 * Root component for the Dig-Safe Triage Console (P7-TRIAGE)
 * Demo Beat 3: "Dig crew hit something — triage/reroute fast?"
 *
 * Layout:
 *   [TriageKPIs]                         ← top bar (6 KPI cards)
 *   [IncidentMap | TriageAgentChat]      ← main split view
 *   [IncidentDetailPanel]                ← selected incident detail
 *   [IncidentTable]                      ← incident list with filters
 *   [ActionLog]                          ← audit trail
 *
 * IncidentForm is a modal triggered by "Report Incident" button.
 *
 * All data is SYNTHETIC until P0-DATAGEN-DIGSAFE-EXECUTE + P6-TRIAGE land.
 */
import { useState, useCallback } from 'react';
import { TriageKPIs } from './components/TriageKPIs';
import { IncidentMap } from './components/IncidentMap';
import { TriageAgentChat } from './components/TriageAgentChat';
import { IncidentForm } from './components/IncidentForm';
import { IncidentDetailPanel } from './components/IncidentDetailPanel';
import { IncidentTable } from './components/IncidentTable';
import { ActionLog } from './components/ActionLog';
import type { Incident, Severity, IncidentStatus } from './mock/mockData';

export interface TriageFilters {
  severity: string;
  state: string;
  status: string;
}

export default function App() {
  // --- State ---
  const [filters, setFilters] = useState<TriageFilters>({
    severity: 'all',
    state: 'all',
    status: 'all',
  });
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [activeTab, setActiveTab] = useState<'map' | 'table' | 'log'>('map');

  const handleIncidentSelect = useCallback((incident: Incident | null) => {
    setSelectedIncident(incident);
  }, []);

  const handleReportIncident = useCallback(() => {
    setShowForm(true);
  }, []);

  const handleFormClose = useCallback(() => {
    setShowForm(false);
  }, []);

  const handleFormSubmit = useCallback((incident: Record<string, unknown>) => {
    console.log('[dig-triage] New incident submitted:', incident);
    setShowForm(false);
    // TODO: POST to /api/triage/incident, refresh incident list
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Lakelink Fiber nav bar */}
      <nav className="flex items-center gap-3 px-4 py-3 bg-[#1B3139] text-white">
        <span className="text-lg font-semibold">Lakelink Fiber</span>
        <span className="text-sm opacity-70">|</span>
        <span className="text-sm">Dig-Safe Triage Console</span>
        <div className="ml-auto flex items-center gap-3">
          <button
            onClick={handleReportIncident}
            className="px-4 py-2 bg-[#FF3621] text-white rounded-md text-sm font-medium hover:bg-[#FF3621]/90 transition-colors focus-visible:ring-2 focus-visible:ring-[#FF3621] focus-visible:ring-offset-2 focus-visible:outline-none"
          >
            + Report Incident
          </button>
          <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
            SYNTHETIC DATA
          </span>
        </div>
      </nav>

      <div className="p-4">

      {/* KPI bar */}
      <TriageKPIs />

      {/* Tab navigation */}
      <div className="flex gap-1 mb-3 border-b">
        {(['map', 'table', 'log'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors focus-visible:ring-2 focus-visible:ring-[#FF3621] focus-visible:outline-none ${
              activeTab === tab
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab === 'map' ? 'Incident Map' : tab === 'table' ? 'Incident List' : 'Action Log'}
          </button>
        ))}
      </div>

      {/* Main content */}
      {activeTab === 'map' && (
        <div className="flex gap-4 mb-4">
          {/* Map + incident detail (left) */}
          <div className="flex-1">
            <IncidentMap
              filters={filters}
              onIncidentSelect={handleIncidentSelect}
              selectedIncident={selectedIncident}
            />
            {selectedIncident && (
              <div className="mt-3">
                <IncidentDetailPanel
                  incident={selectedIncident}
                  onClose={() => setSelectedIncident(null)}
                />
              </div>
            )}
          </div>
          {/* Agent chat (right) */}
          <div className="w-[420px] flex-shrink-0">
            <TriageAgentChat selectedIncident={selectedIncident} />
          </div>
        </div>
      )}

      {activeTab === 'table' && (
        <IncidentTable
          filters={filters}
          onFilterChange={setFilters}
          onIncidentSelect={handleIncidentSelect}
        />
      )}

      {activeTab === 'log' && <ActionLog />}

      {/* Incident form modal */}
      {showForm && (
        <IncidentForm onClose={handleFormClose} onSubmit={handleFormSubmit} />
      )}
      </div>
    </div>
  );
}
