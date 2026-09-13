/**
 * App.tsx
 * Root component for the Commodity & Workforce Dashboard (P7-COMMODITY)
 * Demo Beat 5: "Who digs, and when do we sell copper?"
 *
 * Layout:
 *   [CommodityKPIs]                        ← top bar (8 KPI cards)
 *   Tabs:
 *     Price Forecast   → [PriceChart] + [SellHoldRecommendation] + [FxContextPanel]
 *     Recovery Tracker → [RecoveryTracker] + [ScrapGradeBreakdown]
 *     Contractors      → [ContractorScorecard]
 *
 * All data is SYNTHETIC until P0-DATAGEN-COMMODITY-EXECUTE + P0-DATAGEN-CONTRACTOR-EXECUTE land.
 */
import { useState } from 'react';
import { CommodityKPIs } from './components/CommodityKPIs';
import { PriceChart } from './components/PriceChart';
import { SellHoldRecommendation } from './components/SellHoldRecommendation';
import { RecoveryTracker } from './components/RecoveryTracker';
import { ContractorScorecard } from './components/ContractorScorecard';
import { FxContextPanel } from './components/FxContextPanel';

export type TabKey = 'forecast' | 'recovery' | 'contractors';

export interface CommodityFilters {
  state: string;
  scrap_grade: string;
  contractor_type: string;
  date_range: string;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('forecast');
  const [filters, setFilters] = useState<CommodityFilters>({
    state: 'all',
    scrap_grade: 'all',
    contractor_type: 'all',
    date_range: 'all',
  });

  const tabs: { key: TabKey; label: string }[] = [
    { key: 'forecast', label: 'Price Forecast' },
    { key: 'recovery', label: 'Recovery Tracker' },
    { key: 'contractors', label: 'Contractors' },
  ];

  return (
    <div className="min-h-screen bg-background p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold">Commodity & Workforce Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Lakelink Fiber — Copper Retirement Program
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* State filter (global) */}
          <select
            value={filters.state}
            onChange={(e) => setFilters({ ...filters, state: e.target.value })}
            className="text-sm border rounded px-2 py-1"
          >
            <option value="all">All States</option>
            <option value="CO">Colorado</option>
            <option value="MN">Minnesota</option>
            <option value="WA">Washington</option>
            <option value="OR">Oregon</option>
            <option value="AZ">Arizona</option>
            <option value="ID">Idaho</option>
          </select>
          <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
            SYNTHETIC DATA
          </span>
        </div>
      </div>

      {/* KPI bar */}
      <CommodityKPIs />

      {/* Tab navigation */}
      <div className="flex gap-1 mb-3 border-b">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Main content */}
      {activeTab === 'forecast' && (
        <div className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <PriceChart />
            </div>
            <div className="w-[360px] flex-shrink-0 space-y-4">
              <SellHoldRecommendation />
              <FxContextPanel />
            </div>
          </div>
        </div>
      )}

      {activeTab === 'recovery' && (
        <RecoveryTracker filters={filters} onFilterChange={setFilters} />
      )}

      {activeTab === 'contractors' && (
        <ContractorScorecard filters={filters} onFilterChange={setFilters} />
      )}
    </div>
  );
}
