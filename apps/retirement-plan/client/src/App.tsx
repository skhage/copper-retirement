/**
 * App.tsx — Copper Retirement Accelerator (unified partner-facing app)
 * DEC-ACCEL-UNIFIED-APP / ACC-APP-UNIFY-SHELL. Evolved in place from retirement-plan.
 *
 * IA (BRAND_GUIDE §0, demo order), URL hash routing:
 *   #map         Map & Risk        <- copper-map           (ACC-APP-PORT-MAP)
 *   #plan[/sub]  Plan              <- retirement-plan      (this app; sub = timeline|table|budget|regulatory|scenarios)
 *   #triage      Dig Triage        <- dig-triage           (ACC-APP-PORT-TRIAGE, PORTED 2026-10-24: tabs/triage/, server/routes/triage.js)
 *   #regulatory  Regulatory        <- regulatory-assistant (ACC-APP-PORT-REG; every answer/row carries source title + official URL)
 *   #commodity   Commodity & Value <- commodity-dashboard  (ACC-APP-PORT-COMMODITY)
 *
 * Styling: styles/tokens.css only (ACC-APP-TOKENS-WIRE). Partner rebrand = edit the BRAND LAYER there.
 */
import { useState, useEffect, useCallback } from 'react';
import { LakeLinkHeader, TabBar, ErrorBoundary, panelId, tabId } from './components/shared';
import { PlanTab, isPlanSub, type PlanSub } from './tabs/PlanTab';
import { PendingPortTab } from './tabs/PendingPortTab';
import { TriageTab } from './tabs/triage/App';

export interface PlanFilters {
  wave: string;       // 'all' | '1' | '2' | ... | '8'
  state: string;      // 'all' | 'CO' | 'MN' | ...
  status: string;     // 'all' | 'planned' | 'in_progress' | ...
  constraint: string; // 'all' | 'contract_locked' | 'regulatory_notice_pending' | ...
}

const TOP_TABS = [
  { id: 'map', label: 'Map & Risk' },
  { id: 'plan', label: 'Plan' },
  { id: 'triage', label: 'Dig Triage' },
  { id: 'regulatory', label: 'Regulatory' },
  { id: 'commodity', label: 'Commodity & Value' },
] as const;
type TopTab = (typeof TOP_TABS)[number]['id'];

interface Route { tab: TopTab; planSub: PlanSub }

// Land on Plan (the live tab) until ACC-APP-PORT-MAP lands; then switch default to 'map' (demo order).
const DEFAULT_ROUTE: Route = { tab: 'plan', planSub: 'timeline' };

function parseHash(hash: string): Route {
  const [tab, sub] = hash.replace(/^#\/?/, '').split('/');
  const top = TOP_TABS.find((t) => t.id === tab)?.id ?? DEFAULT_ROUTE.tab;
  return { tab: top, planSub: isPlanSub(sub) ? sub : DEFAULT_ROUTE.planSub };
}

function toHash(r: Route) { return r.tab === 'plan' ? `#plan/${r.planSub}` : `#${r.tab}`; }

export default function App() {
  const [route, setRoute] = useState<Route>(() => parseHash(window.location.hash));

  useEffect(() => {
    const onHash = () => setRoute(parseHash(window.location.hash));
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const navigate = useCallback((next: Route) => {
    const h = toHash(next);
    if (window.location.hash !== h) window.history.replaceState(null, '', h);
    setRoute(next);
  }, []);

  const label = TOP_TABS.find((t) => t.id === route.tab)!.label;

  return (
    <div className="min-h-screen bg-background font-sans">
      <LakeLinkHeader
        subtitle="Copper Retirement Accelerator"
        tagline="Find the copper, plan the path, dig safely, stay compliant, monetize the scrap"
        dataSource="MOCK"
      />

      <TabBar
        tabs={TOP_TABS}
        activeId={route.tab}
        onChange={(tab) => navigate({ ...route, tab })}
        idPrefix="top"
        ariaLabel="Accelerator sections"
      />

      <main
        role="tabpanel"
        id={panelId('top', route.tab)}
        aria-labelledby={tabId('top', route.tab)}
        className="px-4 md:px-6 py-4"
      >
        <ErrorBoundary name={label} key={route.tab}>
          {route.tab === 'map' && (
            <PendingPortTab
              title="Map & Risk"
              question="Where is our copper, and which plant is most at risk?"
              taskCode="ACC-APP-PORT-MAP"
              sourceApp="copper-map"
              dataNote="copper_retirement.gold_wire_center_scorecard, Lakebase copper_app.device_risk_map / wire_center_boundaries, and serving endpoint copper-retirement-risk."
            />
          )}
          {route.tab === 'plan' && (
            <PlanTab sub={route.planSub} onSubChange={(planSub) => navigate({ tab: 'plan', planSub })} />
          )}
          {route.tab === 'triage' && <TriageTab />}
          {route.tab === 'regulatory' && (
            <PendingPortTab
              title="Regulatory"
              question="Are we clear on notice, 811 and permit rules in every jurisdiction?"
              taskCode="ACC-APP-PORT-REG"
              sourceApp="regulatory-assistant"
              dataNote="real official sources in copper_retirement.regulatory_source_register via regulatory_doc_chunks_vs_index. Every answer and jurisdiction row will show the source title and official URL."
            />
          )}
          {route.tab === 'commodity' && (
            <PendingPortTab
              title="Commodity & Value"
              question="What is the recovered copper worth, and when should we sell?"
              taskCode="ACC-APP-PORT-COMMODITY"
              sourceApp="commodity-dashboard"
              dataNote="copper_retirement.copper_commodity_price_official (IMF PCOPPUSDM via FRED) and copper_app.gold_copper_recovery_schedule."
            />
          )}
        </ErrorBoundary>
      </main>
    </div>
  );
}
