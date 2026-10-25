/**
 * tabs/triage/App.tsx — Dig Triage tab of the unified Copper Retirement Accelerator (ACC-APP-PORT-TRIAGE).
 * Ported 2026-10-24 from the retired standalone dig-triage app; exported as TriageTab and mounted by client/src/App.tsx (#triage).
 * Header/brand come from the accelerator shell; colors from styles/tokens.css only.
 * Original: Root component for the Dig-Safe Triage Console (P7-TRIAGE)
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
import { useState, useCallback, useEffect } from 'react';
import { TabHeader, TabBar, SyntheticBadge, EmptyState } from '../../components/shared';
import { TriageKPIs } from './components/TriageKPIs';
import { IncidentMap } from './components/IncidentMap';
import { TriageAgentChat } from './components/TriageAgentChat';
import { IncidentForm } from './components/IncidentForm';
import { IncidentDetailPanel } from './components/IncidentDetailPanel';
import { IncidentTable } from './components/IncidentTable';
import { ActionLog } from './components/ActionLog';
import type { Incident, Severity, IncidentStatus } from './mock/mockData';
import { fetchIncidentDetail, fetchNearbyIncidents, fetchRerouteSuggestion, describeApiError, ApiError } from './lib/triageApi';
import type { IncidentDetail, NearbyIncident, RerouteSuggestion } from './lib/triageApi';
import { Search } from 'lucide-react';

export interface TriageFilters {
  severity: string;
  state: string;
  status: string;
}

const SUB_TABS = [
  { id: 'map', label: 'Incident Map' },
  { id: 'table', label: 'Incident List' },
  { id: 'log', label: 'Action Log' },
] as const;

interface Summary811 { tickets: number; states: number; telecom: number; origin: string; source: string }

/** Real 811 one-call context (directive 13: reuse provable_resilience_intelligence.stg_811_dig_ticket). */
function Dig811Badge() {
  const [s, setS] = useState<Summary811 | null>(null);
  const [err811, setErr811] = useState<string | null>(null);
  useEffect(() => {
    fetch('/api/triage/811')
      .then(async (r) => {
        if (r.ok) return r.json();
        const b = await r.json().catch(() => ({}));
        throw new ApiError(r.status, b.error || `HTTP ${r.status}`);
      })
      .then((j) => {
        const rows: Array<Record<string, string>> = j.data || [];
        setS({
          tickets: rows.reduce((a, r) => a + (parseInt(r.tickets, 10) || 0), 0),
          telecom: rows.reduce((a, r) => a + (parseInt(r.telecom_tickets, 10) || 0), 0),
          states: new Set(rows.map((r) => r.state)).size,
          origin: rows[0]?.origin || 'INGESTED',
          // ACC-QA-DEF-TRIAGE-LINEAGE-LABEL: lineage comes from the server (DIG_811_TABLE env), never hard-coded.
          source: typeof j.source === 'string' ? j.source : '',
        });
      })
      .catch((e) => { setS(null); setErr811(describeApiError(e, 'no 811 rows')); });
  }, []);
  if (err811) {
    return (
      <span className="text-xs text-muted-foreground" role="status" aria-live="polite" title={err811}>
        811 data unavailable ({err811})
      </span>
    );
  }
  if (!s) return null;
  return (
    <span className="text-xs text-muted-foreground" title={s.source || undefined}>
      811 tickets ({s.origin}): {s.tickets.toLocaleString()} across {s.states} states, {s.telecom.toLocaleString()} telecom/copper
    </span>
  );
}

export function TriageTab() {
  // --- State ---
  const [filters, setFilters] = useState<TriageFilters>({
    severity: 'all',
    state: 'all',
    status: 'all',
  });
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [activeTab, setActiveTab] = useState<'map' | 'table' | 'log'>('map');
  const [enrichedData, setEnrichedData] = useState<IncidentDetail | null>(null);
  const [nearbyIncidents, setNearbyIncidents] = useState<NearbyIncident[]>([]);
  const [rerouteSuggestion, setRerouteSuggestion] = useState<RerouteSuggestion | null>(null);
  const [isLoadingEnriched, setIsLoadingEnriched] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchError, setSearchError] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [enrichErrors, setEnrichErrors] = useState<Array<{ section: string; reason: string }>>([]);
  const [toast, setToast] = useState<string | null>(null);

  // Fetch enriched UC data when an incident is selected
  useEffect(() => {
    if (!selectedIncident) {
      setEnrichedData(null);
      setNearbyIncidents([]);
      setRerouteSuggestion(null);
      setEnrichErrors([]);
      return;
    }
    const numericId = parseInt(selectedIncident.incident_id.replace('INC-', ''), 10);
    if (isNaN(numericId)) return;

    setIsLoadingEnriched(true);
    Promise.allSettled([
      fetchIncidentDetail(numericId),
      fetchNearbyIncidents(selectedIncident.latitude, selectedIncident.longitude, 50),
      fetchRerouteSuggestion(numericId),
    ]).then(([detailRes, nearbyRes, rerouteRes]) => {
      setEnrichedData(detailRes.status === 'fulfilled' ? detailRes.value : null);
      setNearbyIncidents(nearbyRes.status === 'fulfilled' ? nearbyRes.value : []);
      setRerouteSuggestion(rerouteRes.status === 'fulfilled' ? rerouteRes.value : null);
      // Surface every failed section with its real reason instead of silently showing 'none'.
      const errs: Array<{ section: string; reason: string }> = [];
      if (detailRes.status === 'rejected') errs.push({ section: 'Incident enrichment (wire center, nearest device)', reason: describeApiError(detailRes.reason, 'No enrichment row for this incident') });
      if (nearbyRes.status === 'rejected') errs.push({ section: 'Nearby incidents', reason: describeApiError(nearbyRes.reason, 'No nearby incidents found') });
      if (rerouteRes.status === 'rejected') errs.push({ section: 'Reroute suggestion', reason: describeApiError(rerouteRes.reason, 'No reroute suggestion for this incident') });
      setEnrichErrors(errs);
      setIsLoadingEnriched(false);
    });
  }, [selectedIncident?.incident_id]);

  const handleIncidentSelect = useCallback((incident: Incident | null) => {
    setSelectedIncident(incident);
  }, []);

  // Incident search via UC incident_lookup function
  const handleSearch = useCallback(async () => {
    const raw = searchQuery.trim().replace(/^INC-/i, '');
    const numericId = parseInt(raw, 10);
    if (isNaN(numericId)) {
      setSearchError('Enter a numeric incident ID (e.g., 201857)');
      return;
    }
    setIsSearching(true);
    setSearchError(null);
    try {
      const detail = await fetchIncidentDetail(numericId);
      // Convert IncidentDetail to Incident for selection
      const inc: Incident = {
        incident_id: `INC-${detail.incident_id}`,
        incident_date: detail.incident_date,
        incident_timestamp: detail.incident_date + 'T12:00:00Z',
        severity: (detail.severity || 'major') as Severity,
        cable_type: (detail.cable_type || 'buried_direct') as Incident['cable_type'],
        cable_damage_type: detail.cable_damage_type || '',
        root_cause: detail.root_cause || '',
        state: detail.state || '',
        latitude: parseFloat(detail.incident_latitude) || 0,
        longitude: parseFloat(detail.incident_longitude) || 0,
        resolution_time_hours: detail.resolution_time_hours ? parseFloat(detail.resolution_time_hours) : null,
        reroute_required: detail.reroute_required === true || detail.reroute_required === 'true',
        service_interruption: detail.service_interruption === true || detail.service_interruption === 'true',
        affected_pair_count: parseInt(String(detail.affected_pair_count), 10) || 0,
        repair_cost: parseFloat(detail.repair_cost_amount) || 0,
        contractor_at_fault: detail.contractor_at_fault === true || detail.contractor_at_fault === 'true',
        one_call_ticket_submitted: detail.one_call_ticket_submitted === true || detail.one_call_ticket_submitted === 'true',
        status: detail.resolution_time_hours ? 'resolved' : 'open' as IncidentStatus,
        work_id: null,
        contractor_name: 'N/A',
      };
      setSelectedIncident(inc);
      setActiveTab('map');
      setSearchQuery('');
    } catch (err) {
      setSearchError(describeApiError(err, `Incident ${numericId} not found`));
    } finally {
      setIsSearching(false);
    }
  }, [searchQuery]);

  const handleReportIncident = useCallback(() => {
    setShowForm(true);
  }, []);

  const handleFormClose = useCallback(() => {
    setShowForm(false);
  }, []);

  // Demo only: Lakebase write-back is not wired, so nothing is persisted. Say so explicitly.
  const handleFormSubmit = useCallback((_incident: Record<string, unknown>) => {
    setShowForm(false);
    setToast('Demo only - not saved. Incident intake is shown for illustration; no record was written.');
    window.setTimeout(() => setToast(null), 8000);
  }, []);

  return (
    <div>
      <TabHeader
        title="Dig Triage"
        question="A dig-in just happened: what is hit, who is affected, how do we reroute?"
        badges={<><SyntheticBadge label="SYNTHETIC INCIDENTS" /><Dig811Badge /></>}
      />
      <div className="mb-3 flex flex-wrap justify-end">
        {/* Incident search — uses live UC incident_lookup function */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setSearchError(null); }}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Incident ID (e.g. 201857)"
              aria-label="Search incident by ID"
              className="w-44 px-3 py-1.5 pr-8 text-sm rounded border border-input bg-card focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
            />
            <button
              onClick={handleSearch}
              disabled={isSearching}
              aria-label="Search"
              className="absolute right-1.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <Search size={14} strokeWidth={1.5} />
            </button>
          </div>
          {searchError && (
            <span className="text-xs text-danger" role="alert">{searchError}</span>
          )}
          {isSearching && (
            <span className="text-xs text-muted-foreground animate-pulse">Searching...</span>
          )}
          <button
            onClick={handleReportIncident}
            className="px-4 py-2 bg-primary-strong text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none"
          >
            + Report Incident
          </button>
        </div>
      </div>

      <div>

      {/* KPI bar */}
      <TriageKPIs />

      {/* Tab navigation */}
      <div className="mb-3">
        <TabBar tabs={SUB_TABS} activeId={activeTab} onChange={setActiveTab} idPrefix="triage" ariaLabel="Dig triage views" />
      </div>

      {/* Main content */}
      {activeTab === 'map' && (
        <div className="flex flex-col lg:flex-row gap-4 mb-4">
          {/* Map + incident detail (left) */}
          <div className="flex-1">
            <IncidentMap
              filters={filters}
              onIncidentSelect={handleIncidentSelect}
              selectedIncident={selectedIncident}
            />
            {selectedIncident && enrichErrors.length > 0 && (
              <div className="mt-3 space-y-2" role="alert" aria-live="polite">
                {enrichErrors.map((e) => (
                  <EmptyState key={e.section} title={`${e.section} unavailable`}>
                    <p>{e.reason}</p>
                  </EmptyState>
                ))}
              </div>
            )}
            {selectedIncident && (
              <div className="mt-3">
                <IncidentDetailPanel
                  incident={selectedIncident}
                  enrichedData={enrichedData}
                  nearbyIncidents={nearbyIncidents}
                  rerouteSuggestion={rerouteSuggestion}
                  isLoadingEnriched={isLoadingEnriched}
                  onClose={() => setSelectedIncident(null)}
                />
              </div>
            )}
          </div>
          {/* Agent chat (right) */}
          <div className="w-full lg:w-[420px] flex-shrink-0">
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
      <div aria-live="polite" role="status" className="fixed bottom-4 right-4 z-50">
        {toast && (
          <div className="rounded-lg border border-input bg-card px-4 py-3 text-sm text-foreground shadow-lg max-w-sm">
            {toast}
          </div>
        )}
      </div>
      </div>
    </div>
  );
}
