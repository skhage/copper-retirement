/**
 * PlanTab.tsx — "Plan" tab of the unified Copper Retirement Accelerator (ACC-APP-UNIFY-SHELL).
 * Moved verbatim from the former retirement-plan App.tsx body; inner views become Plan sub-tabs
 * routed as #plan/<sub> (timeline | table | budget | regulatory | scenarios).
 * Data: /api/plan/* over the SQL warehouse (UC copper_retirement.gold_wave_schedule, silver_budget_allocation,
 * retirement_milestones). The regulatory checklist is built only from UC jurisdiction_requirements_cited x
 * gold_wave_schedule (citation + official_url per item). No Lakebase checklist read (ACC-APP-CHECKLIST-LEGACY-PATH).
 */
import { useState, useCallback } from 'react';
import { PlanKPIs } from '../components/PlanKPIs';
import { GanttTimeline } from '../components/GanttTimeline';
import { WaveSelector } from '../components/WaveSelector';
import { CostBenefitPanel } from '../components/CostBenefitPanel';
import { MigrationTable } from '../components/MigrationTable';
import { ScenarioCompare } from '../components/ScenarioCompare';
import { BudgetChart } from '../components/BudgetChart';
import { RegulatoryChecklist } from '../components/RegulatoryChecklist';
import { TabBar, TabHeader, SyntheticBadge, panelId, tabId } from '../components/shared';
import type { WireCenterPlan } from '../mock/mockData';
import type { PlanFilters } from '../App';

export const PLAN_SUBTABS = [
  { id: 'timeline', label: 'Gantt Timeline' },
  { id: 'table', label: 'Migration Table' },
  { id: 'budget', label: 'Budget' },
  { id: 'regulatory', label: 'Regulatory Checklist' },
  { id: 'scenarios', label: 'Scenario Compare' },
] as const;
export type PlanSub = (typeof PLAN_SUBTABS)[number]['id'];

export function isPlanSub(s: string | undefined): s is PlanSub {
  return !!s && PLAN_SUBTABS.some((t) => t.id === s);
}

interface Props {
  sub: PlanSub;
  onSubChange: (sub: PlanSub) => void;
}

export function PlanTab({ sub, onSubChange }: Props) {
  const [filters, setFilters] = useState<PlanFilters>({ wave: 'all', state: 'all', status: 'all', constraint: 'all' });
  const [selectedWireCenter, setSelectedWireCenter] = useState<WireCenterPlan | null>(null);

  const handleWireCenterSelect = useCallback((wc: WireCenterPlan | null) => setSelectedWireCenter(wc), []);
  const handleFilterChange = useCallback((f: PlanFilters) => setFilters(f), []);

  return (
    <div>
      <TabHeader
        title="Retirement Plan"
        question="What is the capital-efficient path to zero copper?"
        badges={<SyntheticBadge />}
      />

      <PlanKPIs />
      <WaveSelector filters={filters} onFilterChange={handleFilterChange} />

      <div className="mb-3 -mx-4 md:-mx-6">
        <TabBar tabs={PLAN_SUBTABS} activeId={sub} onChange={onSubChange} idPrefix="plan" ariaLabel="Plan views" />
      </div>

      <div role="tabpanel" id={panelId('plan', sub)} aria-labelledby={tabId('plan', sub)} tabIndex={0}>
        {sub === 'timeline' && (
          <GanttTimeline filters={filters} onWireCenterSelect={handleWireCenterSelect} selectedWireCenter={selectedWireCenter} />
        )}
        {sub === 'table' && (
          <MigrationTable filters={filters} onFilterChange={handleFilterChange} onWireCenterSelect={handleWireCenterSelect} />
        )}
        {sub === 'budget' && <BudgetChart />}
        {sub === 'regulatory' && (
          <>
            <p className="text-xs text-muted-foreground mb-2">
              Wave checklist status. Official rule text and source URLs for each requirement live in the{' '}
              <a href="#regulatory" className="text-primary-strong underline underline-offset-2">Regulatory tab</a>.
            </p>
            <RegulatoryChecklist filters={filters} />
          </>
        )}
        {sub === 'scenarios' && <ScenarioCompare />}
      </div>

      {selectedWireCenter && (
        <div className="mt-4">
          <CostBenefitPanel wireCenter={selectedWireCenter} onClose={() => setSelectedWireCenter(null)} />
        </div>
      )}
    </div>
  );
}
