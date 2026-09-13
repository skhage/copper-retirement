/**
 * App.tsx
 * Root component for the Retirement Plan Tracker (P7-PLAN)
 * Demo Beat 2: "Capital-efficient plan to zero copper?"
 *
 * Layout:
 *   [PlanKPIs]                              ← top bar (6 KPI cards)
 *   [WaveSelector]                          ← wave filter bar
 *   Tabs:
 *     Gantt → [GanttTimeline]              ← horizontal Gantt chart
 *     Table → [MigrationTable]             ← tabular view with filters
 *     Scenarios → [ScenarioCompare]        ← optimizer scenario comparison
 *   [CostBenefitPanel]                      ← per-wire-center cost/benefit
 *
 * All data is SYNTHETIC until P4-SEQ + P0-DATAGEN-MIGRATION land.
 */
import { useState, useCallback } from 'react';
import { PlanKPIs } from './components/PlanKPIs';
import { GanttTimeline } from './components/GanttTimeline';
import { WaveSelector } from './components/WaveSelector';
import { CostBenefitPanel } from './components/CostBenefitPanel';
import { MigrationTable } from './components/MigrationTable';
import { ScenarioCompare } from './components/ScenarioCompare';
import type { WireCenterPlan } from './mock/mockData';

export interface PlanFilters {
  wave: string;       // 'all' | '1' | '2' | ... | '8'
  state: string;      // 'all' | 'CO' | 'MN' | ...
  status: string;     // 'all' | 'planned' | 'in_progress' | ...
  constraint: string; // 'all' | 'contract_locked' | 'regulatory_notice_pending' | ...
}

export default function App() {
  // --- State ---
  const [filters, setFilters] = useState<PlanFilters>({
    wave: 'all',
    state: 'all',
    status: 'all',
    constraint: 'all',
  });
  const [selectedWireCenter, setSelectedWireCenter] = useState<WireCenterPlan | null>(null);
  const [activeTab, setActiveTab] = useState<'gantt' | 'table' | 'scenarios'>('gantt');

  const handleWireCenterSelect = useCallback((wc: WireCenterPlan | null) => {
    setSelectedWireCenter(wc);
  }, []);

  const handleFilterChange = useCallback((newFilters: PlanFilters) => {
    setFilters(newFilters);
  }, []);

  return (
    <div className="min-h-screen bg-background p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold">Retirement Plan Tracker</h1>
          <p className="text-sm text-muted-foreground">
            Lakelink Fiber — Copper Retirement Program
          </p>
        </div>
        <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
          SYNTHETIC DATA
        </span>
      </div>

      {/* KPI bar */}
      <PlanKPIs />

      {/* Wave filter bar */}
      <WaveSelector filters={filters} onFilterChange={handleFilterChange} />

      {/* Tab navigation */}
      <div className="flex gap-1 mb-3 border-b">
        {(['gantt', 'table', 'scenarios'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors focus-visible:ring-2 focus-visible:ring-[#FF3621] focus-visible:outline-none ${
              activeTab === tab
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab === 'gantt'
              ? 'Gantt Timeline'
              : tab === 'table'
              ? 'Migration Table'
              : 'Scenario Compare'}
          </button>
        ))}
      </div>

      {/* Main content */}
      {activeTab === 'gantt' && (
        <GanttTimeline
          filters={filters}
          onWireCenterSelect={handleWireCenterSelect}
          selectedWireCenter={selectedWireCenter}
        />
      )}

      {activeTab === 'table' && (
        <MigrationTable
          filters={filters}
          onFilterChange={handleFilterChange}
          onWireCenterSelect={handleWireCenterSelect}
        />
      )}

      {activeTab === 'scenarios' && <ScenarioCompare />}

      {/* Cost/benefit detail panel (shows when a wire center is selected) */}
      {selectedWireCenter && (
        <div className="mt-4">
          <CostBenefitPanel
            wireCenter={selectedWireCenter}
            onClose={() => setSelectedWireCenter(null)}
          />
        </div>
      )}
    </div>
  );
}
