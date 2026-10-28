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
import { LakeLinkHeader } from './components/LakeLinkHeader';
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
    <div className="min-h-screen bg-background">
      {/* Plan B LEGACY banner (ACC-APP-PLANB-LEGACY-BANNER, DEC-PLANB-GONOGO-20261028) */}
      <div
        id="legacy-banner"
        role="note"
        aria-label="Legacy demo surface notice"
        style={{
          backgroundColor: '#F9F7F4', color: '#1B3139',
          borderLeft: '4px solid #1B3139', padding: '8px 16px',
          fontSize: '14px', fontFamily: 'Inter, system-ui, sans-serif',
        }}
      >
        <strong>LEGACY demo surface, not shipped in the accelerator. </strong>
        <span>The partner accelerator ships the unified retirement-plan app (Commodity tab).</span>
      </div>
      {/* Lakelink Fiber nav header (BRAND_GUIDE §5) */}
      <LakeLinkHeader
        subtitle="Commodity & Workforce Dashboard"
        tagline="Copper Retirement Program"
        dataSource="MOCK"
      >
        {/* State filter (global) */}
        <select
          value={filters.state}
          onChange={(e) => setFilters({ ...filters, state: e.target.value })}
          aria-label="Filter by state"
          className="text-sm border rounded px-2 py-1 bg-background focus-visible:ring-2 focus-visible:ring-[#FF3621] focus-visible:outline-none"
        >
          <option value="all">All States</option>
          <option value="CO">Colorado</option>
          <option value="MN">Minnesota</option>
          <option value="WA">Washington</option>
          <option value="OR">Oregon</option>
          <option value="AZ">Arizona</option>
          <option value="ID">Idaho</option>
        </select>
      </LakeLinkHeader>

      <div className="p-4">

      {/* KPI bar */}
      <CommodityKPIs />

      {/* Tab navigation */}
      <div className="flex gap-1 mb-3 border-b">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors focus-visible:ring-2 focus-visible:ring-[#FF3621] focus-visible:outline-none ${
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
    </div>
  );
}
