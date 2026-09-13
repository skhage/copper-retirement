/**
 * App.tsx
 * Root component for the Copper Retirement Impact Map (P7-MAP)
 * Demo Beat 1: "Where should we dig up copper, and what happens when we do?"
 *
 * REDESIGNED per CEO directive (2026-09-11):
 *   NOT about at-risk devices. About retirement impact:
 *   - Customer risk scores and counts per wire center
 *   - Revenue at risk (MRR) from copper services
 *   - Network disruption if copper is dug up
 *   - What-if analysis via Genie Agent
 *
 * Layout:
 *   [RetirementKPIs]                         ← top bar (6 KPI cards)
 *   [Filters] [ImpactMap | Detail] [WhatIf]  ← 3-column: filters + map + chat
 *   [RetirementTable]                        ← wire center table with impact metrics
 *
 * All data is SYNTHETIC until FIX-COORDINATES + P2-H3 + P4-RISK land.
 */
import { useState, useCallback } from 'react';
import { Card, CardContent } from '@databricks/appkit-ui/react';
import { ImpactDetailPanel } from './components/ImpactDetailPanel';
import { WhatIfChat } from './components/WhatIfChat';
import {
  USE_MOCK_DATA,
  getMockWireCenters,
  getMockKPIs,
  PRIORITY_COLORS,
  PRIORITY_TIERS,
} from './mock/retirementData';
import type { WireCenterImpact, Filters } from './mock/retirementData';

export default function App() {
  const [filters, setFilters] = useState<Filters>({ state: 'all', priorityTier: 'all' });
  const [selectedWC, setSelectedWC] = useState<WireCenterImpact | null>(null);
  const [activeTab, setActiveTab] = useState<'map' | 'table' | 'whatif'>('map');

  const wireCenters = getMockWireCenters(filters);
  const kpis = getMockKPIs();
  const states = [...new Set(getMockWireCenters().map((w) => w.state))].sort();

  const handleSelectWC = useCallback((wc: WireCenterImpact) => { setSelectedWC(wc); }, []);
  const handleCloseDetail = useCallback(() => { setSelectedWC(null); }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="px-6 pt-4 pb-2 flex items-center justify-between">
        <div>
          <p className="text-base" style={{ fontWeight: 600, color: '#1B3139', lineHeight: 1.2 }}>Lakelink Fiber</p>
          <h1 className="text-2xl font-bold mt-1" style={{ color: '#1B3139' }}>Copper Retirement Impact Map</h1>
          <p className="text-sm text-muted-foreground">Where to dig, what it costs, who it affects</p>
        </div>
        <div className="flex items-center gap-3">
          {USE_MOCK_DATA && <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">SYNTHETIC DATA</span>}
        </div>
      </div>

      {/* KPI bar */}
      <div className="px-6 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mb-4">
        <Card><CardContent className="p-3">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Revenue at Risk</p>
          <p className="text-xl font-bold text-red-600">${(kpis.total_revenue_at_risk_mrr / 1000).toFixed(0)}K <span className="text-xs font-normal">MRR</span></p>
          <p className="text-xs text-muted-foreground">${(kpis.total_revenue_at_risk_mrr * 12 / 1000000).toFixed(1)}M annualized</p>
        </CardContent></Card>
        <Card><CardContent className="p-3">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Customers on Copper</p>
          <p className="text-xl font-bold">{kpis.total_customers_on_copper.toLocaleString()}</p>
          <p className="text-xs text-muted-foreground">{kpis.contract_locked_customers} contract-locked</p>
        </CardContent></Card>
        <Card><CardContent className="p-3">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Wire Centers</p>
          <p className="text-xl font-bold">{kpis.wire_centers_to_retire}</p>
          <p className="text-xs text-muted-foreground">Targeted for retirement</p>
        </CardContent></Card>
        <Card><CardContent className="p-3">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Services Affected</p>
          <p className="text-xl font-bold">{kpis.total_services_affected.toLocaleString()}</p>
          <p className="text-xs text-muted-foreground">Copper-dependent</p>
        </CardContent></Card>
        <Card><CardContent className="p-3">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Net Retirement Cost</p>
          <p className="text-xl font-bold">${(kpis.total_net_cost / 1000000).toFixed(1)}M</p>
          <p className="text-xs text-muted-foreground">After scrap recovery</p>
        </CardContent></Card>
        <Card><CardContent className="p-3">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Fiber Ready</p>
          <p className="text-xl font-bold text-green-600">{kpis.fiber_ready_pct_avg}%</p>
          <p className="text-xs text-muted-foreground">Avg across wire centers</p>
        </CardContent></Card>
      </div>

      {/* Tab bar */}
      <div className="px-6 mb-3 flex gap-1 border-b">
        {[
          { id: 'map' as const, label: 'Impact Map' },
          { id: 'table' as const, label: 'Wire Center Table' },
          { id: 'whatif' as const, label: 'What-If Analysis' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Filters (shared) */}
      <div className="px-6 mb-3 flex gap-3 items-center">
        <select
          value={filters.state}
          onChange={(e) => setFilters((f) => ({ ...f, state: e.target.value }))}
          className="text-sm border rounded px-2 py-1"
        >
          <option value="all">All States</option>
          {states.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select
          value={filters.priorityTier}
          onChange={(e) => setFilters((f) => ({ ...f, priorityTier: e.target.value }))}
          className="text-sm border rounded px-2 py-1"
        >
          <option value="all">All Priorities</option>
          {PRIORITY_TIERS.map((t) => <option key={t} value={t}>{t.replace('-', ' ')}</option>)}
        </select>
        <span className="text-xs text-muted-foreground">{wireCenters.length} wire centers</span>
      </div>

      {/* Main content area */}
      <div className="px-6 pb-6">
        {/* ---- MAP TAB ---- */}
        {activeTab === 'map' && (
          <div className="flex gap-4">
            {/* Map placeholder + wire center cards */}
            <div className="flex-1">
              <div className="bg-muted rounded-lg relative overflow-hidden mb-4" style={{ minHeight: 460 }}>
                <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground">
                  <p className="text-lg font-semibold mb-1">Retirement Impact Map</p>
                  <p className="text-sm">deck.gl H3HexagonLayer — colored by retirement priority</p>
                  <p className="text-xs mt-1 text-muted-foreground">Click a wire center below to see impact details</p>
                </div>
                {/* Wire center dots on map placeholder */}
                <div className="absolute bottom-4 left-4 right-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                  {wireCenters.map((wc) => (
                    <button
                      key={wc.wire_center_id}
                      className="p-2 rounded text-xs text-left border bg-white/90 hover:bg-white transition-colors"
                      style={{ borderLeftColor: PRIORITY_COLORS[wc.priority_tier], borderLeftWidth: 4 }}
                      onClick={() => handleSelectWC(wc)}
                    >
                      <div className="font-semibold">{wc.wire_center_name}</div>
                      <div className="text-muted-foreground">
                        {wc.customers_affected} customers &middot; ${(wc.revenue_at_risk_mrr / 1000).toFixed(0)}K MRR
                      </div>
                      <div className="text-muted-foreground">
                        Network: {wc.network_disruption_score}/100 &middot; Fiber: {wc.fiber_ready_pct}%
                      </div>
                    </button>
                  ))}
                </div>
              </div>
              {/* Priority legend */}
              <div className="flex gap-4 justify-center">
                {PRIORITY_TIERS.map((tier) => (
                  <div key={tier} className="flex items-center gap-1 text-xs">
                    <span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: PRIORITY_COLORS[tier] }} />
                    <span className="capitalize">{tier.replace('-', ' ')}</span>
                  </div>
                ))}
              </div>
            </div>
            {/* Detail panel */}
            {selectedWC && <ImpactDetailPanel wireCenter={selectedWC} onClose={handleCloseDetail} />}
          </div>
        )}

        {/* ---- TABLE TAB ---- */}
        {activeTab === 'table' && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-muted text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="p-2 text-left">Wire Center</th>
                  <th className="p-2 text-left">State</th>
                  <th className="p-2 text-right">Customers</th>
                  <th className="p-2 text-right">Revenue MRR</th>
                  <th className="p-2 text-right">Network Risk</th>
                  <th className="p-2 text-right">Fiber Ready</th>
                  <th className="p-2 text-right">Net Cost</th>
                  <th className="p-2 text-center">Priority</th>
                  <th className="p-2 text-center">Status</th>
                  <th className="p-2 text-center">Constraints</th>
                </tr>
              </thead>
              <tbody>
                {wireCenters
                  .sort((a, b) => b.retirement_priority - a.retirement_priority)
                  .map((wc) => (
                    <tr
                      key={wc.wire_center_id}
                      className="border-b hover:bg-muted/50 cursor-pointer"
                      onClick={() => { setSelectedWC(wc); setActiveTab('map'); }}
                    >
                      <td className="p-2 font-medium">{wc.wire_center_name}</td>
                      <td className="p-2">{wc.state}</td>
                      <td className="p-2 text-right">{wc.customers_affected}</td>
                      <td className="p-2 text-right">${(wc.revenue_at_risk_mrr / 1000).toFixed(1)}K</td>
                      <td className="p-2 text-right">
                        <span className={wc.network_disruption_score >= 50 ? 'text-red-600 font-medium' : ''}>
                          {wc.network_disruption_score}/100
                        </span>
                      </td>
                      <td className="p-2 text-right">
                        <span className={wc.fiber_ready_pct >= 80 ? 'text-green-600 font-medium' : ''}>
                          {wc.fiber_ready_pct}%
                        </span>
                      </td>
                      <td className="p-2 text-right">${(wc.net_cost_usd / 1000).toFixed(0)}K</td>
                      <td className="p-2 text-center">
                        <span
                          className="inline-block px-2 py-0.5 rounded-full text-xs text-white capitalize"
                          style={{ backgroundColor: PRIORITY_COLORS[wc.priority_tier] }}
                        >
                          {wc.priority_tier.replace('-', ' ')}
                        </span>
                      </td>
                      <td className="p-2 text-center capitalize text-xs">{wc.status.replace('-', ' ')}</td>
                      <td className="p-2 text-center text-xs">
                        {wc.customers_contract_locked > 0 && <span title="Contract-locked customers">&#128274; {wc.customers_contract_locked}</span>}
                        {wc.has_active_dig_incident && <span className="ml-1" title="Active dig incident">&#9888;</span>}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}

        {/* ---- WHAT-IF TAB ---- */}
        {activeTab === 'whatif' && (
          <div className="max-w-3xl mx-auto" style={{ minHeight: 500 }}>
            <WhatIfChat />
          </div>
        )}
      </div>
    </div>
  );
}
